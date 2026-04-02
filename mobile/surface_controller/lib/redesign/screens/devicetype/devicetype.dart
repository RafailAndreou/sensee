import 'package:flutter/material.dart';

class DeviceType extends StatelessWidget {
  const DeviceType({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => Navigator.of(context).pop(),
        ),
        title: const Text('Device Type'),
      ),
      body: const Center(child: Text('Device Type Screen')),
    );
  }
}
