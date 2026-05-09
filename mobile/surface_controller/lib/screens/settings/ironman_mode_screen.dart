import 'dart:async';

import 'package:flutter/material.dart';
import 'package:surface_controller/globals/locale.dart';
import 'package:surface_controller/server/config_service.dart';

const _kGestures = [
  '',
  'Open Palm',
  'Closed Fist',
  'Thumb Up',
  'Thumb Down',
  'Victory',
  'ILoveYou',
  'Pointing Up',
  'Thumb+Index',
  'Thumb+Middle',
  'Thumb+Ring',
  'Thumb+Pinky',
];

const _kActions = [
  ('move_cursor',     'Move Cursor'),
  ('scroll',          'Scroll'),
  ('left_click',      'Left Click'),
  ('right_click',     'Right Click'),
  ('tab_forward',     'Tab Forward'),
  ('tab_backward',    'Tab Backward'),
  ('new_tab',         'New Tab'),
  ('close_tab',       'Close Tab'),
  ('task_view',       'Task View'),
  ('browser_forward', 'Browser Forward'),
  ('browser_back',    'Browser Back'),
  ('browser_search',  'Browser Search'),
  ('screenshot',      'Screenshot'),
];

class IronmanModeScreen extends StatefulWidget {
  const IronmanModeScreen({super.key});

  @override
  State<IronmanModeScreen> createState() => _IronmanModeScreenState();
}

class _IronmanModeScreenState extends State<IronmanModeScreen> {
  double _gain = 5000;
  double _damp = 50;
  double _sensitivity = 3;
  double _steps = 10;
  double _delayMs = 1.0;
  double _scroll = 10;
  Map<String, String> _gestureMap = {};

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
    final data = await loadIronmanParams();
    if (!mounted) return;
    setState(() {
      _loading = false;
      if (data != null) {
        _gain        = (data['gain'] as num?)?.toDouble() ?? 5000;
        _damp        = (data['damp'] as num?)?.toDouble() ?? 50;
        _sensitivity = (data['sensitivity'] as num?)?.toDouble() ?? 3;
        _steps       = (data['steps'] as num?)?.toDouble() ?? 10;
        _delayMs     = ((data['delay'] as num?)?.toDouble() ?? 0.001) * 1000;
        _scroll      = (data['scroll'] as num?)?.toDouble() ?? 10;
        final raw = data['gesture_map'];
        if (raw is Map) {
          _gestureMap = raw.map((k, v) => MapEntry(k.toString(), v?.toString() ?? ''));
        }
      }
    });
  }

  void _scheduleSave() {
    _debounce?.cancel();
    _debounce = Timer(const Duration(milliseconds: 500), _save);
  }

  Future<void> _save() async {
    if (_saving) return;
    setState(() => _saving = true);
    final current = await loadIronmanParams() ?? {};
    await saveIronmanParams({
      ...current,
      'gain':        _gain.round(),
      'damp':        _damp.round(),
      'sensitivity': _sensitivity.round(),
      'steps':       _steps.round(),
      'delay':       double.parse((_delayMs / 1000).toStringAsFixed(4)),
      'scroll':      _scroll.round(),
      'gesture_map': _gestureMap,
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
                const Icon(Icons.bolt, color: Colors.blue, size: 22),
                const SizedBox(width: 8),
                Text(t('ironman_title'),
                    style: const TextStyle(fontWeight: FontWeight.w700)),
              ],
            ),
            actions: [
              if (_saving)
                const Padding(
                  padding: EdgeInsets.all(14),
                  child: SizedBox(
                    width: 18, height: 18,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  ),
                ),
            ],
          ),
          body: _loading
              ? const Center(child: CircularProgressIndicator())
              : ListView(
                  padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
                  children: [
                    _sectionHeader(t('ironman_section_motion')),
                    const SizedBox(height: 12),
                    _ParamSlider(
                      label: t('ironman_gain_label'),
                      hint: t('ironman_gain_hint'),
                      value: _gain, min: 100, max: 10000, divisions: 99,
                      displayValue: _gain.round().toString(),
                      onChanged: (v) { setState(() => _gain = v); _scheduleSave(); },
                    ),
                    _ParamSlider(
                      label: t('ironman_damp_label'),
                      hint: t('ironman_damp_hint'),
                      value: _damp, min: 1, max: 200, divisions: 199,
                      displayValue: _damp.round().toString(),
                      onChanged: (v) { setState(() => _damp = v); _scheduleSave(); },
                    ),
                    _ParamSlider(
                      label: t('ironman_sensitivity_label'),
                      hint: t('ironman_sensitivity_hint'),
                      value: _sensitivity, min: 1, max: 20, divisions: 19,
                      displayValue: _sensitivity.round().toString(),
                      onChanged: (v) { setState(() => _sensitivity = v); _scheduleSave(); },
                    ),
                    _ParamSlider(
                      label: t('ironman_steps_label'),
                      hint: t('ironman_steps_hint'),
                      value: _steps, min: 1, max: 100, divisions: 99,
                      displayValue: _steps.round().toString(),
                      onChanged: (v) { setState(() => _steps = v); _scheduleSave(); },
                    ),
                    _ParamSlider(
                      label: t('ironman_delay_label'),
                      hint: t('ironman_delay_hint'),
                      value: _delayMs, min: 0.1, max: 10, divisions: 99,
                      displayValue: '${_delayMs.toStringAsFixed(1)} ms',
                      onChanged: (v) { setState(() => _delayMs = v); _scheduleSave(); },
                    ),
                    _ParamSlider(
                      label: t('ironman_scroll_label'),
                      hint: t('ironman_scroll_hint'),
                      value: _scroll, min: 1, max: 50, divisions: 49,
                      displayValue: _scroll.round().toString(),
                      onChanged: (v) { setState(() => _scroll = v); _scheduleSave(); },
                    ),
                    const SizedBox(height: 24),
                    _sectionHeader(t('ironman_section_gestures')),
                    const SizedBox(height: 12),
                    ..._kActions.map(((String, String) entry) {
                      final (key, label) = entry;
                      final current = _gestureMap[key] ?? '';
                      return _GestureRow(
                        label: label,
                        value: current,
                        onChanged: (v) {
                          setState(() => _gestureMap = {..._gestureMap, key: v ?? ''});
                          _scheduleSave();
                        },
                      );
                    }),
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
        color: Colors.blue,
        letterSpacing: 0.8,
      ),
    );
  }
}

