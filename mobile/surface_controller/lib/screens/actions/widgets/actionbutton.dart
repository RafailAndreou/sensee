import 'package:flutter/material.dart';

class Actionbutton extends StatelessWidget {
  const Actionbutton({
    super.key,
    required this.deviceType,
    required this.actionName,
  });

  final String deviceType;
  final String actionName;

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 140,
      decoration: BoxDecoration(
        color: Theme.of(context).cardColor,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.15),
            blurRadius: 6,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            _deviceIcon(deviceType),
            const SizedBox(height: 10),
            Text(
              '${deviceType.toUpperCase()}:$actionName',
              textAlign: TextAlign.center,
              style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w500),
            ),
          ],
        ),
      ),
    );
  }

  Widget _deviceIcon(String type) {
    if (type == 'Tv') return const Icon(Icons.tv);
    if (type == 'Ac') return const Icon(Icons.ac_unit);
    if (type == 'Light') return const Icon(Icons.light_mode);
    if (type == 'Fan') return const Icon(Icons.air);
    if (type == 'PC') return const Icon(Icons.computer);
    return const Icon(Icons.device_unknown);
  }
}
