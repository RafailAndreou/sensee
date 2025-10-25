import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:surface_controller/globals/global.dart';

const String serverUrl = "http://10.180.97.82:8000/configuration";

Future<void> sendConfiguration(ConnectionConfig config) async {
  final configData = {
    "brand": config.brand.value,
    "action": config.action.value,
    "gesture": config.gesture.value,
    "sound": config.sound.value,
    "hand": config.hand.value,
  };

  try {
    final response = await http.post(
      Uri.parse(serverUrl),
      headers: {"Content-Type": "application/json"},
      body: jsonEncode(configData),
    );

    if (response.statusCode == 200) {
      print("✅ Configuration sent successfully!");
    } else {
      print("⚠️ Server error: ${response.statusCode}");
    }
  } catch (e) {
    print("❌ Failed to send configuration: $e");
  }
}
