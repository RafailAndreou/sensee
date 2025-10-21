import 'package:flutter/material.dart';

class HandButton extends StatefulWidget {
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
  State<HandButton> createState() => _HandButtonState();
}

class _HandButtonState extends State<HandButton> {
  @override
  Widget build(BuildContext context) {
    return TextButton(
      style: TextButton.styleFrom(
        backgroundColor: widget.backgroundColor,
        // Set fixed size (width x height)
        fixedSize: const Size(60, 20),
        padding: EdgeInsets.zero,
        minimumSize: Size.zero,

        // Remove default padding to allow smaller heights

        // Remove minimum size constraint

        // Set border radius
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(9), // Change this value
        ),
      ),
      onPressed: widget.onPressed,
      child: Text(
        widget.label,
        style: const TextStyle(color: Colors.black, fontSize: 12),
      ),
    );
  }
}
