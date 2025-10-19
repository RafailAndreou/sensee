import 'package:flutter/material.dart';

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
        // Set fixed size (width x height)
        fixedSize: const Size(100, 40),

        // Set border radius
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(9), // Change this value
        ),
      ),
      onPressed: onPressed,
      child: Text(label),
    );
  }
}
