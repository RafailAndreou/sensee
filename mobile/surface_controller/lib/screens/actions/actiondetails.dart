import 'package:flutter/material.dart';
import 'dart:async';
import 'package:surface_controller/globals/connectionslist.dart';
import 'package:surface_controller/globals/global.dart';
import 'package:surface_controller/globals/locale.dart';
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
  late String _selectedAction;
  String _selectedGesture = 'Index+Thumb';
  String _selectedHand = 'Right Hand';

  String _defaultActionForDeviceType(String deviceType) {
    if (deviceType.toLowerCase() == 'pc') {
      return 'Open Spotify';
    }
    return 'Turn on';
  }

  String _normalizeSelectionValue(String value) {
    return value.trim().toLowerCase();
  }

  String _normalizeHandValue(String value) {
    final normalized = _normalizeSelectionValue(value);
    if (normalized.contains('both')) return 'both hands';
    if (normalized.contains('left')) return 'left hand';
    if (normalized.contains('right')) return 'right hand';
    return normalized;
  }

  Set<String> _existingHandsForGesture({required int? excludeConnectionId}) {
    final targetGesture = _normalizeSelectionValue(_selectedGesture);
    final hands = <String>{};

    for (final entry in connectionConfigs.entries) {
      final connectionId = entry.key;
      if (excludeConnectionId != null && connectionId == excludeConnectionId) {
        continue;
      }

      final config = entry.value;
      final configGesture = _normalizeSelectionValue(config.gesture.value);
      if (configGesture != targetGesture) {
        continue;
      }

      hands.add(_normalizeHandValue(config.hand.value));
    }

    return hands;
  }

  bool _hasDuplicateGestureHandMapping({required int? excludeConnectionId}) {
    final targetGesture = _normalizeSelectionValue(_selectedGesture);
    final targetHand = _normalizeSelectionValue(_selectedHand);

    for (final entry in connectionConfigs.entries) {
      final connectionId = entry.key;
      if (excludeConnectionId != null && connectionId == excludeConnectionId) {
        continue;
      }

      final config = entry.value;
      final configGesture = _normalizeSelectionValue(config.gesture.value);
      final configHand = _normalizeSelectionValue(config.hand.value);

      if (configGesture == targetGesture && configHand == targetHand) {
        return true;
      }
    }

    return false;
  }

  @override
  void initState() {
    super.initState();
    _selectedAction = _defaultActionForDeviceType(widget.deviceType);

    if (widget.editingConnectionId != null) {
      final config = getConnectionConfig(widget.editingConnectionId!);
      _selectedAction = config.action.value.isEmpty
          ? _defaultActionForDeviceType(widget.deviceType)
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
    final existingConnectionId = widget.editingConnectionId;
    final selectedHandNormalized = _normalizeHandValue(_selectedHand);
    final existingHands = _existingHandsForGesture(
      excludeConnectionId: existingConnectionId,
    );

    if (selectedHandNormalized == 'both hands') {
      if (existingHands.contains('both hands')) {
        if (!mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(t('err_both_hands_assigned'))),
        );
        return;
      }

      final hasLeft = existingHands.contains('left hand');
      final hasRight = existingHands.contains('right hand');
      if (hasLeft && !hasRight) {
        _selectedHand = 'Right Hand';
        if (!mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(t('err_both_conflicts_left'))),
        );
      } else if (hasRight && !hasLeft) {
        _selectedHand = 'Left Hand';
        if (!mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(t('err_both_conflicts_right'))),
        );
      } else if (hasLeft && hasRight) {
        if (!mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(t('err_both_left_right_used'))),
        );
        return;
      }
    } else {
      if (existingHands.contains('both hands')) {
        if (!mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(t('err_gesture_assigned_both'))),
        );
        return;
      }
    }

    if (_hasDuplicateGestureHandMapping(
      excludeConnectionId: existingConnectionId,
    )) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(t('err_duplicate_gesture_hand'))),
      );
      return;
    }

    final int connectionId;
    if (existingConnectionId != null) {
      connectionId = existingConnectionId;
      final existing = getConnectionConfig(connectionId);
      if (widget.connectionType.isNotEmpty) {
        existing.connectionType.value = widget.connectionType;
      }
      if (widget.entityId.isNotEmpty) {
        existing.entityId.value = widget.entityId;
      }
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
