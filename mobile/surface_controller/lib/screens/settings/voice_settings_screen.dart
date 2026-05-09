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
  Timer? _saveDebounce;

  // Model download status
  String _modelStatus = 'idle'; // idle | loading | ready
  String? _loadedModel;
  Timer? _pollTimer;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _saveDebounce?.cancel();
    _pollTimer?.cancel();
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
    _refreshStatus();
  }

  Future<void> _refreshStatus() async {
    final status = await loadVoiceStatus();
    if (!mounted) return;
    setState(() {
      _modelStatus = status?['status'] as String? ?? 'idle';
      _loadedModel = status?['model'] as String?;
    });
  }

  void _startPolling() {
    _pollTimer?.cancel();
    _pollTimer = Timer.periodic(const Duration(seconds: 2), (_) async {
      final status = await loadVoiceStatus();
      if (!mounted) return;
      final s = status?['status'] as String? ?? 'idle';
      final m = status?['model'] as String?;
      setState(() {
        _modelStatus = s;
        _loadedModel = m;
      });
      if (s == 'ready' && m == _model) {
        _pollTimer?.cancel();
      }
    });
  }

  void _scheduleSave() {
    _saveDebounce?.cancel();
    _saveDebounce = Timer(const Duration(milliseconds: 400), _save);
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
    // Server triggers preload on POST; start polling until ready
    _startPolling();
  }

  bool get _isModelDownloading =>
      _modelStatus == 'loading' && _loadedModel == _model;

  bool get _isModelReady =>
      _modelStatus == 'ready' && _loadedModel == _model;

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
                    // ── Model picker ──────────────────────────────
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
                        if (v == null) return;
                        setState(() => _model = v);
                        _scheduleSave();
                      },
                    ),
                    // ── Download status badge ─────────────────────
                    const SizedBox(height: 10),
                    _ModelStatusBadge(
                      isDownloading: _isModelDownloading,
                      isReady: _isModelReady,
                      modelName: _model,
                    ),
                    const SizedBox(height: 8),
                    // ── Language picker ───────────────────────────
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
                      icon: Icons.mouse,
                      text:
                          'Click inside any text field (search bar, address bar, chat…)',
                    ),
                    const SizedBox(height: 8),
                    _InfoCard(
                      icon: Icons.mic,
                      text:
                          'Speak — Whisper transcribes after you stop talking',
                    ),
                    const SizedBox(height: 8),
                    _InfoCard(
                      icon: Icons.keyboard,
                      text:
                          'The transcribed text is pasted at the cursor position',
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

class _ModelStatusBadge extends StatelessWidget {
  final bool isDownloading;
  final bool isReady;
  final String modelName;

  const _ModelStatusBadge({
    required this.isDownloading,
    required this.isReady,
    required this.modelName,
  });

  @override
  Widget build(BuildContext context) {
    if (!isDownloading && !isReady) return const SizedBox.shrink();

    final isDark = Theme.of(context).brightness == Brightness.dark;
    final color = isDownloading ? Colors.orange : Colors.green;
    final bg = isDownloading
        ? (isDark ? const Color(0xFF2D1F00) : const Color(0xFFFFF3E0))
        : (isDark ? const Color(0xFF0D2A1A) : const Color(0xFFE8F5E9));

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: color.withOpacity(0.4)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (isDownloading) ...[
            SizedBox(
              width: 14,
              height: 14,
              child: CircularProgressIndicator(
                strokeWidth: 2,
                color: Colors.orange,
              ),
            ),
            const SizedBox(width: 8),
            Text(
              'Downloading $modelName…',
              style: TextStyle(
                fontSize: 13,
                fontWeight: FontWeight.w600,
                color: Colors.orange,
              ),
            ),
          ] else ...[
            Icon(Icons.check_circle, size: 16, color: Colors.green),
            const SizedBox(width: 6),
            Text(
              '$modelName ready',
              style: const TextStyle(
                fontSize: 13,
                fontWeight: FontWeight.w600,
                color: Colors.green,
              ),
            ),
          ],
        ],
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
