import 'dart:convert';

import 'package:http/http.dart' as http;
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
      body: jsonEncode({'url': url, 'token': token}),
    );

    return response.statusCode == 200;
  } catch (_) {
    return false;
  }
}

Future<List<dynamic>> getHADiscovered() async {
  try {
    final client = await getServerClient();
    if (client == null) return [];

    final response = await http.get(client.haDiscoveredUri);
    if (response.statusCode == 200) {
      final decoded = jsonDecode(response.body);
      return decoded is List ? decoded : [];
    }
  } catch (_) {}
  return [];
}

Future<Map<String, dynamic>?> startHAPairing(String handler) async {
  try {
    final client = await getServerClient();
    if (client == null) return null;

    final response = await http.post(
      client.haPairStartUri,
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'handler': handler}),
    );

    if (response.statusCode == 200) {
      final decoded = jsonDecode(response.body);
      return decoded['result'];
    }
  } catch (_) {}
  return null;
}

Future<Map<String, dynamic>?> submitHAPairingStep(
  String flowId,
  Map<String, dynamic> userInput,
) async {
  try {
    final client = await getServerClient();
    if (client == null) return null;

    final response = await http.post(
      client.haPairSubmitUri,
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'flow_id': flowId, 'user_input': userInput}),
    );

    if (response.statusCode == 200) {
      final decoded = jsonDecode(response.body);
      return decoded['result'];
    }
  } catch (_) {}
  return null;
}
