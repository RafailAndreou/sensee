import 'package:flutter/material.dart';

// Legacy global variables (kept for backward compatibility)
ValueNotifier<String> brand = ValueNotifier("test");
ValueNotifier<String> action = ValueNotifier("");
ValueNotifier<String> gesture = ValueNotifier("");
ValueNotifier<String> sound = ValueNotifier("Test");
ValueNotifier<String> hand = ValueNotifier("Test");

// Connection-specific configuration
class ConnectionConfig {
  final ValueNotifier<String> brand = ValueNotifier("test");
  final ValueNotifier<String> action = ValueNotifier("");
  final ValueNotifier<String> gesture = ValueNotifier("");
  final ValueNotifier<String> sound = ValueNotifier("Test");
  final ValueNotifier<String> hand = ValueNotifier("Test");
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
