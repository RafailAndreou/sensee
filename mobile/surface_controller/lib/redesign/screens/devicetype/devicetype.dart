import 'package:flutter/material.dart';
import 'devicetypebutton.dart';
import '../brandselection/brandselection.dart';

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
        title: const Text(
          ' Select Device Type',
          style: TextStyle(fontWeight: FontWeight.w900),
        ),
      ),
      body: GridView.count(
        padding: const EdgeInsets.all(12),
        crossAxisCount: 2,
        crossAxisSpacing: 20,
        mainAxisSpacing: 10,
        childAspectRatio: 1,
        children: [
          GestureDetector(
            onTap: () {
              Navigator.of(context).push(
                MaterialPageRoute(
                  builder: (_) => const BrandSelection(deviceType: 'Tv'),
                ),
              );
            },
            child: const Align(
              alignment: Alignment.topLeft,
              child: DeviceTypeButton(devicetype: 'Tv'),
            ),
          ),
          GestureDetector(
            onTap: () {
              Navigator.of(context).push(
                MaterialPageRoute(
                  builder: (_) => const BrandSelection(deviceType: 'Ac'),
                ),
              );
            },
            child: const Align(
              alignment: Alignment.topRight,
              child: DeviceTypeButton(devicetype: 'Ac'),
            ),
          ),
          GestureDetector(
            onTap: () {
              Navigator.of(context).push(
                MaterialPageRoute(
                  builder: (_) => const BrandSelection(deviceType: 'Light'),
                ),
              );
            },
            child: const Align(
              alignment: Alignment.topLeft,
              child: DeviceTypeButton(devicetype: 'Light'),
            ),
          ),
          GestureDetector(
            onTap: () {
              Navigator.of(context).push(
                MaterialPageRoute(
                  builder: (_) => const BrandSelection(deviceType: 'Fan'),
                ),
              );
            },
            child: const Align(
              alignment: Alignment.topRight,
              child: DeviceTypeButton(devicetype: 'Fan'),
            ),
          ),
        ],
      ),
    );
  }
}
