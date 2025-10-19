import 'package:flutter/material.dart';
import 'dropdownmenu.dart';
import 'handbutton.dart';
import 'configurebutton.dart';

class Connection extends StatelessWidget {
  const Connection({super.key});

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: const Color(0xFFE9E9E9),
        borderRadius: BorderRadius.circular(5),
        border: Border.all(
          color: const Color.fromARGB(75, 86, 81, 81),
          width: 2,
        ),
      ),
      // child must be outside the decoration
      child: Column(
        children: [
          Row(
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
          ),
          Row(
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
                ), // Image
              ), // DropDownMenu
            ],
          ), // Row
          const SizedBox(height: 15),
          Row(
            children: [
              const SizedBox(width: 60),
              const Text("hand", style: TextStyle(color: Colors.black)),
              const SizedBox(width: 5),
            ],
          ),
          Row(
            children: [
              SizedBox(
                height: 80,
                width: 350,
                child: Column(
                  children: [
                    const SizedBox(height: 5),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                      children: [
                        HandButton(
                          label: "Left",
                          onPressed: () {},
                          backgroundColor: Color(0xFFACA9A9),
                        ),
                        const SizedBox(width: 15),
                        HandButton(
                          label: "Right",
                          onPressed: () {},
                          backgroundColor: Color(0xFF71B8FF),
                        ),
                        SizedBox(width: 70),
                        ConfigureButton(label: "Configure", onPressed: () {}),
                      ],
                    ),
                  ],
                ),
              ),
            ],
          ), // Text
        ],
      ), // Column
    ); //  container
  }
}
