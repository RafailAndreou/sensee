import 'package:flutter/material.dart';

ValueNotifier<List<int>> connectionsList = ValueNotifier<List<int>>([0]);
int _nextConnectionId = 1;

void addNewConnection() {
  connectionsList.value = List.from(connectionsList.value)
    ..add(_nextConnectionId++);
}

void removeConnection(int id) {
  connectionsList.value = List.from(connectionsList.value)
    ..removeWhere((connectionId) => connectionId == id);

  // Reset counter if list becomes empty (safe to reuse IDs)
  if (connectionsList.value.isEmpty) {
    _nextConnectionId = 0;
  }
}
