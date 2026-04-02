import 'package:flutter/material.dart';

class Actionbutton extends StatefulWidget {
  const Actionbutton({
    super.key,
    required this.deviceType,
    required this.actionName,
  });

  final String deviceType;
  final String actionName;

  @override
  State<Actionbutton> createState() => _ActionbuttonState();
}

class _ActionbuttonState extends State<Actionbutton> {
  @override
  Widget build(BuildContext context) {
    return Container(
      child: Row(
        children: [
          if (widget.deviceType == 'Tv')
            Icon(Icons.tv)
          else if (widget.deviceType == 'Ac')
            Icon(Icons.ac_unit)
          else if (widget.deviceType == 'Light')
            Icon(Icons.light_mode)
          else if (widget.deviceType == 'Fan')
            Icon(Icons.air),
          Text(
            widget.deviceType + ": " + widget.actionName,
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.w500),
          ),
          SizedBox(width: 20),
        ],
      ),
    );
  }
}
