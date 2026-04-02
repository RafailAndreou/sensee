import 'package:flutter/material.dart';

class ActionSelectorCard extends StatefulWidget {
  final String deviceType;
  final String brand;

  const ActionSelectorCard({
    super.key,
    required this.deviceType,
    required this.brand,
  });

  @override
  State<ActionSelectorCard> createState() => _ActionSelectorCardState();
}

class _ActionSelectorCardState extends State<ActionSelectorCard> {
  String selectedAction = 'Turn on';
  String selectedGesture = 'Index+Thumb';
  String selectedHand = 'Right Hand';

  final List<String> actions = [
    'Turn on',
    'Turn off',
    'Increase volume',
    'Decrease volume',
  ];
  final List<String> gestures = ['Index+Thumb', 'Peace', 'OK', 'Point', 'Fist'];
  final List<String> hands = ['Left Hand', 'Right Hand', 'Both Hands'];

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      child: Padding(
        padding: const EdgeInsets.all(16.0),
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
                color: Colors.grey[200],
                borderRadius: BorderRadius.circular(8),
              ),
              child: DropdownButton<String>(
                value: selectedAction,
                isExpanded: true,
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
                        Icon(Icons.tv, size: 20),
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
                color: Colors.grey[200],
                borderRadius: BorderRadius.circular(8),
              ),
              child: DropdownButton<String>(
                value: selectedGesture,
                isExpanded: true,
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
                        const Icon(Icons.pan_tool, size: 20),
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
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: hands
                  .map(
                    (hand) => Expanded(
                      child: GestureDetector(
                        onTap: () {
                          setState(() {
                            selectedHand = hand;
                          });
                        },
                        child: Padding(
                          padding: const EdgeInsets.symmetric(horizontal: 6),
                          child: ElevatedButton(
                            style: ElevatedButton.styleFrom(
                              backgroundColor: selectedHand == hand
                                  ? Colors.blue
                                  : Colors.grey[300],
                              foregroundColor: selectedHand == hand
                                  ? Colors.white
                                  : Colors.black,
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(8),
                              ),
                              padding: const EdgeInsets.symmetric(vertical: 12),
                            ),
                            onPressed: () {
                              setState(() {
                                selectedHand = hand;
                              });
                            },
                            child: Text(hand),
                          ),
                        ),
                      ),
                    ),
                  )
                  .toList(),
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
                  // TODO: Implement save action
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
    );
  }
}
