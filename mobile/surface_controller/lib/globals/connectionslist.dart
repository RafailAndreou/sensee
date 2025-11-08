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
