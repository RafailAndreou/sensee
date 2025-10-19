import 'package:flutter/material.dart';
import 'dropdownmenu.dart';

class Menus extends StatelessWidget {
  const Menus({super.key});

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        const SizedBox(width: 15),
        DropDownMenu(
          selectedValue: "Play Music",
          options: const ["Play Music", "Open Ac", "Turn on tv"],
          leadingIcon: Image(
            image: AssetImage('assets/connection/menu/music.png'),
          ),
        ),
        const SizedBox(width: 20),
        DropDownMenu(
          selectedValue: "Thumb+Index",
          options: const ["Thumb+Index", "Thumb+Middle", "Thumb+Ring"],
          leadingIcon: Image(
            image: AssetImage('assets/connection/menu/hand.png'),
          ),
        ),
        const SizedBox(width: 20),
        DropDownMenu(
          selectedValue: "Sound1",
          options: const ["Sound1", "Sound2", "Sound3"],
          leadingIcon: Image(
            image: AssetImage('assets/connection/menu/sound1.png'),
          ),
        ),
      ],
    );
  }
}
