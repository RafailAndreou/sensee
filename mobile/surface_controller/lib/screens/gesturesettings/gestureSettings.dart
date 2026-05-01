import 'package:flutter/material.dart';
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

  @override
  void initState() {
    super.initState();
    _loadGestureSettings();
  }

  Future<void> _loadGestureSettings() async {
    // Load from local storage immediately
    final localSettings = await loadGestureSettingsLocal();
    if (mounted) {
      setState(() {
        _wakeEnabled = localSettings['wakeEnabled'] ?? false;
        _selectedGesture = localSettings['selectedGesture'] ?? 'Open Hand';
        _holdDurationSeconds = (localSettings['holdDurationSeconds'] ?? 2)
            .toDouble();
        _activeWindowSeconds = (localSettings['activeWindowSeconds'] ?? 5)
            .toDouble();
      });
    }

    // Sync with server in the background
    final serverSettings = await loadGestureSettings();
    if (serverSettings != null && mounted) {
      setState(() {
        _wakeEnabled = serverSettings['wakeEnabled'] ?? false;
        _selectedGesture = serverSettings['selectedGesture'] ?? 'Open Hand';
        _holdDurationSeconds = (serverSettings['holdDurationSeconds'] ?? 2)
            .toDouble();
        _activeWindowSeconds = (serverSettings['activeWindowSeconds'] ?? 5)
            .toDouble();
      });
      // Update local cache with server data
      await saveGestureSettingsLocal(
        wakeEnabled: _wakeEnabled,
        holdDurationSeconds: _holdDurationSeconds,
        activeWindowSeconds: _activeWindowSeconds,
        selectedGesture: _selectedGesture,
      );
    }
  }

  String _formatSeconds(double value) {
    return '${value.toInt()} seconds';
  }

  Widget _buildLabeledSlider({
    required String title,
    required double value,
    required ValueChanged<double> onChanged,
    required double min,
    required double max,
    required int divisions,
  }) {
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
            overlayColor: Colors.blue.withOpacity(0.2),
            valueIndicatorColor: Colors.blue,
          ),
          child: Slider(
            value: value,
            min: min,
            max: max,
            divisions: divisions,
            label: _formatSeconds(value),
            onChanged: onChanged,
          ),
        ),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 8),
          child: Row(
            children: List.generate(divisions + 1, (index) {
              final tickValue = min + ((max - min) / divisions) * index;
              final isActive =
                  index <= ((value - min) / ((max - min) / divisions)).round();

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
                      tickValue.toInt().toString() + 's',
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
    return Scaffold(
      backgroundColor: const Color(0xFFEAEDF4),
      appBar: AppBar(
        title: const Text(
          "Gesture Settings",
          style: TextStyle(fontSize: 27, fontWeight: FontWeight.w500),
        ),
      ),
      body: Column(
        children: [
          Container(
            // container takes 90% of the body
            margin: const EdgeInsets.all(16),
            width: getProportionalHeight(context, 500),
            height: getProportionalHeight(context, 600),
            // use decoration to keep rounded corners and background color
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
                  const Text(
                    'Wake-up Gesture',
                    style: TextStyle(fontSize: 24, fontWeight: FontWeight.w700),
                  ),
                  const SizedBox(height: 16),
                  Row(
                    children: [
                      const Icon(Icons.back_hand, size: 40),
                      const SizedBox(width: 16),
                      Expanded(
                        child: Text(
                          "Enable Wake-up Gesture",
                          style: TextStyle(
                            fontSize: 18,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                      ),
                      // toggle switch similar to the provided image
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
                  SizedBox(height: 50),
                  _scrollDownButton(context),
                  SizedBox(height: 20),
                  _buildLabeledSlider(
                    title: 'Hold Duration',
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
                  SizedBox(height: 30),
                  _buildLabeledSlider(
                    title: 'Active Window',
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
            // Blue color
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
            onPressed: () async {
              // Save to local storage immediately
              await saveGestureSettingsLocal(
                wakeEnabled: _wakeEnabled,
                holdDurationSeconds: _holdDurationSeconds,
                activeWindowSeconds: _activeWindowSeconds,
                selectedGesture: _selectedGesture,
              );
              // Send to server
              await sendGestureSettings(
                wakeEnabled: _wakeEnabled,
                holdDurationSeconds: _holdDurationSeconds,
                activeWindowSeconds: _activeWindowSeconds,
                selectedGesture: _selectedGesture,
              );
              if (mounted) {
                Navigator.pop(context);
              }
            },
            child: Text("Save Settings", style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
    );
  }

  Widget _scrollDownButton(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.only(left: 8.0, bottom: 6.0),
          child: Text(
            'Wake-up Gesture',
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
                    child: Text("Open Hand"),
                  ),
                  DropdownMenuItem(
                    value: "Closed Fist",
                    child: Text("Closed Fist"),
                  ),
                  DropdownMenuItem(
                    value: "Thumbs+Index",
                    child: Text("Thumbs + Index"),
                  ),
                  DropdownMenuItem(
                    value: "Middle+Thumb",
                    child: Text("Middle + Thumb"),
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
