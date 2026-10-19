import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:surface_controller/server/auth_http.dart' as auth;

void main() {
  late HttpServer server;
  late Uri baseUri;
  late int status;
  late List<HttpRequest> requests;

  setUp(() async {
    SharedPreferences.setMockInitialValues({});
    status = 200;
    requests = [];
    server = await HttpServer.bind(InternetAddress.loopbackIPv4, 0);
    baseUri = Uri.parse('http://127.0.0.1:${server.port}');
    server.listen((request) async {
      requests.add(request);
      await request.drain<void>();
      request.response.statusCode = status;
      request.response.headers.contentType = ContentType.json;
      if (status == 302) {
        request.response.headers.set('location', '/redirected');
      }
      request.response.write(jsonEncode({'status': 'ok'}));
      await request.response.close();
    });
  });

  tearDown(() async => server.close(force: true));

  test('configuration requests need no key and ignore old stored keys', () async {
    SharedPreferences.setMockInitialValues({
      'sensee.pairing.${baseUri.origin}': 'old-key',
    });
    final response = await auth.get(baseUri.resolve('/configuration'));
    expect(response.statusCode, 200);
    expect(requests.single.headers.value('authorization'), isNull);
  });

  test('configuration can be posted without pairing', () async {
    final response = await auth.post(
      baseUri.resolve('/configuration'),
      headers: {'Content-Type': 'application/json'},
      body: '[]',
    );
    expect(response.statusCode, 200);
    expect(requests.single.method, 'POST');
    expect(requests.single.headers.value('authorization'), isNull);
  });

  test('HTTP errors are returned to the caller', () async {
    status = 401;
    final response = await auth.get(baseUri.resolve('/voice-settings'));
    expect(response.statusCode, 401);
  });

  test('requests do not follow redirects', () async {
    status = 302;
    final response = await auth.get(baseUri.resolve('/configuration'));
    expect(response.statusCode, 302);
    expect(requests.length, 1);
  });
}
