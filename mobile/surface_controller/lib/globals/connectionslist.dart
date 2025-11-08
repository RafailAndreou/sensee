import 'package:flutter/material.dart';
import 'global.dart';
import 'dart:io';
import 'dart:convert';
import 'package:path_provider/path_provider.dart';

ValueNotifier<List<int>> connectionsList = ValueNotifier<List<int>>([0]);
int _nextConnectionId = 1;

void addNewConnection() {
  connectionsList.value = List.from(connectionsList.value)
    ..add(_nextConnectionId++);
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
      'brand': config.brand.value,
      'action': config.action.value,
      'gesture': config.gesture.value,
      'sound': config.sound.value,
      'hand': config.hand.value,
    };
  });

  final jsonString = jsonEncode(allConfigs);
  debugPrint('All Connection Configs as JSON: $jsonString');
}

void saveConfigsToFile() async {
  final Map<String, dynamic> allConfigs = {};

  connectionConfigs.forEach((connectionId, config) {
    allConfigs[connectionId.toString()] = {
      'brand': config.brand.value,
      'action': config.action.value,
      'gesture': config.gesture.value,
      'sound': config.sound.value,
      'hand': config.hand.value,
    };
  });

  final jsonString = jsonEncode(allConfigs);
  final file = await _localFile;
  await file.writeAsString(jsonString);
}

void loadConfigurationsFromFile() async {
  final file = await _localFile;
  final jsonString = await file.readAsString();
  final Map<String, dynamic> allConfigs = jsonDecode(jsonString);

  allConfigs.forEach((connectionIdStr, configData) {
    final connectionId = int.parse(connectionIdStr);
    final config = getConnectionConfig(connectionId);

    config.brand.value = configData['brand'] ?? '';
    config.action.value = configData['action'] ?? '';
    config.gesture.value = configData['gesture'] ?? '';
    config.sound.value = configData['sound'] ?? '';
    config.hand.value = configData['hand'] ?? '';
    debugPrint('Loaded config for connection ID $connectionId');
  });
}
