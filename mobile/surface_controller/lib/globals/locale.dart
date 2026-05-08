import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:surface_controller/l10n/strings.dart';

const String _prefKey = 'app_locale';

final ValueNotifier<String> appLocale = ValueNotifier<String>('en');

Future<void> initLocale() async {
  final prefs = await SharedPreferences.getInstance();
  final saved = prefs.getString(_prefKey);
  if (saved != null) {
    appLocale.value = saved;
  }
}

Future<void> setLocale(String locale) async {
  appLocale.value = locale;
  final prefs = await SharedPreferences.getInstance();
  await prefs.setString(_prefKey, locale);
}

String t(String key) => AppStrings.of(appLocale.value, key);

String tFormat(String key, String value) => t(key).replaceFirst('%s', value);
