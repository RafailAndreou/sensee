import 'package:http/http.dart' as raw;

const _requestTimeout = Duration(seconds: 10);

Future<raw.Response> _request(
  String method,
  Uri uri, {
  Map<String, String>? headers,
  Object? body,
}) async {
  final timeout = uri.path.startsWith('/ha/pair/')
      ? const Duration(seconds: 45)
      : _requestTimeout;
  final client = raw.Client();
  try {
    final request = raw.Request(method, uri)..followRedirects = false;
    request.headers.addAll(headers ?? {});
    if (body is String) request.body = body;
    final stream = await client.send(request).timeout(timeout);
    final response = await raw.Response.fromStream(stream).timeout(timeout);
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
