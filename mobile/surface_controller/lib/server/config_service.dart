import 'dart:async';
import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'auth_http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'package:surface_controller/globals/connectionslist.dart';
import 'package:surface_controller/globals/global.dart';
import 'package:surface_controller/server/discovery_service.dart';

final configurationSyncError = ValueNotifier<String?>(null);

int _mappingGeneration = 0;
int _sendsPending = 0;
Future<void> _sendTail = Future.value();
Future<void> sendAllConfigurations() {
  _mappingGeneration++;
  _sendsPending++;
  _sendTail = _sendTail
      .catchError((Object _) {})
      .then((_) => _sendAllConfigurations())
      .whenComplete(() {
        _sendsPending--;
        _mappingGeneration++;
      });
  return _sendTail;
}

String _snapshot() => jsonEncode([
  for (final c in connectionConfigs.values)
    {
      "id": c.id.value.toString(),
      "connectionType": c.connectionType.value,
      "entityId": c.entityId.value,
      "brand": c.brand.value,
      "action": c.action.value,
      "gesture": c.gesture.value,
      "sound": c.sound.value,
      "hand": c.hand.value,
    },
]);

Future<void> _sendAllConfigurations() async {
  final snapshot = _snapshot();
  final deletions = Set<int>.from(pendingDeletedConnectionIds);
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

    if (response.statusCode == 412) {
      configurationSyncError.value =
          'Mappings changed on another client. Unsaved edits kept. Review both versions in Settings → Engine tools.';
    } else if (response.statusCode == 200) {
      configurationSyncError.value = null;
    } else {
      configurationSyncError.value =
          "Mapping save failed (${response.statusCode}). Unsaved edits kept.";
    }
    if (response.statusCode == 200 && snapshot == _snapshot()) {
      connectionConfigs.forEach((id, config) => config.isSynced.value = true);
      acknowledgeConnectionDeletions(deletions);
    } else {
      connectionConfigs.forEach((id, config) => config.isSynced.value = false);
    }
  } catch (_) {
    configurationSyncError.value = "Engine unavailable. Unsaved mappings kept.";
    invalidateServerClientCache();
    connectionConfigs.forEach((id, config) => config.isSynced.value = false);
  }
}

Future<void> sendConfiguration(ConnectionConfig config) async {
  await sendAllConfigurations();
}

Future<bool> pullLatestConfigurationsFromServer() async {
  if (_sendsPending > 0) return false;
  final generation = _mappingGeneration;
  try {
    final client = await getServerClient();
    if (client == null) {
      return false;
    }

    final snapshot = _snapshot();
    final deleted = Set<int>.from(pendingDeletedConnectionIds);
    final dirty =
        connectionConfigs.values.any((c) => !c.isSynced.value) ||
        pendingDeletedConnectionIds.isNotEmpty;
    final response = await http.get(
      client.configUri,
      rememberRevision: false,
      timeout: const Duration(milliseconds: 1800),
    );

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

    if (generation != _mappingGeneration ||
        _sendsPending > 0 ||
        snapshot != _snapshot() ||
        !setEquals(deleted, pendingDeletedConnectionIds)) {
      return false;
    }
    if (!dirty) await http.rememberResponseRevision(client.configUri, response);
    if (generation != _mappingGeneration ||
        _sendsPending > 0 ||
        snapshot != _snapshot() ||
        !setEquals(deleted, pendingDeletedConnectionIds)) {
      return false;
    }
    applyServerConfigurationsSnapshot(configs);
    return true;
  } catch (_) {
    invalidateServerClientCache();
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

Future<Map<String, dynamic>?> loadGestureSettings({
  bool Function()? acceptRevision,
}) async {
  try {
    final client = await getServerClient();
    if (client == null) {
      return null;
    }

    final response = await http.get(
      client.gestureSettingsUri,
      acceptRevision: acceptRevision,
    );

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
      'selectedGesture': prefs.getString('gesture_selected') ?? 'Open Palm',
    };
  } catch (_) {
    return {
      'wakeEnabled': false,
      'holdDurationSeconds': 2.0,
      'activeWindowSeconds': 5.0,
      'selectedGesture': 'Open Palm',
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

Future<Map<String, dynamic>?> loadCameraSettings({
  bool Function()? acceptRevision,
}) async {
  try {
    final client = await getServerClient();
    if (client == null) return null;

    final response = await http.get(
      client.cameraSettingsUri,
      acceptRevision: acceptRevision,
    );
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

Future<Map<String, dynamic>?> loadIronmanParams() async {
  try {
    final client = await getServerClient();
    if (client == null) return null;
    final response = await http.get(client.ironmanParamsUri);
    if (response.statusCode == 200) {
      return jsonDecode(response.body) as Map<String, dynamic>;
    }
    return null;
  } catch (_) {
    return null;
  }
}

Future<bool> saveIronmanParams(Map<String, dynamic> params) async {
  try {
    final client = await getServerClient();
    if (client == null) return false;
    final response = await http.post(
      client.ironmanParamsUri,
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode(params),
    );
    return response.statusCode == 200;
  } catch (_) {
    return false;
  }
}

Future<Map<String, dynamic>?> loadVoiceSettings() async {
  try {
    final client = await getServerClient();
    if (client == null) return null;
    final response = await http.get(client.voiceSettingsUri);
    if (response.statusCode == 200) {
      return jsonDecode(response.body) as Map<String, dynamic>;
    }
    return null;
  } catch (_) {
    return null;
  }
}

Future<Map<String, dynamic>?> loadVoiceStatus() async {
  try {
    final client = await getServerClient();
    if (client == null) return null;
    final response = await http.get(
      client.voiceStatusUri,
      timeout: const Duration(seconds: 3),
    );
    if (response.statusCode == 200) {
      return jsonDecode(response.body) as Map<String, dynamic>;
    }
    return null;
  } catch (_) {
    return null;
  }
}

Future<bool> saveVoiceSettings(Map<String, dynamic> settings) async {
  try {
    final client = await getServerClient();
    if (client == null) return false;
    final response = await http.post(
      client.voiceSettingsUri,
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode(settings),
    );
    return response.statusCode == 200;
  } catch (_) {
    return false;
  }
}

Future<List<Map<String, dynamic>>> loadHACameras() async {
  try {
    final client = await getServerClient();
    if (client == null) return [];

    final response = await http.get(
      client.haCamerasUri,
      timeout: const Duration(seconds: 5),
    );

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
