import 'package:flutter/material.dart';
import 'package:surface_controller/redesign/globals/sizes.dart';

class DeviceTypeButton extends StatelessWidget {
  const DeviceTypeButton({super.key, required this.devicetype});

  final String devicetype;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      child: Container(
        width: getProportionalWidth(context, 110),
        height: getProportionalHeight(context, 90),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(8),
          border: Border.all(color: Colors.black, width: 1),
        ),
        child: Padding(
          padding: EdgeInsets.only(left: 8),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              SizedBox(height: 10),
              if (devicetype == 'Tv')
                Icon(Icons.tv)
              else if (devicetype == 'Ac')
                Icon(Icons.ac_unit)
              else if (devicetype == 'Light')
                Icon(Icons.light_mode)
              else if (devicetype == 'Fan')
                Icon(Icons.air),

              SizedBox(height: 25),
              Text(
                devicetype,
                style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
