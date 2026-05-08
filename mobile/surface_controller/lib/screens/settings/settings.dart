import 'package:flutter/material.dart';
import 'package:surface_controller/globals/app_theme.dart';
import 'package:surface_controller/globals/locale.dart';
import 'package:surface_controller/globals/sizes.dart';
import 'widgets/settingsbutton.dart';
import '../setup/ha_settings.dart';
import '../gestureSettings/gesture_settings.dart';
import '../cameraSettings/camera_settings.dart';

class Settings extends StatelessWidget {
  const Settings({super.key});

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<String>(
      valueListenable: appLocale,
      builder: (context, locale, _) {
        return Scaffold(
          appBar: AppBar(
            title: Text(
              t('nav_settings'),
              style: const TextStyle(fontWeight: FontWeight.w700),
            ),
          ),
          body: Container(
            width: double.infinity,
            height: double.infinity,
            color: Theme.of(context).scaffoldBackgroundColor,
            child: Column(
              children: [
                const SizedBox(height: 24),
                Settingsbutton(
                  image: const Icon(Icons.dns, size: 32),
                  title: t('settings_server_title'),
                  description: t('settings_server_description'),
                  onTap: () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (context) => const HASettings(),
                      ),
                    );
                  },
                ),
                const SizedBox(height: 24),
                Settingsbutton(
                  image: const Icon(Icons.back_hand, size: 32),
                  title: t('settings_gesture_title'),
                  description: t('settings_gesture_description'),
                  onTap: () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (context) => const Gesturesettings(),
                      ),
                    );
                  },
                ),
                const SizedBox(height: 24),
                Settingsbutton(
                  image: const Icon(Icons.videocam, size: 32),
                  title: t('settings_camera_title'),
                  description: t('settings_camera_description'),
                  onTap: () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (context) => const CameraSettingsScreen(),
                      ),
                    );
                  },
                ),
                const SizedBox(height: 24),
                _LanguageToggleCard(locale: locale),
                const SizedBox(height: 24),
                ValueListenableBuilder<String>(
                  valueListenable: appTheme,
                  builder: (context, theme, _) =>
                      _ThemeToggleCard(theme: theme),
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}

class _LanguageToggleCard extends StatelessWidget {
  final String locale;
  const _LanguageToggleCard({required this.locale});

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return Container(
      width: getProportionalWidth(context, 350),
      height: 115,
      decoration: BoxDecoration(
        color: Theme.of(context).cardColor,
        borderRadius: BorderRadius.circular(12),
        boxShadow: const [
          BoxShadow(color: Colors.black12, blurRadius: 5, offset: Offset(0, 2)),
        ],
      ),
      padding: const EdgeInsets.all(16),
      child: Row(
        children: [
          const Icon(Icons.language, size: 32),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  t('settings_language_title'),
                  style: const TextStyle(
                    fontSize: 20,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const SizedBox(height: 6),
                Text(t('settings_language_description')),
              ],
            ),
          ),
          Container(
            padding: const EdgeInsets.all(4),
            decoration: BoxDecoration(
              color: isDark
                  ? const Color(0xFF374151)
                  : const Color(0xFFDCE3EC),
              borderRadius: BorderRadius.circular(999),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                _LangPill(label: 'EN', code: 'en', activeLocale: locale),
                _LangPill(label: 'ΕΛ', code: 'el', activeLocale: locale),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _LangPill extends StatelessWidget {
  final String label;
  final String code;
  final String activeLocale;

  const _LangPill({
    required this.label,
    required this.code,
    required this.activeLocale,
  });

  @override
  Widget build(BuildContext context) {
    final isActive = activeLocale == code;
    return GestureDetector(
      onTap: () => setLocale(code),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 180),
        curve: Curves.easeOut,
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
        decoration: BoxDecoration(
          color: isActive ? Colors.blue : Colors.transparent,
          borderRadius: BorderRadius.circular(999),
        ),
        child: Text(
          label,
          style: TextStyle(
            fontWeight: FontWeight.w600,
            color: isActive
                ? Colors.white
                : Theme.of(context).textTheme.bodyMedium?.color,
          ),
        ),
      ),
    );
  }
}

class _ThemeToggleCard extends StatelessWidget {
  final String theme;
  const _ThemeToggleCard({required this.theme});

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return Container(
      width: getProportionalWidth(context, 350),
      height: 115,
      decoration: BoxDecoration(
        color: Theme.of(context).cardColor,
        borderRadius: BorderRadius.circular(12),
        boxShadow: const [
          BoxShadow(color: Colors.black12, blurRadius: 5, offset: Offset(0, 2)),
        ],
      ),
      padding: const EdgeInsets.all(16),
      child: Row(
        children: [
          const Icon(Icons.dark_mode_outlined, size: 32),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  t('settings_theme_title'),
                  style: const TextStyle(
                    fontSize: 20,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const SizedBox(height: 6),
                Text(t('settings_theme_description')),
              ],
            ),
          ),
          Container(
            padding: const EdgeInsets.all(4),
            decoration: BoxDecoration(
              color: isDark
                  ? const Color(0xFF374151)
                  : const Color(0xFFDCE3EC),
              borderRadius: BorderRadius.circular(999),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                _ThemePill(
                  label: t('theme_light'),
                  code: 'light',
                  activeTheme: theme,
                ),
                _ThemePill(
                  label: t('theme_dark'),
                  code: 'dark',
                  activeTheme: theme,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _ThemePill extends StatelessWidget {
  final String label;
  final String code;
  final String activeTheme;

  const _ThemePill({
    required this.label,
    required this.code,
    required this.activeTheme,
  });

  @override
  Widget build(BuildContext context) {
    final isActive = activeTheme == code;
    return GestureDetector(
      onTap: () => setTheme(code),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 180),
        curve: Curves.easeOut,
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
        decoration: BoxDecoration(
          color: isActive ? Colors.blue : Colors.transparent,
          borderRadius: BorderRadius.circular(999),
        ),
        child: Text(
          label,
          style: TextStyle(
            fontWeight: FontWeight.w600,
            color: isActive
                ? Colors.white
                : Theme.of(context).textTheme.bodyMedium?.color,
          ),
        ),
      ),
    );
  }
}
