import 'package:flutter/material.dart';
import '../../../../globals/sizes.dart';

class ConfigureButton extends StatelessWidget {
  final String label;
  final VoidCallback onPressed;
  final Color backgroundColor = const Color(0xFFDDF0F7);

  const ConfigureButton({
    super.key,
    required this.label,
    required this.onPressed,
  });

  @override
  Widget build(BuildContext context) {
    return TextButton(
      style: TextButton.styleFrom(
        backgroundColor: backgroundColor,
        // Set dynamic size based on screen dimensions
        fixedSize: Size(
          getProportionalWidth(context, 100),
          getProportionalHeight(context, 40),
        ),

        // Set border radius and stroke
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(9),
          side: const BorderSide(
            color: Color(0xFFB0BEC5), // Border color
            width: 2, // Border thickness
          ),
        ),
      ),
      onPressed: onPressed,
      child: Text(label),
    );
  }
}
