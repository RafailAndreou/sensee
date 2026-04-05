import 'package:flutter/material.dart';

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
  late String selectedAction;
  late String selectedGesture;
  late String selectedHand;

  final List<String> actions = [
    'Turn on',
    'Turn off',
    'Increase volume',
    'Decrease volume',
  ];
  final List<String> gestures = [
    'Index+Thumb',
    'Middle+Thumb',
    'Open Palm',
    'OK',
    'Point',
    'Fist',
  ];
  final List<String> hands = ['Left Hand', 'Right Hand', 'Both Hands'];

  @override
  void initState() {
    super.initState();
    selectedAction = widget.initialAction;
    selectedGesture = widget.initialGesture;
    selectedHand = widget.initialHand;
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
      default:
        return Icons.device_unknown;
    }
  }

  @override
  Widget build(BuildContext context) {
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
              const Text(
                'Action Selector',
                style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
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
                          Icon(_deviceIcon(widget.deviceType), size: 30),
                          const SizedBox(width: 8),
                          Text('${widget.deviceType}: $action'),
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
              const Text(
                'Gesture Selector',
                style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
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
                          Text(gesture),
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
              const Text(
                'Hand Target',
                style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
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
                                hand,
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
                  child: const Text(
                    'Save Action',
                    style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
