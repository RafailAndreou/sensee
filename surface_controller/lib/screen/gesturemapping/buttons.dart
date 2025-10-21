import 'package:flutter/material.dart';
import '../../irblaster.dart';

class CustomButton extends StatelessWidget {
  final String title;
  final Image icon;
  final VoidCallback? onPressed;

  const CustomButton({
    required this.title,
    required this.icon,
    this.onPressed,
    super.key,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(15),
        boxShadow: [
          BoxShadow(
            color: const Color.fromARGB(183, 0, 93, 223),
            spreadRadius: 0,
            blurRadius: 3,
            offset: const Offset(0, 3),
          ),
        ],
      ),
      child: SizedBox(
        child: TextButton(
          style: TextButton.styleFrom(
            backgroundColor: Colors.white,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(15),
              side: const BorderSide(
                color: Color.fromARGB(113, 158, 158, 158),
                width: 3,
              ),
            ),
          ),
          onPressed:
              onPressed ??
              () {
                blast(up);
              },
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              icon,
              Text(
                title,
                style: const TextStyle(fontSize: 10, color: Colors.black),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
