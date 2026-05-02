import 'dart:async';
import 'dart:convert';

import 'package:flutter/widgets.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'package:surface_controller/globals/connectionslist.dart';
import 'package:surface_controller/globals/global.dart';
import 'package:surface_controller/server/discovery_service.dart';

Future<void> sendAllConfigurations() async {
  final List<Map<String, dynamic>> allConfigsData = [];

  connectionConfigs.forEach((id, config) {
    allConfigsData.add({
      'id': config.id.value.toString(),
      'connectionType': config.connectionType.value,
      'entityId': config.entityId.value,
      'brand': config.brand.value,
      'action': config.action.value,
      'gesture': config.gesture.value,
      'sound': config.sound.value,
      'hand': config.hand.value,
    });
  });

  debugPrint('[Config] Sending ${allConfigsData.length} configurations...');

  try {
    final client = await getServerClient();
    if (client == null) {
      connectionConfigs.forEach((id, config) => config.isSynced.value = false);
      return;
    }

    final response = await http.post(
      client.configUri,
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode(allConfigsData),
    );

    if (response.statusCode == 200) {
      connectionConfigs.forEach((id, config) => config.isSynced.value = true);
      clearPendingConnectionDeletions();
    } else {
      connectionConfigs.forEach((id, config) => config.isSynced.value = false);
    }
  } catch (_) {
    connectionConfigs.forEach((id, config) => config.isSynced.value = false);
  }
}

Future<void> sendConfiguration(ConnectionConfig config) async {
  await sendAllConfigurations();
}

Future<bool> pullLatestConfigurationsFromServer() async {
  try {
    final client = await getServerClient();
    if (client == null) {
      return false;
    }

    final response = await http
        .get(client.configUri)
        .timeout(const Duration(milliseconds: 1800));

    if (response.statusCode != 200) {
      return false;
    }

    final decoded = jsonDecode(response.body);
    if (decoded is! List) {
      return false;
    }

    final configs = <Map<String, dynamic>>[];
    for (final item in decoded) {
      if (item is Map<String, dynamic>) {
        configs.add(item);
      } else if (item is Map) {
        configs.add(Map<String, dynamic>.from(item));
      }
    }

    applyServerConfigurationsSnapshot(configs);
    return true;
  } catch (_) {
    return false;
  }
}

Future<bool> sendGestureSettings({
  required bool wakeEnabled,
  required double holdDurationSeconds,
  required double activeWindowSeconds,
  required String selectedGesture,
}) async {
  try {
    final client = await getServerClient();
    if (client == null) {
      return false;
    }

    final payload = {
      'wakeEnabled': wakeEnabled,
      'holdDurationSeconds': holdDurationSeconds,
      'activeWindowSeconds': activeWindowSeconds,
      'selectedGesture': selectedGesture,
    };

    final response = await http.post(
      client.gestureSettingsUri,
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode(payload),
    );

    return response.statusCode == 200;
  } catch (_) {
    return false;
  }
}

Future<Map<String, dynamic>?> loadGestureSettings() async {
  try {
    final client = await getServerClient();
    if (client == null) {
      return null;
    }

    final response = await http.get(client.gestureSettingsUri);

    if (response.statusCode == 200) {
      return jsonDecode(response.body) as Map<String, dynamic>;
    }
    return null;
  } catch (_) {
    return null;
  }
}

Future<void> saveGestureSettingsLocal({
  required bool wakeEnabled,
  required double holdDurationSeconds,
  required double activeWindowSeconds,
  required String selectedGesture,
}) async {
  try {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool('gesture_wake_enabled', wakeEnabled);
    await prefs.setDouble('gesture_hold_duration', holdDurationSeconds);
    await prefs.setDouble('gesture_active_window', activeWindowSeconds);
    await prefs.setString('gesture_selected', selectedGesture);
  } catch (_) {
    // Silently fail if local storage unavailable
  }
}

Future<Map<String, dynamic>> loadGestureSettingsLocal() async {
  try {
    final prefs = await SharedPreferences.getInstance();
    return {
      'wakeEnabled': prefs.getBool('gesture_wake_enabled') ?? false,
      'holdDurationSeconds': prefs.getDouble('gesture_hold_duration') ?? 2.0,
      'activeWindowSeconds': prefs.getDouble('gesture_active_window') ?? 5.0,
      'selectedGesture': prefs.getString('gesture_selected') ?? 'Open Hand',
    };
  } catch (_) {
    return {
      'wakeEnabled': false,
      'holdDurationSeconds': 2.0,
      'activeWindowSeconds': 5.0,
      'selectedGesture': 'Open Hand',
    };
  }
}

Future<bool> sendCameraSettings({
  required bool useNetwork,
  required String streamUrl,
}) async {
  try {
    final client = await getServerClient();
    if (client == null) return false;

    final response = await http.post(
      client.cameraSettingsUri,
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'useNetwork': useNetwork, 'streamUrl': streamUrl}),
    );
    return response.statusCode == 200;
  } catch (_) {
    return false;
  }
}

Future<Map<String, dynamic>?> loadCameraSettings() async {
  try {
    final client = await getServerClient();
    if (client == null) return null;

    final response = await http.get(client.cameraSettingsUri);
    if (response.statusCode == 200) {
      return jsonDecode(response.body) as Map<String, dynamic>;
    }
    return null;
  } catch (_) {
    return null;
  }
}

Future<void> saveCameraSettingsLocal({
  required bool useNetwork,
  required String streamUrl,
}) async {
  try {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool('camera_use_network', useNetwork);
    await prefs.setString('camera_stream_url', streamUrl);
  } catch (_) {}
}

Future<List<Map<String, dynamic>>> loadHACameras() async {
  try {
    final client = await getServerClient();
    if (client == null) return [];

    final response = await http
        .get(client.haCamerasUri)
        .timeout(const Duration(seconds: 5));

    if (response.statusCode != 200) return [];

    final body = jsonDecode(response.body);
    final list = body['cameras'];
    if (list is! List) return [];
    return list.whereType<Map<String, dynamic>>().toList();
  } catch (_) {
    return [];
  }
}

Future<Map<String, dynamic>> loadCameraSettingsLocal() async {
  try {
    final prefs = await SharedPreferences.getInstance();
    return {
      'useNetwork': prefs.getBool('camera_use_network') ?? false,
      'streamUrl': prefs.getString('camera_stream_url') ?? '',
    };
  } catch (_) {
    return {'useNetwork': false, 'streamUrl': ''};
  }
}
