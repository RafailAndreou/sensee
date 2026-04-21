import 'package:flutter/material.dart';
import 'package:surface_controller/globals/sizes.dart';

class DashboardCard extends StatelessWidget {
  const DashboardCard({
    super.key,
    required this.brandName,
    required this.deviceType,
    required this.actionName,
    required this.gestureName,
    required this.isSynced,
    this.onTap,
    this.onMoreTap,
  });

  final String brandName;
  final String deviceType;
  final String actionName;
  final String gestureName;
  final ValueNotifier<bool> isSynced;
  final VoidCallback? onTap;
  final VoidCallback? onMoreTap;

  @override
  Widget build(BuildContext context) {
    final displayName = brandName.isEmpty ? deviceType : brandName;

    return GestureDetector(
      behavior: HitTestBehavior.opaque,
      onTap: onTap,
      child: ClipRRect(
        borderRadius: BorderRadius.circular(20),
        child: Container(
          height: getProportionalHeight(context, 166),
          width: getProportionalHeight(context, 155),
          decoration: BoxDecoration(
            color: const Color.fromARGB(255, 255, 255, 255),
            borderRadius: BorderRadius.circular(20),
            boxShadow: [
              BoxShadow(
                color: const Color.fromARGB(100, 0, 0, 0),
                spreadRadius: 1,
                blurRadius: 5,
                offset: const Offset(2, 2),
              ),
            ],
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Padding(
                padding: const EdgeInsets.fromLTRB(16, 16, 16, 0),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Container(
                      width: 36,
                      height: 36,
                      decoration: BoxDecoration(
                        color: _deviceColor(deviceType).withValues(alpha: 0.12),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Icon(
                        _deviceIcon(deviceType),
                        size: 22,
                        color: _deviceColor(deviceType),
                      ),
                    ),
                    ValueListenableBuilder<bool>(
                      valueListenable: isSynced,
                      builder: (context, synced, _) {
                        return Container(
                          width: 10,
                          height: 10,
                          decoration: BoxDecoration(
                            shape: BoxShape.circle,
                            color: synced
                                ? Colors.greenAccent
                                : Colors.redAccent,
                            boxShadow: [
                              BoxShadow(
                                color: synced
                                    ? Colors.greenAccent.withValues(alpha: 0.5)
                                    : Colors.redAccent.withValues(alpha: 0.5),
                                blurRadius: 4,
                                spreadRadius: 1,
                              ),
                            ],
                          ),
                        );
                      },
                    ),
                    GestureDetector(
                      behavior: HitTestBehavior.opaque,
                      onTap: onMoreTap,
                      child: const SizedBox(
                        width: 33,
                        height: 28,
                        child: Image(
                          image: AssetImage('assets/redesign/more.png'),
                          width: 33,
                          height: 28,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 8),
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16),
                child: Text(
                  displayName,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  textAlign: TextAlign.left,
                  style: const TextStyle(fontWeight: FontWeight.w900),
                ),
              ),
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16),
                child: Text(
                  '$deviceType $actionName',
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                  textAlign: TextAlign.left,
                  style: const TextStyle(fontWeight: FontWeight.w500),
                ),
              ),
              const Spacer(),
              Padding(
                padding: const EdgeInsets.fromLTRB(12, 0, 12, 12),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    const Image(
                      image: AssetImage('assets/redesign/hand.png'),
                      width: 44,
                      height: 44,
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Text(
                        gestureName,
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                        textAlign: TextAlign.left,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
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
      case 'pc':
        return Icons.computer;
      default:
        return Icons.device_unknown;
    }
  }

  Color _deviceColor(String type) {
    switch (type.toLowerCase()) {
      case 'tv':
        return const Color(0xFF2F80ED);
      case 'ac':
        return const Color(0xFF38A169);
      case 'light':
        return const Color(0xFFF2C94C);
      case 'fan':
        return const Color(0xFF9B51E0);
      case 'pc':
        return const Color(0xFF4A5568);
      default:
        return Colors.black54;
    }
  }
}
