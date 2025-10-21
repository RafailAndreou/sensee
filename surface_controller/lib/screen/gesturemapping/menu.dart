import 'package:flutter/material.dart';
import 'buttons.dart';

class Menu extends StatelessWidget {
  const Menu({super.key});

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Flexible(
          flex: 9,
          child: CustomButton(
            title: "Gesture mapping",
            icon: Image.asset(
              'assets/gesturemapping.png',
              width: 15,
              height: 15,
            ),
          ),
        ),
        Spacer(flex: 1),
        Flexible(
          flex: 9,
          child: CustomButton(
            title: "Surface Zones",
            icon: Image.asset('assets/surfacezone.png', width: 20, height: 20),
          ),
        ),
        Spacer(),
        Flexible(
          flex: 9,
          child: CustomButton(
            title: "Device Actions",
            icon: Image.asset('assets/deviceaction.png', width: 20, height: 20),
          ),
        ),
      ],
    );
  }
}
