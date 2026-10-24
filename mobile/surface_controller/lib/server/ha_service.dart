import 'dart:convert';
import 'package:flutter/foundation.dart';

import 'auth_http.dart' as http;
import 'package:surface_controller/server/discovery_service.dart';

Future<Map<String, dynamic>?> getHAConfig() async {
  try {
    final client = await getServerClient();
    if (client == null) return null;

    final response = await http.get(client.haConfigUri);
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    }
  } catch (_) {}
  return null;
}

Future<bool> saveHAConfig(String url, String token) async {
  try {
    final client = await getServerClient();
    if (client == null) return false;

    final response = await http.post(
      client.haConfigUri,
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'url': url,
        if (token.trim().isNotEmpty) 'token': token.trim(),
      }),
    );

    return response.statusCode == 200;
  } catch (_) {
    return false;
  }
}

Future<List<dynamic>> getHADiscovered() async {
  try {
    final client = await getServerClient();
    if (client == null) throw Exception('Sensee is unavailable');

    final response = await http.get(client.haDiscoveredUri);
    if (response.statusCode == 200) {
      final decoded = jsonDecode(response.body);
      if (decoded is! Map || decoded['flows'] is! List) {
        throw Exception('Invalid Home Assistant discovery response');
      }
      return decoded['flows'] as List;
    }
    throw Exception(
      jsonDecode(response.body)['detail'] ??
          'Cannot read Home Assistant discoveries',
    );
  } catch (error) {
    debugPrint('Home Assistant discovery failed: $error');
    rethrow;
  }
}

Map<String, dynamic> _pairResult(int statusCode, String body) {
  final decoded = jsonDecode(body);
  if (statusCode != 200) {
    throw Exception(decoded['detail'] ?? 'Home Assistant pairing failed');
  }
  return Map<String, dynamic>.from(decoded['result']);
}

Future<Map<String, dynamic>?> startHAPairing(
  String handler, {
  String? host,
}) async {
  final client = await getServerClient();
  if (client == null) throw Exception('Sensee is unavailable');
  final response = await http.post(
    client.haPairStartUri,
    headers: {'Content-Type': 'application/json'},
    body: jsonEncode({'handler': handler, if (host != null) 'host': host}),
  );
  return _pairResult(response.statusCode, response.body);
}

Future<Map<String, dynamic>?> submitHAPairingStep(
  String flowId,
  Map<String, dynamic> userInput,
) async {
  final client = await getServerClient();
  if (client == null) throw Exception('Sensee is unavailable');
  final response = await http.post(
    client.haPairSubmitUri,
    headers: {'Content-Type': 'application/json'},
    body: jsonEncode({'flow_id': flowId, 'user_input': userInput}),
  );
  return _pairResult(response.statusCode, response.body);
}

Future<Map<String, dynamic>> getHAPairingFlow(String flowId) async {
  final client = await getServerClient();
  if (client == null) throw Exception('Sensee is unavailable');
  final uri = client.haPairSubmitUri.resolve(
    '/ha/pair/${Uri.encodeComponent(flowId)}',
  );
  final response = await http.get(uri);
  return _pairResult(response.statusCode, response.body);
}
