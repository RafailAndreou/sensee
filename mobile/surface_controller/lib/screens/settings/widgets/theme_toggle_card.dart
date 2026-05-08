import 'package:flutter/material.dart';
import 'package:surface_controller/globals/app_theme.dart';
import 'package:surface_controller/globals/locale.dart';
import 'package:surface_controller/globals/sizes.dart';

class ThemeToggleCard extends StatelessWidget {
  final String theme;
  const ThemeToggleCard({super.key, required this.theme});

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
