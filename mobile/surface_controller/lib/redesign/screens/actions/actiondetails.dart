import 'package:flutter/material.dart';
import 'widgets/actionselectorcard.dart';

class ActionDetails extends StatelessWidget {
  final String deviceType;
  final String brand;

  const ActionDetails({
    super.key,
    required this.deviceType,
    required this.brand,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => Navigator.of(context).pop(),
        ),
        title: Text(
          '$brand - Action Details',
          style: const TextStyle(fontWeight: FontWeight.w900),
        ),
      ),
      body: ActionSelectorCard(deviceType: deviceType, brand: brand),
    );
  }
}
