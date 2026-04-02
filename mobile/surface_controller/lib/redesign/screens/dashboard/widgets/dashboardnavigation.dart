import 'package:flutter/material.dart';

class DashBoardNavigation extends StatelessWidget {
  const DashBoardNavigation({super.key});

  @override
  Widget build(BuildContext context) {
    return Container(
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceAround,
        children: [
          GestureDetector(
            onTap: () {
              // Handle dashboard tap
            },
            child: Column(
              children: [
                Image(
                  image: AssetImage("assets/redesign/dashboard-active.png"),
                ),
                const Text(
                  "Dashboard",
                  style: TextStyle(fontWeight: FontWeight.w900),
                ),
              ],
            ),
          ),
          GestureDetector(
            onTap: () {
              // Handle camera tap
            },
            child: Column(
              children: [
                Image(image: AssetImage("assets/redesign/Camera.png")),
                const Text(
                  "Camera",
                  style: TextStyle(fontWeight: FontWeight.w900),
                ),
              ],
            ),
          ),
          GestureDetector(
            onTap: () {
              // Handle settings tap
            },
            child: Column(
              children: [
                Image(image: AssetImage("assets/redesign/settings.png")),
                const Text("Settings"),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
