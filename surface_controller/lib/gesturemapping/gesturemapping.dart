import 'package:flutter/material.dart';
import 'buttons.dart';
import 'connection.dart';
import 'addactionbutton.dart';

class Gesturemapping extends StatelessWidget {
  const Gesturemapping({super.key});

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        const SizedBox(height: 20),
        Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            CustomButton(
              title: "Gesture mapping",
              icon: Image.asset(
                'assets/gesturemapping.png',
                width: 15,
                height: 15,
              ),
            ),
            const SizedBox(width: 8),
            CustomButton(
              title: "Surface Zones",
              icon: Image.asset(
                'assets/surfacezone.png',
                width: 20,
                height: 20,
              ),
            ),
            const SizedBox(width: 8),
            CustomButton(
              title: "Device Actions",
              icon: Image.asset(
                'assets/deviceaction.png',
                width: 20,
                height: 20,
              ),
            ),
          ],
        ),
        const SizedBox(height: 50),
        // keep the connection widget at its intended height
        const SizedBox(child: Connection()),
        const SizedBox(height: 50),
        AddActionButton(title: "Add item"),
        CustomButton(
          title: "Test",
          icon: Image.asset("assets/deviceaction.png"),
        ),
      ],
    );
  }
}
