import 'package:flutter/material.dart';
import 'package:surface_controller/globals/sizes.dart';

class DeviceTypeButton extends StatelessWidget {
  const DeviceTypeButton({super.key, required this.devicetype});

  final String devicetype;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.white,
      elevation: 3,
      shadowColor: Colors.black26,
      borderRadius: BorderRadius.circular(16),
      child: InkWell(
        borderRadius: BorderRadius.circular(16),
        child: Container(
          width: getProportionalWidth(context, 92),
          height: getProportionalHeight(context, 88),
          padding: const EdgeInsets.all(10),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: const Color(0xFFB7C0CF), width: 1),
          ),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              Icon(_deviceIcon(), size: 28, color: Colors.black87),
              const SizedBox(height: 8),
              Text(
                devicetype,
                textAlign: TextAlign.center,
                style: const TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.w800,
                  color: Colors.black87,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  IconData _deviceIcon() {
    if (devicetype == 'Tv') return Icons.tv;
    if (devicetype == 'Ac') return Icons.ac_unit;
    if (devicetype == 'Light') return Icons.light_mode;
    if (devicetype == 'Fan') return Icons.air;
    return Icons.device_unknown;
  }
}
