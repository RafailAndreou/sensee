import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:surface_controller/server/auth_http.dart' as auth;
import 'package:surface_controller/server/discovery_service.dart';
import 'package:surface_controller/server/first_success.dart';
import 'package:surface_controller/server/config_service.dart' as config;
import 'package:surface_controller/globals/global.dart' as local;
import 'package:surface_controller/globals/connectionslist.dart';

void main() {
  setUp(() => SharedPreferences.setMockInitialValues({}));

  test('successful reads reuse a TCP connection', () async {
    final server = await HttpServer.bind(InternetAddress.loopbackIPv4, 0);
    final ports = <int>[];
    server.listen((request) async {
      ports.add(request.connectionInfo!.remotePort);
      await request.drain<void>();
      request.response.write('{}');
      await request.response.close();
    });
    try {
      final uri = Uri.parse('http://127.0.0.1:${server.port}/pool');
      await auth.get(uri);
      await auth.get(uri);
      expect(ports.length, 2);
      expect(ports.toSet().length, 1);
    } finally {
      await server.close(force: true);
    }
  });

  test(
    'a deadline aborts a stalled request and later requests still work',
    () async {
      final server = await HttpServer.bind(InternetAddress.loopbackIPv4, 0);
      server.listen((request) async {
        await request.drain<void>();
        if (request.uri.path == '/ok') {
          request.response.write('{}');
          await request.response.close();
        }
      });
      try {
        final base = Uri.parse('http://127.0.0.1:${server.port}');
        await expectLater(
          auth.get(
            base.resolve('/stall'),
            timeout: const Duration(milliseconds: 50),
          ),
          throwsA(anything),
        );
        expect((await auth.get(base.resolve('/ok'))).statusCode, 200);
      } finally {
        await server.close(force: true);
      }
    },
  );

  test(
    'configuration writes serialize and advance only acknowledged revisions',
    () async {
      final server = await HttpServer.bind(InternetAddress.loopbackIPv4, 0);
      var revision = 0;
      final headers = <String?>[];
      final bodies = <String>[];
      final firstStarted = Completer<void>();
      final release = Completer<void>();
      server.listen((request) async {
        final body = await utf8.decoder.bind(request).join();
        if (request.method == 'POST') {
          headers.add(request.headers.value('if-match'));
          bodies.add(body);
          if (headers.length == 1) {
            firstStarted.complete();
            await release.future;
          }
          revision++;
        }
        request.response.headers.set('etag', '"$revision"');
        request.response.write('{}');
        await request.response.close();
      });
      try {
        final uri = Uri.parse(
          'http://127.0.0.1:${server.port}/engine-settings',
        );
        final first = auth.post(uri, body: '{"previewFps":5}');
        await firstStarted.future;
        final second = auth.post(uri, body: '{"previewFps":10}');
        await Future<void>.delayed(Duration.zero);
        expect(headers.length, 1);
        release.complete();
        await Future.wait([first, second]);
        expect(headers, ['"0"', '"1"']);
        expect(bodies, ['{"previewFps":5}', '{"previewFps":10}']);
      } finally {
        await server.close(force: true);
      }
    },
  );

  test(
    'an old poll cannot overwrite a newly acknowledged local mapping',
    () async {
      final server = await HttpServer.bind(InternetAddress.loopbackIPv4, 0);
      final base = 'http://127.0.0.1:${server.port}';
      SharedPreferences.setMockInitialValues({'sensee.lastAddress': base});
      invalidateServerClientCache();
      local.connectionConfigs.clear();
      final mapping = local.getConnectionConfig(1);
      mapping.id.value = 1;
      mapping.action.value = 'Turn on';
      mapping.isSynced.value = true;
      final started = Completer<void>();
      final release = Completer<void>();
      var gate = false;
      server.listen((request) async {
        await request.drain<void>();
        if (request.uri.path == '/ping') {
          request.response.write('{"status":"ok","service":"sensee"}');
        } else {
          if (request.method == 'GET' && gate) {
            if (!started.isCompleted) started.complete();
            await release.future;
          }
          request.response.headers.set(
            'etag',
            request.method == 'POST' ? '"new"' : '"old"',
          );
          request.response.write(
            request.method == 'POST' ? '{}' : '[{"id":"1","action":"Turn on"}]',
          );
        }
        await request.response.close();
      });
      try {
        await auth.get(Uri.parse('$base/configuration'));
        gate = true;
        final poll = config.pullLatestConfigurationsFromServer();
        await started.future.timeout(const Duration(seconds: 5));
        mapping.action.value = 'Turn off';
        mapping.isSynced.value = false;
        await config.sendAllConfigurations();
        expect(mapping.isSynced.value, isTrue);
        release.complete();
        expect(await poll, isFalse);
        expect(mapping.action.value, 'Turn off');
      } finally {
        if (!release.isCompleted) release.complete();
        local.connectionConfigs.clear();
        clearPendingConnectionDeletions();
        invalidateServerClientCache();
        await server.close(force: true);
      }
    },
  );

  test(
    'a late settings GET cannot rebase an edited form or a conflict',
    () async {
      final server = await HttpServer.bind(InternetAddress.loopbackIPv4, 0);
      var reads = 0;
      final started = Completer<void>();
      final release = Completer<void>();
      final sentRevisions = <String?>[];
      server.listen((request) async {
        await request.drain<void>();
        if (request.method == 'GET') {
          reads++;
          final number = reads;
          if (number == 2) {
            started.complete();
            await release.future;
          }
          request.response.headers.set(
            'etag',
            number == 1 ? '"base"' : '"remote"',
          );
        } else {
          sentRevisions.add(request.headers.value('if-match'));
          request.response.statusCode = 412;
          request.response.headers.set('etag', '"remote"');
        }
        request.response.write('{}');
        await request.response.close();
      });
      try {
        final uri = Uri.parse(
          'http://127.0.0.1:${server.port}/camera-settings',
        );
        await auth.get(uri);
        var edited = false;
        final pending = auth.get(uri, acceptRevision: () => !edited);
        await started.future;
        edited = true;
        release.complete();
        await pending;
        expect(
          (await auth.post(uri, body: '{"streamUrl":"draft"}')).statusCode,
          412,
        );
        expect(
          (await auth.post(uri, body: '{"streamUrl":"draft"}')).statusCode,
          412,
        );
        expect(sentRevisions, ['"base"', '"base"']);
        expect(auth.settingsWriteError.value, contains('Your edits are kept'));
      } finally {
        if (!release.isCompleted) release.complete();
        await server.close(force: true);
      }
    },
  );

  test('discovery cancellation closes every registered losing resource', () {
    final cancellation = DiscoveryCancellation();
    var closed = 0;
    cancellation.add(() => closed++);
    cancellation.add(() => closed++);
    cancellation.cancel();
    cancellation.add(() => closed++);
    expect(closed, 3);
  });

  test('throwing probes cannot prevent a reachable server winning', () async {
    expect(
      await firstSuccessful<String>([
        Future.error(StateError('failed probe')),
        Future.value('reachable'),
      ]),
      'reachable',
    );
  });
}
