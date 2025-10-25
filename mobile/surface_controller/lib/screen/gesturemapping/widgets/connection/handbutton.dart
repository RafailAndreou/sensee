import 'package:flutter/material.dart';
import 'package:surface_controller/globals/sizes.dart';

class HandButton extends StatelessWidget {
  final String label;
  final VoidCallback onPressed;
  final Color backgroundColor;

  const HandButton({
    super.key,
    required this.label,
    required this.onPressed,
    this.backgroundColor = const Color.fromARGB(255, 255, 255, 255),
  });

  @override
  Widget build(BuildContext context) {
    return TextButton(
      style: TextButton.styleFrom(
        backgroundColor: backgroundColor,
        // Set fixed size (width x height)
        fixedSize: Size(
          getProportionalWidth(context, 50),
          getProportionalHeight(context, 20),
        ),
        padding: EdgeInsets.zero,
        minimumSize: Size.zero,
        side: const BorderSide(
          color: Color.fromARGB(112, 127, 74, 74),
          width: 3,
        ),

        // Remove default padding to allow smaller heights

        // Remove minimum size constraint

        // Set border radius
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(10), // Change this value
        ),
      ),
      onPressed: onPressed,
      child: Text(
        label,
        style: const TextStyle(color: Colors.black, fontSize: 12),
      ),
    );
  }
}
