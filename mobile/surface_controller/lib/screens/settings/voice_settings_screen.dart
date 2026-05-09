import 'dart:async';

import 'package:flutter/material.dart';
import 'package:surface_controller/globals/locale.dart';
import 'package:surface_controller/server/config_service.dart';

const _kModels = ['tiny', 'base', 'small'];
const _kModelLabels = {
  'tiny': 'Tiny — fastest (~39 MB)',
  'base': 'Base (~74 MB)',
  'small': 'Small — best accuracy (~244 MB)',
};
const _kLanguages = [
  ('en', 'English'),
  ('el', 'Greek'),
  ('auto', 'Auto-detect'),
];

class VoiceSettingsScreen extends StatefulWidget {
  const VoiceSettingsScreen({super.key});

  @override
  State<VoiceSettingsScreen> createState() => _VoiceSettingsScreenState();
}

class _VoiceSettingsScreenState extends State<VoiceSettingsScreen> {
  String _model = 'tiny';
  String _language = 'en';
  bool _loading = true;
  bool _saving = false;
  Timer? _debounce;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _debounce?.cancel();
    super.dispose();
  }

  Future<void> _load() async {
    final data = await loadVoiceSettings();
    if (!mounted) return;
    setState(() {
      _loading = false;
      if (data != null) {
        _model = data['model'] as String? ?? 'tiny';
        _language = data['language'] as String? ?? 'en';
      }
    });
  }

  void _scheduleSave() {
    _debounce?.cancel();
    _debounce = Timer(const Duration(milliseconds: 400), _save);
  }

  Future<void> _save() async {
    if (_saving) return;
    setState(() => _saving = true);
    final current = await loadVoiceSettings() ?? {};
    await saveVoiceSettings({
      ...current,
      'model': _model,
      'language': _language,
    });
    if (mounted) setState(() => _saving = false);
  }

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<String>(
      valueListenable: appLocale,
      builder: (context, _, __) {
        return Scaffold(
          appBar: AppBar(
            title: Row(
              children: [
                const Icon(Icons.mic, color: Colors.green, size: 22),
                const SizedBox(width: 8),
                Text(t('voice_title'),
                    style: const TextStyle(fontWeight: FontWeight.w700)),
              ],
            ),
            actions: [
              if (_saving)
                const Padding(
                  padding: EdgeInsets.all(14),
                  child: SizedBox(
                    width: 18,
                    height: 18,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  ),
                ),
            ],
          ),
          body: _loading
              ? const Center(child: CircularProgressIndicator())
              : ListView(
                  padding: const EdgeInsets.symmetric(
                      horizontal: 20, vertical: 16),
                  children: [
                    _sectionHeader(t('voice_section_model')),
                    const SizedBox(height: 12),
                    _DropdownRow(
                      label: t('voice_model_label'),
                      value: _model,
                      items: _kModels
                          .map((m) => DropdownMenuItem(
                                value: m,
                                child: Text(_kModelLabels[m] ?? m),
                              ))
                          .toList(),
                      onChanged: (v) {
                        if (v != null) setState(() => _model = v);
                        _scheduleSave();
                      },
                    ),
                    const SizedBox(height: 8),
                    _DropdownRow(
                      label: t('voice_language_label'),
                      value: _language,
                      items: _kLanguages
                          .map(((String, String) e) => DropdownMenuItem(
                                value: e.$1,
                                child: Text(e.$2),
                              ))
                          .toList(),
                      onChanged: (v) {
                        if (v != null) setState(() => _language = v);
                        _scheduleSave();
                      },
                    ),
                    const SizedBox(height: 28),
                    _sectionHeader('HOW IT WORKS'),
                    const SizedBox(height: 12),
                    _InfoCard(
                      icon: Icons.mic,
                      text:
                          'Click inside any text field (search bar, browser address bar, chat…), then speak.',
                    ),
                    const SizedBox(height: 8),
                    _InfoCard(
                      icon: Icons.keyboard,
                      text:
                          'When you stop talking, Whisper transcribes your speech and types it at the cursor position.',
                    ),
                    const SizedBox(height: 8),
                    _InfoCard(
                      icon: Icons.speed,
                      text:
                          'Tiny is fastest and works well for short phrases. Use Small for longer, complex sentences.',
                    ),
                    const SizedBox(height: 32),
                  ],
                ),
        );
      },
    );
  }

  Widget _sectionHeader(String text) {
    return Text(
      text,
      style: const TextStyle(
        fontSize: 12,
        fontWeight: FontWeight.w700,
        color: Colors.green,
        letterSpacing: 0.8,
      ),
    );
  }
}

class _DropdownRow extends StatelessWidget {
  final String label;
  final String value;
  final List<DropdownMenuItem<String>> items;
  final ValueChanged<String?> onChanged;

  const _DropdownRow({
    required this.label,
    required this.value,
    required this.items,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return Row(
      children: [
        Expanded(
          child: Text(label,
              style:
                  const TextStyle(fontSize: 14, fontWeight: FontWeight.w600)),
        ),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 2),
          decoration: BoxDecoration(
            color: isDark
                ? const Color(0xFF374151)
                : const Color(0xFFEEF2F7),
            borderRadius: BorderRadius.circular(8),
          ),
          child: DropdownButtonHideUnderline(
            child: DropdownButton<String>(
              value: value,
              isDense: true,
              style: TextStyle(
                fontSize: 13,
                fontWeight: FontWeight.w600,
                color: Theme.of(context).textTheme.bodyMedium?.color,
              ),
              dropdownColor: Theme.of(context).cardColor,
              items: items,
              onChanged: onChanged,
            ),
          ),
        ),
      ],
    );
  }
}

class _InfoCard extends StatelessWidget {
  final IconData icon;
  final String text;

  const _InfoCard({required this.icon, required this.text});

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: isDark ? const Color(0xFF1A2332) : const Color(0xFFF0F4FA),
        borderRadius: BorderRadius.circular(10),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, size: 18, color: Colors.green),
          const SizedBox(width: 10),
          Expanded(
            child: Text(
              text,
              style: TextStyle(
                fontSize: 13,
                color: Theme.of(context).textTheme.bodyMedium?.color,
                height: 1.4,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
