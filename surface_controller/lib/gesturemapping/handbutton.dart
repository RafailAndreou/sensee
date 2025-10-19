import 'package:flutter/material.dart';

class HandButton extends StatelessWidget {
  final String label;
  final VoidCallback onPressed;
  final Color backgroundColor;

  const HandButton({
    super.key,
    required this.label,
    required this.onPressed,
    this.backgroundColor = Colors.grey,
  });

  @override
  Widget build(BuildContext context) {
    return TextButton(
      style: TextButton.styleFrom(
        backgroundColor: backgroundColor,
        // Set fixed size (width x height)
        fixedSize: const Size(80, 30),

        // Remove default padding to allow smaller heights
        padding: EdgeInsets.zero,

        // Remove minimum size constraint
        minimumSize: Size.zero,

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
