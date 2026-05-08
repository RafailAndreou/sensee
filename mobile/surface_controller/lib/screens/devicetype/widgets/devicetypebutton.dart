import 'package:flutter/material.dart';
import 'package:surface_controller/globals/locale.dart';
import 'package:surface_controller/globals/sizes.dart';

class DeviceTypeButton extends StatelessWidget {
  const DeviceTypeButton({super.key, required this.devicetype});

  final String devicetype;

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<String>(
      valueListenable: appLocale,
      builder: (context, _, __) {
        final isDark = Theme.of(context).brightness == Brightness.dark;
        return Material(
          color: Theme.of(context).cardColor,
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
                border: Border.all(
                  color: isDark
                      ? const Color(0xFF4B5563)
                      : const Color(0xFFB7C0CF),
                  width: 1,
                ),
              ),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                crossAxisAlignment: CrossAxisAlignment.center,
                children: [
                  Icon(_deviceIcon(), size: 28),
                  const SizedBox(height: 8),
                  Text(
                    _displayName(),
                    textAlign: TextAlign.center,
                    style: const TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.w800,
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

  IconData _deviceIcon() {
    if (devicetype == 'Tv') return Icons.tv;
    if (devicetype == 'Ac') return Icons.ac_unit;
    if (devicetype == 'Light') return Icons.light_mode;
    if (devicetype == 'Fan') return Icons.air;
    if (devicetype == 'PC') return Icons.computer;
    return Icons.device_unknown;
  }

  String _displayName() {
    switch (devicetype.toLowerCase()) {
      case 'tv':
        return t('device_tv');
      case 'ac':
        return t('device_ac');
      case 'light':
        return t('device_light');
      case 'fan':
        return t('device_fan');
      case 'pc':
        return t('device_pc');
      default:
        return devicetype;
    }
  }
}
