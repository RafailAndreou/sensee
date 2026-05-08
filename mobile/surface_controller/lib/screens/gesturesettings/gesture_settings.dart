import 'package:flutter/material.dart';
import 'package:surface_controller/globals/locale.dart';
import 'package:surface_controller/globals/sizes.dart';
import 'package:surface_controller/server/config_service.dart';

class Gesturesettings extends StatefulWidget {
  const Gesturesettings({super.key});

  @override
  State<Gesturesettings> createState() => _GesturesettingsState();
}

class _GesturesettingsState extends State<Gesturesettings> {
  bool _wakeEnabled = false;
  String _selectedGesture = 'Open Hand';
  double _holdDurationSeconds = 2;
  double _activeWindowSeconds = 5;

  double _clampValue(double value, double min, double max) {
    return value.clamp(min, max).toDouble();
  }

  @override
  void initState() {
    super.initState();
    _loadGestureSettings();
  }

  Future<void> _loadGestureSettings() async {
    final localSettings = await loadGestureSettingsLocal();
    if (mounted) {
      setState(() {
        _wakeEnabled = localSettings['wakeEnabled'] ?? false;
        _selectedGesture = localSettings['selectedGesture'] ?? 'Open Hand';
        _holdDurationSeconds = _clampValue(
          (localSettings['holdDurationSeconds'] ?? 2).toDouble(),
          0,
          5,
        );
        _activeWindowSeconds = _clampValue(
          (localSettings['activeWindowSeconds'] ?? 5).toDouble(),
          5,
          20,
        );
      });
    }

    final serverSettings = await loadGestureSettings();
    if (serverSettings != null && mounted) {
      setState(() {
        _wakeEnabled = serverSettings['wakeEnabled'] ?? false;
        _selectedGesture = serverSettings['selectedGesture'] ?? 'Open Hand';
        _holdDurationSeconds = _clampValue(
          (serverSettings['holdDurationSeconds'] ?? 2).toDouble(),
          0,
          5,
        );
        _activeWindowSeconds = _clampValue(
          (serverSettings['activeWindowSeconds'] ?? 5).toDouble(),
          5,
          20,
        );
      });
      await saveGestureSettingsLocal(
        wakeEnabled: _wakeEnabled,
        holdDurationSeconds: _holdDurationSeconds,
        activeWindowSeconds: _activeWindowSeconds,
        selectedGesture: _selectedGesture,
      );
    }
  }

  Future<void> _saveSettings() async {
    await saveGestureSettingsLocal(
      wakeEnabled: _wakeEnabled,
      holdDurationSeconds: _holdDurationSeconds,
      activeWindowSeconds: _activeWindowSeconds,
      selectedGesture: _selectedGesture,
    );
    await sendGestureSettings(
      wakeEnabled: _wakeEnabled,
      holdDurationSeconds: _holdDurationSeconds,
      activeWindowSeconds: _activeWindowSeconds,
      selectedGesture: _selectedGesture,
    );
    if (mounted) {
      Navigator.pop(context);
    }
  }

  String _formatSeconds(double value) {
    return '${value.toInt()} ${t('gesture_seconds_suffix')}';
  }

