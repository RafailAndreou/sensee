import 'package:flutter/material.dart';

// Legacy global variables (kept for backward compatibility){
ValueNotifier<int> connectionId = ValueNotifier(-1);
ValueNotifier<String> brand = ValueNotifier("");
ValueNotifier<String> action = ValueNotifier("");
ValueNotifier<String> gesture = ValueNotifier("");
ValueNotifier<String> sound = ValueNotifier("");
ValueNotifier<String> hand = ValueNotifier("");

// Connection-specific configuration
class ConnectionConfig {
  final ValueNotifier<int> id = ValueNotifier(-1);
  final ValueNotifier<String> connectionType = ValueNotifier("ir");
  final ValueNotifier<String> entityId = ValueNotifier("");
  final ValueNotifier<String> brand = ValueNotifier("");
  final ValueNotifier<String> action = ValueNotifier("");
  final ValueNotifier<String> gesture = ValueNotifier("");
  final ValueNotifier<String> sound = ValueNotifier("");
  final ValueNotifier<String> hand = ValueNotifier("");
  final ValueNotifier<bool> isSynced = ValueNotifier(false);
}

// Store configuration for each connection ID
final Map<int, ConnectionConfig> connectionConfigs = {};

// Get or create config for a connection
ConnectionConfig getConnectionConfig(int connectionId) {
  return connectionConfigs.putIfAbsent(connectionId, () => ConnectionConfig());
}

// Remove config when connection is deleted
void removeConnectionConfig(int connectionId) {
  connectionConfigs.remove(connectionId);
}

void printMap(Map<String, dynamic> configData) {
  configData.forEach((key, value) {
    debugPrint('[Config] $key: $value');
  });
}
