import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

const String _prefKey = 'app_theme';

final ValueNotifier<String> appTheme = ValueNotifier<String>('light');

Future<void> initTheme() async {
  final prefs = await SharedPreferences.getInstance();
  final saved = prefs.getString(_prefKey);
  if (saved != null) {
    appTheme.value = saved;
  }
}

Future<void> setTheme(String theme) async {
  appTheme.value = theme;
  final prefs = await SharedPreferences.getInstance();
  await prefs.setString(_prefKey, theme);
}

final ThemeData lightTheme = ThemeData(
  brightness: Brightness.light,
  colorScheme: const ColorScheme.light(primary: Colors.blue),
  scaffoldBackgroundColor: const Color(0xFFEAEDF4),
  cardColor: Colors.white,
  appBarTheme: const AppBarTheme(
    backgroundColor: Colors.white,
    foregroundColor: Colors.black87,
    surfaceTintColor: Colors.transparent,
    elevation: 1,
  ),
);

final ThemeData darkTheme = ThemeData(
  brightness: Brightness.dark,
  colorScheme: const ColorScheme.dark(primary: Colors.blue),
  scaffoldBackgroundColor: const Color(0xFF121212),
  cardColor: const Color(0xFF1E1E1E),
  appBarTheme: const AppBarTheme(
    backgroundColor: Color(0xFF1A1A1A),
    foregroundColor: Colors.white,
    surfaceTintColor: Colors.transparent,
    elevation: 0,
  ),
);
