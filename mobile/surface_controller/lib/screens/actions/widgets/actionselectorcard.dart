import 'package:flutter/material.dart';
import 'package:surface_controller/globals/locale.dart';

typedef OnSelectionChanged =
    void Function({
      required String action,
      required String gesture,
      required String hand,
    });

class ActionSelectorCard extends StatefulWidget {
  final String deviceType;
  final String brand;
  final String initialAction;
  final String initialGesture;
  final String initialHand;
  final OnSelectionChanged? onSelectionChanged;
  final VoidCallback? onSave;

  const ActionSelectorCard({
    super.key,
    required this.deviceType,
    required this.brand,
    this.initialAction = 'Turn on',
    this.initialGesture = 'Index+Thumb',
    this.initialHand = 'Right Hand',
    this.onSelectionChanged,
    this.onSave,
  });

  @override
  State<ActionSelectorCard> createState() => _ActionSelectorCardState();
}

class _ActionSelectorCardState extends State<ActionSelectorCard> {
  late List<String> actions;
  late String selectedAction;
  late String selectedGesture;
  late String selectedHand;
  final List<String> gestures = [
    'Index+Thumb',
    'Middle+Thumb',
    'Open Palm',
    'Fist',
  ];
  final List<String> hands = ['Left Hand', 'Right Hand', 'Both Hands'];

  @override
  void initState() {
    super.initState();
    actions = _actionsForDeviceType(widget.deviceType);
    selectedAction = actions.contains(widget.initialAction)
        ? widget.initialAction
        : actions.first;
    selectedGesture = widget.initialGesture;
    selectedHand = widget.initialHand;
  }

  List<String> _actionsForDeviceType(String type) {
    switch (type.toLowerCase()) {
      case 'pc':
        return [
          'Open Spotify',
          'Open YouTube',
          'Close Window',
          'Open Browser',
        ];
      default:
        return ['Turn on', 'Turn off', 'Increase volume', 'Decrease volume'];
    }
  }

  void _notifySelectionChanged() {
    widget.onSelectionChanged?.call(
      action: selectedAction,
      gesture: selectedGesture,
      hand: selectedHand,
    );
  }

  IconData _deviceIcon(String type) {
    switch (type.toLowerCase()) {
      case 'tv':
        return Icons.tv;
      case 'ac':
        return Icons.ac_unit;
      case 'light':
        return Icons.light_mode;
      case 'fan':
        return Icons.air;
      case 'pc':
        return Icons.computer;
      default:
        return Icons.device_unknown;
    }
  }

  String _displayAction(String action) {
    switch (action) {
      case 'Turn on':
        return t('action_turn_on');
      case 'Turn off':
        return t('action_turn_off');
      case 'Increase volume':
        return t('action_increase_volume');
      case 'Decrease volume':
        return t('action_decrease_volume');
      case 'Open Spotify':
        return t('action_open_spotify');
      case 'Open YouTube':
        return t('action_open_youtube');
      case 'Close Window':
        return t('action_close_window');
      case 'Open Browser':
        return t('action_open_browser');
      default:
        return action;
    }
  }

  String _displayGesture(String gesture) {
    switch (gesture) {
      case 'Index+Thumb':
        return t('gesture_index_thumb');
      case 'Middle+Thumb':
        return t('gesture_middle_thumb');
      case 'Open Palm':
        return t('gesture_open_palm');
      case 'Fist':
        return t('gesture_fist');
      default:
        return gesture;
    }
  }

