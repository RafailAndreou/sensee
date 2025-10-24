import 'package:flutter/material.dart';
import 'package:surface_controller/globals/connectionslist.dart';

class AddActionButton extends StatelessWidget {
  const AddActionButton({super.key, required this.title});

  final String title;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: () {
        addNewConnection();
        // Handle button tap
      },
      child: Container(
        alignment: Alignment.center,
        width: 138,
        height: 36,
        decoration: BoxDecoration(
          color: const Color(0xFFFFFFFF),
          borderRadius: BorderRadius.circular(15),
          border: Border.all(
            color: const Color.fromARGB(255, 16, 16, 16),
            width: 3,
          ),
        ),
        child: Row(
          children: [
            const SizedBox(width: 10),
            Image.asset('assets/plus.png', width: 15, height: 15),
            const SizedBox(width: 25),
            Text(title, style: TextStyle(fontSize: 10, color: Colors.black)),
          ],
        ),
      ),
    );
  }
}
