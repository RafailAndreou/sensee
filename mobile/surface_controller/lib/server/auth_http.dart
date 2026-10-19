import 'dart:convert';
import 'dart:async';
import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as raw;
import 'package:shared_preferences/shared_preferences.dart';

final pairingRequired = ValueNotifier<bool>(false);
final settingsWriteError = ValueNotifier<String?>(null);
const _requestTimeout = Duration(seconds: 10);

final _transport = HttpClient()..idleTimeout = const Duration(seconds: 30);
final _revisions = <String, String>{};
final _writes = <String, Future<raw.Response>>{};
const _revisionPaths = {
  '/configuration',
  '/engine-settings',
  '/profiles',
  '/camera-settings',
  '/gesture-settings',
  '/ironman-params',
  '/voice-settings',
  '/ha/config',
};

String _storageKey(Uri uri) => 'sensee.pairing.${uri.origin}';

Future<String?> getPairingKey(Uri uri) async {
  final preferences = await SharedPreferences.getInstance();
  return preferences.getString(_storageKey(uri));
}

Map<String, String> _responseHeaders(HttpHeaders headers) {
  final result = <String, String>{};
  headers.forEach((name, values) => result[name] = values.join(', '));
  return result;
}

Future<raw.Response> _request(
  String method,
  Uri uri, {
  Map<String, String>? headers,
  Object? body,
  bool authenticate = true,
  Duration timeout = _requestTimeout,
}) async {
  HttpClientRequest? request;
  Timer? timer;
  bool expired = false;
  try {
    timer = Timer(timeout, () {
      expired = true;
      request?.abort(TimeoutException('Request timed out'));
    });
    final opening = _transport.openUrl(method, uri);
    opening.then((lateRequest) {
      if (expired) lateRequest.abort(TimeoutException('Request timed out'));
    }, onError: (Object _) {});
    request = await opening.timeout(timeout);
    request.followRedirects = false;
    headers?.forEach(request.headers.set);
    if (authenticate) {
      final key = await getPairingKey(uri);
      if (key != null) request.headers.set('Authorization', 'Bearer $key');
    }

    if (body is String) request.write(body);
    final stream = await request.close();
    final bytes = await stream.fold<List<int>>(
      [],
      (all, chunk) => all..addAll(chunk),
    );
    final response = raw.Response.bytes(
      bytes,
      stream.statusCode,
      headers: _responseHeaders(stream.headers),
    );
    if (authenticate && response.statusCode == 401) {
      pairingRequired.value = true;
    }
    if (expired) throw TimeoutException("Request timed out");
    return response;
  } finally {
    timer?.cancel();
  }
}

Future<void> rememberResponseRevision(Uri uri, raw.Response response) async {
  final revision = response.headers['etag'];
  if (response.statusCode == 200 && revision != null) {
    _revisions[uri.toString()] = revision;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('sensee.revision.$uri', revision);
  }
}

Future<raw.Response> get(
  Uri uri, {
  Map<String, String>? headers,
  bool rememberRevision = true,
  bool Function()? acceptRevision,
  Duration timeout = _requestTimeout,
}) async {
  final response = await _request(
    'GET',
    uri,
    headers: headers,
    timeout: timeout,
  );
  if (rememberRevision && (acceptRevision?.call() ?? true)) {
    await rememberResponseRevision(uri, response);
  } else if (!_revisions.containsKey(uri.toString())) {
    final prefs = await SharedPreferences.getInstance();
    final previous = prefs.getString('sensee.revision.$uri');
    if (previous != null) _revisions[uri.toString()] = previous;
  }
  return response;
}

Future<raw.Response> post(
  Uri uri, {
  Map<String, String>? headers,
  Object? body,
}) {
  final key = uri.toString();
  final previous = _writes[key];
  final operation = (() async {
    if (previous != null) {
      try {
        await previous;
      } catch (_) {}
    }
    if (_revisionPaths.contains(uri.path) && !_revisions.containsKey(key)) {
      final prefs = await SharedPreferences.getInstance();
      final stored = prefs.getString('sensee.revision.$uri');
      if (stored != null) {
        _revisions[key] = stored;
      } else {
        await get(uri);
      }
    }
    final revision = _revisions[key];
    final response = await _request(
      'POST',
      uri,
      headers: {
        ...?headers,
        if (revision != null) 'If-Match': revision,
        if (uri.path == '/profiles' &&
            _revisions.containsKey(uri.resolve('/configuration').toString()))
          'If-Match-Configuration':
              _revisions[uri.resolve('/configuration').toString()]!,
      },
      body: body,
    );
    settingsWriteError.value = response.statusCode == 412
        ? 'Settings changed on another client. Your edits are kept; review or reload before retrying.'
        : response.statusCode >= 400
        ? 'Settings save failed (${response.statusCode}). Your edits are kept.'
        : null;
    await rememberResponseRevision(uri, response);
    return response;
  })();
  _writes[key] = operation;
  return operation;
}

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
