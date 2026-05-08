import 'package:flutter/material.dart';

class Gesturebutton extends StatelessWidget {
  const Gesturebutton({super.key, required this.gestureName});

  final String gestureName;

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 140,
      decoration: BoxDecoration(
        color: Theme.of(context).cardColor,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.15),
            blurRadius: 6,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Image.asset(
              'assets/redesign/gesture.png',
              width: 42,
              height: 42,
              color: Theme.of(context).brightness == Brightness.dark
                  ? Colors.white
                  : null,
              colorBlendMode: BlendMode.srcIn,
            ),
            const SizedBox(height: 10),
            Text(
              'Gesture:\n$gestureName',
              textAlign: TextAlign.center,
              style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
            ),
          ],
        ),
      ),
    );
  }
}
