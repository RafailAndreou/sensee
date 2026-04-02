import 'package:flutter/material.dart';

class DeviceType extends StatefulWidget {
  const DeviceType({super.key, required this.gestureName});

  final String gestureName;

  @override
  State<DeviceType> createState() => _DeviceTypeState();
}

class _DeviceTypeState extends State<DeviceType> {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: Row(
          children: [
            Image.asset('assets/redesign/gesture.png'),
            Text(widget.gestureName),
          ],
        ),
      ),
    );
  }
}
