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
    auth.pairingRequired.value = false;
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
      request.response.write(jsonEncode({'status': 'paired'}));
      await request.response.close();
    });
  });

  tearDown(() async => server.close(force: true));

  test('pairing stores a key and authenticates later requests', () async {
    expect(await auth.pairWithServer(baseUri, 'test-key'), isTrue);
    expect(requests.first.headers.value('authorization'), isNull);
    expect(await auth.getPairingKey(baseUri), 'test-key');
    await auth.get(baseUri.resolve('/configuration'));
    expect(requests.last.headers.value('authorization'), 'Bearer test-key');
  });

  test('incorrect pairing never stores the supplied key', () async {
    status = 401;
    expect(await auth.pairWithServer(baseUri, 'incorrect'), isFalse);
    expect(await auth.getPairingKey(baseUri), isNull);
  });

  test('an unauthorized API request signals that pairing is needed', () async {
    status = 401;
    await auth.get(baseUri.resolve('/voice-settings'));
    expect(auth.pairingRequired.value, isTrue);
  });

  test('keys are scoped to the server origin', () async {
    await auth.pairWithServer(baseUri, 'test-key');
    expect(
      await auth.getPairingKey(Uri.parse('http://different-server:8000')),
      isNull,
    );
  });

  test('authenticated requests do not follow redirects', () async {
    await auth.pairWithServer(baseUri, 'test-key');
    requests.clear();
    status = 302;
    final response = await auth.get(baseUri.resolve('/configuration'));
    expect(response.statusCode, 302);
    expect(requests.length, 1);
  });
}
