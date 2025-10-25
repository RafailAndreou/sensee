import 'package:flutter/material.dart';
import '../../irblaster.dart';
import 'package:surface_controller/globals/sizes.dart';

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
        gradient: LinearGradient(
          colors: [
            const Color.fromARGB(255, 219, 219, 219),
            const Color.fromARGB(255, 250, 250, 250),
          ],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(20),
        boxShadow: [
          BoxShadow(
            color: const Color.fromARGB(100, 0, 0, 0),
            spreadRadius: 1,
            blurRadius: 5,
            offset: const Offset(2, 2), // changes position of shadow
          ),
        ],
      ),
      child: SizedBox(
        height: getProportionalHeight(context, 35),
        child: TextButton(
          style: TextButton.styleFrom(
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(15),
            ),
          ),
          onPressed:
              onPressed ??
              () {
                blast(up);
              },
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              icon,
              Text(
                title,
                style: TextStyle(
                  fontSize: getProportionalWidth(context, 9),
                  fontFamily: 'Roboto',
                  color: const Color.fromARGB(255, 0, 0, 0),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
