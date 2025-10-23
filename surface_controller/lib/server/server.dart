import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:surface_controller/global.dart';

const String serverUrl = "http://10.219.41.82:8000/configuration";

Future<void> sendConfiguration() async {
  final config = {
    "brand": brand.value,
    "action": action.value,
    "gesture": gesture.value,
    "sound": sound.value,
    "hand": hand.value,
  };

  try {
    final response = await http.post(
      Uri.parse(serverUrl),
      headers: {"Content-Type": "application/json"},
      body: jsonEncode(config),
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
