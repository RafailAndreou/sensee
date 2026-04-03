import 'package:flutter/material.dart';
import 'widgets/devicetypebutton.dart';
import '../brandselection/brandselection.dart';

class DeviceType extends StatelessWidget {
  const DeviceType({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFEAEDF4),
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
        padding: const EdgeInsets.fromLTRB(18, 18, 18, 18),
        crossAxisCount: 2,
        crossAxisSpacing: 10,
        mainAxisSpacing: 10,
        childAspectRatio: 1.08,
        children: [
          GestureDetector(
            onTap: () {
              Navigator.of(context).push(
                MaterialPageRoute(
                  builder: (_) => const BrandSelection(deviceType: 'Tv'),
                ),
              );
            },
            child: const DeviceTypeButton(devicetype: 'Tv'),
          ),
          GestureDetector(
            onTap: () {
              Navigator.of(context).push(
                MaterialPageRoute(
                  builder: (_) => const BrandSelection(deviceType: 'Ac'),
                ),
              );
            },
            child: const DeviceTypeButton(devicetype: 'Ac'),
          ),
          GestureDetector(
            onTap: () {
              Navigator.of(context).push(
                MaterialPageRoute(
                  builder: (_) => const BrandSelection(deviceType: 'Light'),
                ),
              );
            },
            child: const DeviceTypeButton(devicetype: 'Light'),
          ),
          GestureDetector(
            onTap: () {
              Navigator.of(context).push(
                MaterialPageRoute(
                  builder: (_) => const BrandSelection(deviceType: 'Fan'),
                ),
              );
            },
            child: const DeviceTypeButton(devicetype: 'Fan'),
          ),
        ],
      ),
    );
  }
}