  Widget _buildLabeledSlider({
    required String title,
    required double value,
    required ValueChanged<double> onChanged,
    required double min,
    required double max,
    required int divisions,
  }) {
    final clampedValue = _clampValue(value, min, max);
    final stepSize = (max - min) / divisions;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          title,
          style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w300),
          textAlign: TextAlign.left,
        ),
        Text(
          _formatSeconds(value),
          textAlign: TextAlign.left,
          style: const TextStyle(fontSize: 20, color: Colors.black),
        ),
        const SizedBox(height: 15),
        SliderTheme(
          data: SliderTheme.of(context).copyWith(
            activeTrackColor: Colors.blue,
            inactiveTrackColor: Colors.grey[300],
            thumbColor: Colors.blue,
            overlayColor: Colors.blue.withValues(alpha: 0.2),
            valueIndicatorColor: Colors.blue,
          ),
          child: Slider(
            value: clampedValue,
            min: min,
            max: max,
            divisions: divisions,
            label: _formatSeconds(clampedValue),
            onChanged: onChanged,
          ),
        ),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 8),
          child: Row(
            children: List.generate(divisions + 1, (index) {
              final tickValue = min + stepSize * index;
              final isActive =
                  index <= ((clampedValue - min) / stepSize).round();

              return Expanded(
                child: Column(
                  children: [
                    Container(
                      width: 6,
                      height: 6,
                      decoration: BoxDecoration(
                        color: isActive ? Colors.blue : Colors.grey,
                        shape: BoxShape.circle,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      '${tickValue.toInt()}s',
                      style: TextStyle(fontSize: 12, color: Colors.grey[700]),
                    ),
                  ],
                ),
              );
            }),
          ),
        ),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<String>(
      valueListenable: appLocale,
      builder: (context, _, __) {
        return Scaffold(
          backgroundColor: const Color(0xFFEAEDF4),
          appBar: AppBar(
            title: Text(
              t('gesture_settings_title'),
              style: const TextStyle(fontSize: 27, fontWeight: FontWeight.w500),
            ),
          ),
          body: Column(
            children: [
              Container(
                margin: const EdgeInsets.all(16),
                width: getProportionalHeight(context, 500),
                height: getProportionalHeight(context, 600),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: Colors.black12, width: 2),
                ),
                padding: const EdgeInsets.all(24),
                child: SingleChildScrollView(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        t('gesture_wakeup_section'),
                        style: const TextStyle(
                          fontSize: 24,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                      const SizedBox(height: 16),
                      Row(
                        children: [
                          const Icon(Icons.back_hand, size: 40),
                          const SizedBox(width: 16),
                          Expanded(
                            child: Text(
                              t('gesture_enable_wakeup'),
                              style: const TextStyle(
                                fontSize: 18,
                                fontWeight: FontWeight.w500,
                              ),
                            ),
                          ),
                          Switch.adaptive(
                            value: _wakeEnabled,
                            activeTrackColor: Colors.blue,
                            onChanged: (val) {
                              setState(() {
                                _wakeEnabled = val;
                              });
                            },
                          ),
                        ],
                      ),
                      const SizedBox(height: 50),
                      _scrollDownButton(context),
                      const SizedBox(height: 20),
                      _buildLabeledSlider(
                        title: t('gesture_hold_duration'),
                        value: _holdDurationSeconds,
                        min: 0,
                        max: 5,
                        divisions: 5,
                        onChanged: (value) {
                          setState(() {
                            _holdDurationSeconds = value;
                          });
                        },
                      ),
                      const SizedBox(height: 30),
                      _buildLabeledSlider(
                        title: t('gesture_active_window'),
                        value: _activeWindowSeconds,
                        min: 5,
                        max: 20,
                        divisions: 4,
                        onChanged: (value) {
                          setState(() {
                            _activeWindowSeconds = value;
                          });
                        },
                      ),
                    ],
                  ),
                ),
              ),
              TextButton(
                style: TextButton.styleFrom(
                  backgroundColor: Colors.blue,
                  padding: const EdgeInsets.symmetric(
                    horizontal: 100,
                    vertical: 12,
                  ),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(8),
                  ),
                ),
                onPressed: _saveSettings,
                child: Text(
                  t('gesture_save'),
                  style: const TextStyle(color: Colors.white),
                ),
              ),
            ],
          ),
        );
      },
    );
  }

  Widget _scrollDownButton(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.only(left: 8.0, bottom: 6.0),
          child: Text(
            t('gesture_wakeup_section'),
            style: TextStyle(
              fontSize: 12,
              color: Colors.grey[700],
              fontWeight: FontWeight.w500,
            ),
          ),
        ),
        FractionallySizedBox(
          widthFactor: 0.9,
          child: Container(
            height: 56,
            padding: const EdgeInsets.symmetric(horizontal: 16),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: Colors.black12, width: 1.5),
            ),
            child: DropdownButtonHideUnderline(
              child: DropdownButton<String>(
                isExpanded: true,
                borderRadius: BorderRadius.circular(12),
                icon: const Icon(Icons.keyboard_arrow_down_rounded),
                onChanged: (value) {
                  if (value == null) return;
                  setState(() {
                    _selectedGesture = value;
                  });
                },
                value: _selectedGesture,
                items: [
                  DropdownMenuItem(
                    value: "Open Hand",
                    child: Text(t('gesture_dropdown_open_hand')),
                  ),
                  DropdownMenuItem(
                    value: "Closed Fist",
                    child: Text(t('gesture_dropdown_closed_fist')),
                  ),
                  DropdownMenuItem(
                    value: "Thumbs+Index",
                    child: Text(t('gesture_dropdown_thumbs_index')),
                  ),
                  DropdownMenuItem(
                    value: "Middle+Thumb",
                    child: Text(t('gesture_dropdown_middle_thumb')),
                  ),
                ],
              ),
            ),
          ),
        ),
      ],
    );
  }
}
