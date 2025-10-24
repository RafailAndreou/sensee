import 'package:flutter/material.dart';
import 'package:surface_controller/globals/connectionslist.dart';
import 'package:surface_controller/globals/sizes.dart';

class RemoveButton extends StatelessWidget {
  final VoidCallback onPressed;

  const RemoveButton({super.key, required this.onPressed});

  @override
  Widget build(BuildContext context) {
    return TextButton(
      child: const Text(
        'Remove',
        style: TextStyle(fontSize: 11, color: Colors.white),
      ),
      onPressed: onPressed,
      style: TextButton.styleFrom(
        backgroundColor: Colors.red,
        fixedSize: Size(
          getProportionalWidth(context, 70),
          getProportionalHeight(context, 20),
        ),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(9),
          side: const BorderSide(
            color: Color(0xFFB0BEC5), // Border color
            width: 2, // Border thickness
          ),
        ),
      ),
    );
  }
}
