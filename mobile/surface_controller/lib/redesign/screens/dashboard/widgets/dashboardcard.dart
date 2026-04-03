import 'package:flutter/material.dart';
import 'package:surface_controller/redesign/globals/sizes.dart';

class DashboardCard extends StatelessWidget {
  const DashboardCard({
    super.key,
    this.brandName = 'Philips',
    this.deviceType = 'Tv',
    this.actionName = 'Turn on',
    this.gestureName = 'Thumb and index',
  });

  final String brandName;
  final String deviceType;
  final String actionName;
  final String gestureName;

  @override
  Widget build(BuildContext context) {
    return Container(
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
            offset: const Offset(2, 2), // changes position of shadow
          ),
        ],
      ),
      child: GestureDetector(
        onTap: () {
          // Handle dashboard card tap
          print("Dashboard card tapped");
        },
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 16, 16, 0),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Image(
                    image: AssetImage("assets/redesign/AC_icon.png"),
                    width: 30,
                    height: 38,
                  ),
                  GestureDetector(
                    onTap: () {
                      print("More tapped");
                      // Handle more tap
                    },
                    child: Image(
                      image: AssetImage("assets/redesign/more.png"),
                      width: 33,
                      height: 28,
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
              padding: EdgeInsets.symmetric(horizontal: 16),
              child: Text(
                '$deviceType $actionName',
                textAlign: TextAlign.left,
                style: const TextStyle(fontWeight: FontWeight.w500),
              ),
            ),
            Row(
              children: [
                Image(
                  image: AssetImage("assets/redesign/hand.png"),
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
