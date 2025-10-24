import 'package:flutter/material.dart';

ValueNotifier<List<int>> connectionsList = ValueNotifier<List<int>>([0]);

void addNewConnection() {
  connectionsList.value = List.from(connectionsList.value)
    ..add(connectionsList.value.length);
}
