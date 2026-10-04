import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as raw;
import 'package:shared_preferences/shared_preferences.dart';

final pairingRequired = ValueNotifier<bool>(false);
const _requestTimeout = Duration(seconds: 10);

String _storageKey(Uri uri) => 'sensee.pairing.${uri.origin}';

Future<String?> getPairingKey(Uri uri) async {
  final preferences = await SharedPreferences.getInstance();
  return preferences.getString(_storageKey(uri));
}

Future<raw.Response> _request(
  String method,
  Uri uri, {
  Map<String, String>? headers,
  Object? body,
  bool authenticate = true,
}) async {
  final client = raw.Client();
  try {
    final request = raw.Request(method, uri)..followRedirects = false;
    request.headers.addAll(headers ?? {});
    if (authenticate) {
      final key = await getPairingKey(uri);
      if (key != null) request.headers['Authorization'] = 'Bearer $key';
    }
    if (body is String) request.body = body;
    final stream = await client.send(request).timeout(_requestTimeout);
    final response = await raw.Response.fromStream(
      stream,
    ).timeout(_requestTimeout);
    if (authenticate && response.statusCode == 401) {
      pairingRequired.value = true;
    }
    return response;
  } finally {
    client.close();
  }
}

Future<raw.Response> get(Uri uri, {Map<String, String>? headers}) =>
    _request('GET', uri, headers: headers);

Future<raw.Response> post(
  Uri uri, {
  Map<String, String>? headers,
  Object? body,
}) => _request('POST', uri, headers: headers, body: body);

Future<bool> isPaired(Uri baseUri) async {
  try {
    return (await get(baseUri.resolve('/auth/status'))).statusCode == 200;
  } catch (error) {
    debugPrint('Could not check pairing: $error');
    return false;
  }
}

Future<bool> pairWithServer(Uri baseUri, String key) async {
  final response = await _request(
    'POST',
    baseUri.resolve('/auth/pair'),
    headers: {'Content-Type': 'application/json'},
    body: jsonEncode({'key': key.trim()}),
    authenticate: false,
  );
  if (response.statusCode != 200) return false;
  final preferences = await SharedPreferences.getInstance();
  await preferences.setString(_storageKey(baseUri), key.trim());
  pairingRequired.value = false;
  return true;
}
