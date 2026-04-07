import 'package:flutter/material.dart';
import 'global.dart';
import 'dart:io';
import 'dart:convert';
import 'package:path_provider/path_provider.dart';

ValueNotifier<List<int>> connectionsList = ValueNotifier<List<int>>([]);
int _nextConnectionId = 1;

// In mobile/surface_controller/lib/globals/connectionslist.dart

void addNewConnection() {
  // 1. Capture the new ID
  final newId = _nextConnectionId++;

  // 2. IMPORTANT: Explicitly set the ID in the config object immediately
  // This ensures config.id.value is 'newId' instead of the default '-1'
  getConnectionConfig(newId).id.value = newId;

  // 3. Add to the list to update the UI
  connectionsList.value = List.from(connectionsList.value)..add(newId);

  debugPrint("Created new connection with ID: $newId");
}

void removeConnection(int id) {
  connectionsList.value = List.from(connectionsList.value)
    ..removeWhere((connectionId) => connectionId == id);

  removeConnectionConfig(id);

  if (connectionsList.value.isEmpty) {
    _nextConnectionId = 0;
  }
}

int countConnections() {
  return connectionsList.value.length;
}

void PrintDirectory() async {
  final directory = await getApplicationDocumentsDirectory();
  print('App Documents Directory: ${directory.path}');
}

// ···
Future<String> get _localPath async {
  final directory = await getApplicationDocumentsDirectory();

  return directory.path;
}

Future<File> get _localFile async {
  final path = await _localPath;
  return File('$path/server.json');
}

Future<File> get _configurationsFile async {
  final path = await _localPath;
  return File('$path/configurations.json');
}

Future<File> writeCountConnections(int count) async {
  final file = await _localFile;
  return file.writeAsString('$count');
}

Future<String> readCountConnections() async {
  try {
    final file = await _localFile;
    final contents = await file.readAsString();
    return contents;
  } catch (e) {
    return 'Error: $e';
  }
}

void printAllConnections() {
  for (var connectionId in connectionsList.value) {
    debugPrint('Connection ID: $connectionId');
    debugPrint('  Brand: ${getConnectionConfig(connectionId).brand.value}');
    debugPrint('  Action: ${getConnectionConfig(connectionId).action.value}');
    debugPrint('  Gesture: ${getConnectionConfig(connectionId).gesture.value}');
    debugPrint('  Sound: ${getConnectionConfig(connectionId).sound.value}');
    debugPrint('  Hand: ${getConnectionConfig(connectionId).hand.value}');
  }
}

void configuesToJson() {
  final Map<String, dynamic> allConfigs = {};

  connectionConfigs.forEach((connectionId, config) {
    allConfigs[connectionId.toString()] = {
      "id": config.id.value,
      "brand": config.brand.value,
      "action": config.action.value,
      "gesture": config.gesture.value,
      "sound": config.sound.value,
      "hand": config.hand.value,
    };
  });

  final jsonString = jsonEncode(allConfigs);
  debugPrint('All Connection Configs as JSON: $jsonString');
}

void saveConfigsToFile() async {
  try {
    final Map<String, dynamic> allConfigs = {};

    connectionConfigs.forEach((connectionId, config) {
      allConfigs[connectionId.toString()] = {
        "id": config.id.value,
        "connectionType": config.connectionType.value,
        "entityId": config.entityId.value,
        "brand": config.brand.value,
        "action": config.action.value,
        "gesture": config.gesture.value,
        "sound": config.sound.value,
        "hand": config.hand.value,
      };
    });

    final jsonString = jsonEncode(allConfigs);
    final file = await _configurationsFile;
    await file.writeAsString(jsonString);
    debugPrint('Configurations saved to file: $jsonString');
  } catch (e) {
    debugPrint('Error saving configurations to file: $e');
  }
}

Future<void> loadConfigurationsFromFile() async {
  try {
    final file = await _configurationsFile;
    final path = file.path;
    debugPrint('Attempting to load configurations from: $path');

    // Check if file exists
    if (!await file.exists()) {
      debugPrint('Configuration file does not exist yet at: $path');
      return;
    }

    final jsonString = await file.readAsString();
    debugPrint('Read configuration file content: $jsonString');

    // Check if file is empty
    if (jsonString.isEmpty) {
      debugPrint('Configuration file is empty');
      return;
    }

    final decodedData = jsonDecode(jsonString);

    // Check if decodedData is a Map (configurations) or something else (old format)
    if (decodedData is! Map<String, dynamic>) {
      debugPrint(
        'Configuration file format is invalid or contains old data: $decodedData',
      );
      return;
    }

    final Map<String, dynamic> allConfigs = decodedData;
    final List<int> loadedConnectionIds = [];

    allConfigs.forEach((connectionIdStr, configData) {
      // Skip if configData is not a Map (e.g., old count data)
      if (configData is! Map<String, dynamic>) {
        debugPrint('Skipping invalid config data for $connectionIdStr');
        return;
      }

      final connectionId = int.parse(connectionIdStr);
      loadedConnectionIds.add(connectionId);
      final config = getConnectionConfig(connectionId);
      config.id.value = configData["id"] ?? connectionId;
      config.connectionType.value = configData["connectionType"] ?? 'ir';
      config.entityId.value = configData["entityId"] ?? '';
      config.brand.value = configData["brand"] ?? '';
      config.action.value = configData["action"] ?? '';
      config.gesture.value = configData["gesture"] ?? '';
      config.sound.value = configData["sound"] ?? '';
      config.hand.value = configData["hand"] ?? '';
      debugPrint('Loaded config for connection ID $connectionId');
    });

    // Update the connectionsList with loaded connection IDs
    if (loadedConnectionIds.isNotEmpty) {
      loadedConnectionIds.sort();
      final maxConnectionId = loadedConnectionIds.reduce(
        (a, b) => a > b ? a : b,
      );
      _nextConnectionId = maxConnectionId + 1;
      connectionsList.value = loadedConnectionIds;
      debugPrint(
        'Updated connectionsList with ${loadedConnectionIds.length} connections',
      );
    }
  } catch (e) {
    debugPrint('Error loading configurations from file: $e');
  }
}

void applyServerConfigurationsSnapshot(List<Map<String, dynamic>> incoming) {
  final incomingIds = <int>{};

  for (final configData in incoming) {
    final parsedId = int.tryParse('${configData["id"] ?? ''}');
    if (parsedId == null) {
      continue;
    }

    incomingIds.add(parsedId);
    final config = getConnectionConfig(parsedId);
    config.id.value = parsedId;
    config.connectionType.value = configData["connectionType"]?.toString() ?? 'ir';
    config.entityId.value = configData["entityId"]?.toString() ?? '';
    config.brand.value = configData["brand"]?.toString() ?? '';
    config.action.value = configData["action"]?.toString() ?? '';
    config.gesture.value = configData["gesture"]?.toString() ?? '';
    config.sound.value = configData["sound"]?.toString() ?? '';
    config.hand.value = configData["hand"]?.toString() ?? '';
    config.isSynced.value = true;
  }

  final existingIds = connectionConfigs.keys.toList(growable: false);
  for (final id in existingIds) {
    if (!incomingIds.contains(id)) {
      removeConnectionConfig(id);
    }
  }

  final sortedIds = incomingIds.toList()..sort();
  connectionsList.value = sortedIds;
  _nextConnectionId = sortedIds.isEmpty ? 1 : (sortedIds.last + 1);
  saveConfigsToFile();
}