class _ParamSlider extends StatelessWidget {
  final String label;
  final String hint;
  final double value;
  final double min;
  final double max;
  final int divisions;
  final String displayValue;
  final ValueChanged<double> onChanged;

  const _ParamSlider({
    required this.label,
    required this.hint,
    required this.value,
    required this.min,
    required this.max,
    required this.divisions,
    required this.displayValue,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Row(
            children: [
              Text(label,
                  style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600)),
              const SizedBox(width: 6),
              Expanded(
                child: Text(hint,
                    style: TextStyle(
                        fontSize: 12,
                        color: Theme.of(context).textTheme.bodySmall?.color)),
              ),
              Text(displayValue,
                  style: const TextStyle(
                      fontSize: 14, fontWeight: FontWeight.w600, color: Colors.blue)),
            ],
          ),
          SliderTheme(
            data: SliderTheme.of(context).copyWith(
              trackHeight: 3,
              thumbShape: const RoundSliderThumbShape(enabledThumbRadius: 7),
              overlayShape: const RoundSliderOverlayShape(overlayRadius: 14),
            ),
            child: Slider(
              value: value.clamp(min, max),
              min: min, max: max, divisions: divisions,
              activeColor: Colors.blue,
              onChanged: onChanged,
            ),
          ),
        ],
      ),
    );
  }
}

class _GestureRow extends StatelessWidget {
  final String label;
  final String value;
  final ValueChanged<String?> onChanged;

  const _GestureRow({required this.label, required this.value, required this.onChanged});

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final current = _kGestures.contains(value) ? value : '';

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        children: [
          Expanded(
            child: Text(label,
                style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w500)),
          ),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 2),
            decoration: BoxDecoration(
              color: isDark ? const Color(0xFF374151) : const Color(0xFFEEF2F7),
              borderRadius: BorderRadius.circular(8),
            ),
            child: DropdownButtonHideUnderline(
              child: DropdownButton<String>(
                value: current,
                isDense: true,
                style: TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.w600,
                  color: current.isEmpty
                      ? Theme.of(context).textTheme.bodySmall?.color
                      : Colors.blue,
                ),
                dropdownColor: Theme.of(context).cardColor,
                items: _kGestures.map((g) => DropdownMenuItem(
                  value: g,
                  child: Text(
                    g.isEmpty ? '— None —' : g,
                    style: TextStyle(
                      fontSize: 13,
                      color: g.isEmpty
                          ? Theme.of(context).textTheme.bodySmall?.color
                          : Theme.of(context).textTheme.bodyMedium?.color,
                    ),
                  ),
                )).toList(),
                onChanged: onChanged,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
