import 'package:flutter/material.dart';
import 'package:surface_controller/globals/sizes.dart';

class DashboardCard extends StatelessWidget {
  const DashboardCard({
    super.key,
    required this.brandName,
    required this.deviceType,
    required this.actionName,
    required this.gestureName,
    this.onTap,
    this.onMoreTap,
  });

  final String brandName;
  final String deviceType;
  final String actionName;
  final String gestureName;
  final VoidCallback? onTap;
  final VoidCallback? onMoreTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      behavior: HitTestBehavior.opaque,
      onTap: onTap,
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
                  Image(
                    image: const AssetImage("assets/redesign/AC_icon.png"),
                    width: 30,
                    height: 38,
                  ),
                  GestureDetector(
                    behavior: HitTestBehavior.opaque,
                    onTap: onMoreTap,
                    child: const SizedBox(
                      width: 33,
                      height: 28,
                      child: Image(
                        image: AssetImage("assets/redesign/more.png"),
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
                brandName,
                textAlign: TextAlign.left,
                style: const TextStyle(fontWeight: FontWeight.w900),
              ),
            ),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: Text(
                '$deviceType $actionName',
                textAlign: TextAlign.left,
                style: const TextStyle(fontWeight: FontWeight.w500),
              ),
            ),
            Row(
              children: [
                Image(
                  image: const AssetImage("assets/redesign/hand.png"),
                  width: 50,
                  height: 50,
                ),
                const SizedBox(width: 35),
                Expanded(
                  child: Text(
                    gestureName,
                    softWrap: true,
                    maxLines: 2,
                    overflow: TextOverflow.visible,
                    textAlign: TextAlign.left,
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
