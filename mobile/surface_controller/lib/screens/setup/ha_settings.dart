import 'package:flutter/material.dart';

class HASettings extends StatelessWidget {
  const HASettings({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFEAEDF4),
      appBar: AppBar(title: const Text("Settings")),
      body: const Center(
        child: Text(
          "Settings Screen - Placeholder",
          style: TextStyle(fontSize: 18),
        ),
      ),
    );
  }
}
