import 'package:flutter/material.dart';
import 'package:surface_controller/redesign/globals/connectionslist.dart';
import 'package:surface_controller/redesign/globals/global.dart';
import 'widgets/actionselectorcard.dart';
import 'widgets/actionbutton.dart';
import 'widgets/gesturebutton.dart';

class ActionDetails extends StatefulWidget {
  final String deviceType;
  final String brand;

  const ActionDetails({
    super.key,
    required this.deviceType,
    required this.brand,
  });

  @override
  State<ActionDetails> createState() => _ActionDetailsState();
}

class _ActionDetailsState extends State<ActionDetails> {
  String _selectedAction = 'Turn on';
  String _selectedGesture = 'Index+Thumb';
  String _selectedHand = 'Right Hand';

  Future<void> _saveConfiguration() async {
    addNewConnection();
    final int newId = connectionsList.value.last;
    final config = getConnectionConfig(newId);

    config.id.value = newId;
    config.brand.value = widget.brand;
    config.action.value = _selectedAction;
    config.gesture.value = _selectedGesture;
    config.hand.value = _selectedHand;
    config.sound.value = widget.deviceType;

    saveConfigsToFile();

    if (!mounted) return;
    Navigator.of(context).popUntil((route) => route.isFirst);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFEAEDF4),
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => Navigator.of(context).pop(),
        ),
        title: Text(
          '${widget.brand} - Action Details',
          style: const TextStyle(fontWeight: FontWeight.w900),
        ),
      ),
      body: SafeArea(
        child: Column(
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 16, 16, 0),
              child: Row(
                children: [
                  Expanded(
                    child: Actionbutton(
                      deviceType: widget.deviceType,
                      actionName: _selectedAction,
                    ),
                  ),
                  const SizedBox(width: 16),
                  Expanded(child: Gesturebutton(gestureName: _selectedGesture)),
                ],
              ),
            ),
            const Spacer(),
            ActionSelectorCard(
              deviceType: widget.deviceType,
              brand: widget.brand,
              initialAction: _selectedAction,
              initialGesture: _selectedGesture,
              initialHand: _selectedHand,
              onSelectionChanged:
                  ({required action, required gesture, required hand}) {
                    setState(() {
                      _selectedAction = action;
                      _selectedGesture = gesture;
                      _selectedHand = hand;
                    });
                  },
              onSave: _saveConfiguration,
            ),
          ],
        ),
      ),
    );
  }
}
