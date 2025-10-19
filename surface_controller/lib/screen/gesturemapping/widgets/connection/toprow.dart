import 'package:flutter/material.dart';

class TopRow extends StatelessWidget {
  const TopRow({super.key});

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceEvenly,
      crossAxisAlignment: CrossAxisAlignment.start,
      children: const [
        // Action (icon + label)
        Row(
          children: [
            Image(
              image: AssetImage('assets/connection/action.png'),
              width: 18,
              height: 37,
            ),
            SizedBox(width: 5),
            Text("Action", style: TextStyle(color: Colors.black)),
          ],
        ),

        // Gesture (okhand icon + label)
        Row(
          children: [
            Image(
              image: AssetImage('assets/connection/okhand.png'),
              width: 18,
              height: 37,
            ),
            SizedBox(width: 5),
            Text("Gesture", style: TextStyle(color: Colors.black)),
          ],
        ),

        // Play Music (sound icon + label)
        Row(
          children: [
            Image(
              image: AssetImage('assets/connection/sound.png'),
              width: 18,
              height: 37,
            ),
            SizedBox(width: 5),
            Text("Play Music", style: TextStyle(color: Colors.black)),
          ],
        ),
      ],
    );
  }
}
