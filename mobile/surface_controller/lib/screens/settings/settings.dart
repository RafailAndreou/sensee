import 'package:flutter/material.dart';
import 'widgets/settingsbutton.dart';
import '../setup/ha_settings.dart';
import '../gestureSettings/gestureSettings.dart';

class Settings extends StatelessWidget {
  const Settings({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text(
          'Settings',
          style: TextStyle(fontWeight: FontWeight.w700),
        ),
      ),
      body: Container(
        width: double.infinity,
        height: double.infinity,
        color: const Color(0xFFEAEDF4),
        child: Column(
          children: [
            SizedBox(height: 24),
            Settingsbutton(
              image: Icon(Icons.dns, size: 32),
              title: 'Server Connection',
              description: 'Hass connection settings',
              onTap: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(builder: (context) => const HASettings()),
                );
              },
            ),
            SizedBox(height: 24),
            Settingsbutton(
              image: Icon(Icons.back_hand, size: 32),
              title: 'Gesture Settings',
              description: 'Manage device wake-up and gesture holds',
              onTap: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (context) => const Gesturesettings(),
                  ),
                );
              },
            ),
          ],
        ),
      ),
    );
  }
}
