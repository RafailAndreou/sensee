import 'package:flutter/material.dart';
import 'dart:async';
import 'package:surface_controller/globals/connectionslist.dart';
import 'package:surface_controller/globals/global.dart';
import 'package:surface_controller/server/server.dart' as server_sync;
import 'package:surface_controller/screens/dashboard/widgets/dashboardnavigation.dart';
import 'widgets/actionselectorcard.dart';
import 'widgets/actionbutton.dart';
import 'widgets/gesturebutton.dart';

class ActionDetails extends StatefulWidget {
  final String deviceType;
  final String brand;
  final int? editingConnectionId;
  final String connectionType;
  final String entityId;

  const ActionDetails({
    super.key,
    required this.deviceType,
    required this.brand,
    this.editingConnectionId,
    this.connectionType = 'ir',
    this.entityId = '',
  });

  @override
  State<ActionDetails> createState() => _ActionDetailsState();
}

class _ActionDetailsState extends State<ActionDetails> {
  String _selectedAction = 'Turn on';
  String _selectedGesture = 'Index+Thumb';
  String _selectedHand = 'Right Hand';

  @override
  void initState() {
    super.initState();
    if (widget.editingConnectionId != null) {
      final config = getConnectionConfig(widget.editingConnectionId!);
      _selectedAction = config.action.value.isEmpty
          ? _selectedAction
          : config.action.value;
      _selectedGesture = config.gesture.value.isEmpty
          ? _selectedGesture
          : config.gesture.value;
      _selectedHand = config.hand.value.isEmpty
          ? _selectedHand
          : config.hand.value;
    }
  }

  Future<void> _saveConfiguration() async {
    final int connectionId;
    if (widget.editingConnectionId != null) {
      connectionId = widget.editingConnectionId!;
    } else {
      addNewConnection();
      connectionId = connectionsList.value.last;
      final config = getConnectionConfig(connectionId);
      config.connectionType.value = widget.connectionType;
      config.entityId.value = widget.entityId;
    }

    final config = getConnectionConfig(connectionId);

    config.id.value = connectionId;
    config.brand.value = widget.brand;
    config.action.value = _selectedAction;
    config.gesture.value = _selectedGesture;
    config.hand.value = _selectedHand;
    config.sound.value = widget.deviceType;

    // Ensure dashboard cards listening to id-list updates also repaint on edits.
    connectionsList.value = List.from(connectionsList.value);

    saveConfigsToFile();

    if (!mounted) return;
    Navigator.of(context).popUntil((route) => route.isFirst);

    unawaited(server_sync.sendAllConfigurations());
  }

  @override
  Widget build(BuildContext context) {
    final displayName = widget.brand.isEmpty ? widget.deviceType : widget.brand;

    return Scaffold(
      backgroundColor: const Color(0xFFEAEDF4),
      appBar: AppBar(
        automaticallyImplyLeading: false,
        title: Text(
          '$displayName - Action Details',
          style: const TextStyle(fontWeight: FontWeight.w900),
        ),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
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
                    Expanded(
                      child: Gesturebutton(gestureName: _selectedGesture),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 24),
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
              const SizedBox(height: 24),
            ],
          ),
        ),
      ),
      bottomNavigationBar: const SafeArea(
        top: false,
        child: Padding(
          padding: EdgeInsets.fromLTRB(0, 8, 0, 16),
          child: DashBoardNavigation(selectedTab: DashboardTab.settings),
        ),
      ),
    );
  }
}
