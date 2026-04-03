import 'package:flutter/material.dart';
import 'package:surface_controller/globals/sizes.dart';

class DeviceTypeButton extends StatelessWidget {
  const DeviceTypeButton({super.key, required this.devicetype});

  final String devicetype;

  @override
  Widget build(BuildContext context) {
    final Color accentColor = _deviceColor();

    return Container(
      width: getProportionalWidth(context, 96),
      height: getProportionalHeight(context, 106),
      decoration: BoxDecoration(
        color: const Color(0xFFFDFDFD),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFF64748B), width: 1.1),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.14),
            blurRadius: 16,
            offset: const Offset(0, 5),
          ),
        ],
      ),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              width: 44,
              height: 44,
              decoration: BoxDecoration(
                color: accentColor.withValues(alpha: 0.18),
                borderRadius: BorderRadius.circular(14),
              ),
              child: Icon(_deviceIcon(), size: 24, color: accentColor),
            ),
            const SizedBox(height: 10),
            Text(
              devicetype,
              textAlign: TextAlign.center,
              style: const TextStyle(
                fontSize: 15,
                fontWeight: FontWeight.w700,
                color: Colors.black87,
              ),
            ),
          ],
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

  Color _deviceColor() {
    if (devicetype == 'Tv') return const Color(0xFF2F80ED);
    if (devicetype == 'Ac') return const Color(0xFF38A169);
    if (devicetype == 'Light') return const Color(0xFFF2C94C);
    if (devicetype == 'Fan') return const Color(0xFF9B51E0);
    return Colors.black54;
  }
}