  String _displayHand(String hand) {
    switch (hand) {
      case 'Left Hand':
        return t('hand_left');
      case 'Right Hand':
        return t('hand_right');
      case 'Both Hands':
        return t('hand_both');
      default:
        return hand;
    }
  }

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<String>(
      valueListenable: appLocale,
      builder: (context, _, __) {
        return SingleChildScrollView(
          child: Padding(
            padding: const EdgeInsets.all(16.0),
            child: Container(
              width: double.infinity,
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(12),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Action Selector
                  Text(
                    t('selector_action_label'),
                    style: const TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 12),
                  Container(
                    decoration: BoxDecoration(
                      color: const Color(0xFFDCE3EC),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: DropdownButton<String>(
                      value: selectedAction,
                      isExpanded: true,
                      iconSize: 40,
                      underline: const SizedBox(),
                      padding: const EdgeInsets.symmetric(
                        horizontal: 12,
                        vertical: 12,
                      ),
                      items: actions.map((action) {
                        return DropdownMenuItem(
                          value: action,
                          child: Row(
                            children: [
                              Icon(
                                _deviceIcon(widget.deviceType),
                                size: 30,
                              ),
                              const SizedBox(width: 8),
                              Text(
                                '${widget.deviceType}: ${_displayAction(action)}',
                              ),
                            ],
                          ),
                        );
                      }).toList(),
                      onChanged: (value) {
                        if (value != null) {
                          setState(() {
                            selectedAction = value;
                          });
                          _notifySelectionChanged();
                        }
                      },
                    ),
                  ),
                  const SizedBox(height: 32),

                  // Gesture Selector
                  Text(
                    t('selector_gesture_label'),
                    style: const TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 12),
                  Container(
                    decoration: BoxDecoration(
                      color: const Color(0xFFDCE3EC),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: DropdownButton<String>(
                      value: selectedGesture,
                      isExpanded: true,
                      iconSize: 40,
                      underline: const SizedBox(),
                      padding: const EdgeInsets.symmetric(
                        horizontal: 12,
                        vertical: 12,
                      ),
                      items: gestures.map((gesture) {
                        return DropdownMenuItem(
                          value: gesture,
                          child: Row(
                            children: [
                              const Icon(Icons.pan_tool, size: 30),
                              const SizedBox(width: 8),
                              Text(_displayGesture(gesture)),
                            ],
                          ),
                        );
                      }).toList(),
                      onChanged: (value) {
                        if (value != null) {
                          setState(() {
                            selectedGesture = value;
                          });
                          _notifySelectionChanged();
                        }
                      },
                    ),
                  ),
                  const SizedBox(height: 32),

                  // Hand Target
                  Text(
                    t('selector_hand_label'),
                    style: const TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 12),
                  Container(
                    padding: const EdgeInsets.all(4),
                    decoration: BoxDecoration(
                      color: const Color(0xFFDCE3EC),
                      borderRadius: BorderRadius.circular(999),
                    ),
                    child: Row(
                      children: hands
                          .map(
                            (hand) => Expanded(
                              child: GestureDetector(
                                onTap: () {
                                  setState(() {
                                    selectedHand = hand;
                                  });
                                  _notifySelectionChanged();
                                },
                                child: AnimatedContainer(
                                  duration: const Duration(milliseconds: 180),
                                  curve: Curves.easeOut,
                                  height: 38,
                                  alignment: Alignment.center,
                                  decoration: BoxDecoration(
                                    color: selectedHand == hand
                                        ? Colors.blue
                                        : Colors.transparent,
                                    borderRadius: BorderRadius.circular(999),
                                  ),
                                  child: Text(
                                    _displayHand(hand),
                                    textAlign: TextAlign.center,
                                    style: TextStyle(
                                      fontSize: 14,
                                      fontWeight: FontWeight.w500,
                                      color: selectedHand == hand
                                          ? Colors.white
                                          : Colors.black87,
                                    ),
                                  ),
                                ),
                              ),
                            ),
                          )
                          .toList(),
                    ),
                  ),
                  const SizedBox(height: 32),

                  // Save Action Button
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton(
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.blue,
                        foregroundColor: Colors.white,
                        padding: const EdgeInsets.symmetric(vertical: 16),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(8),
                        ),
                      ),
                      onPressed: () {
                        widget.onSave?.call();
                      },
                      child: Text(
                        t('selector_save'),
                        style: const TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        );
      },
    );
  }
}
