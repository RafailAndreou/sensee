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
      child: Column(
        children: [
          _buildTopRow(),
          const SizedBox(height: 10),
          _buildMenuRow(),
          const SizedBox(height: 50),
          _buildHandLabel(),
          _buildHandButtons(),
        ],
      ),
    );
  }

  /// Top row with icon labels (Action, Gesture, Play Music)
  Widget _buildTopRow() {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceEvenly,
      crossAxisAlignment: CrossAxisAlignment.start,
      children: const [
        // Action (icon + label)
        Spacer(),
        Flexible(
          flex: 4,
          child: Row(
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
        ),

        // Gesture (okhand icon + label)
        Flexible(
          flex: 4,
          child: Row(
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
        ),

        // Play Music (sound icon + label)
        Flexible(
          flex: 4,
          child: Row(
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
        ),
      ],
    );
  }

  /// Row with three dropdown menus
  Widget _buildMenuRow() {
    return Row(
      children: [
        Spacer(),
        Flexible(
          flex: 4,
          child: DropDownMenu(
            selectedValue: "Play Music",
            options: const ["Play Music", "Open Ac", "Turn on tv"],
            leadingIcon: const Image(
              image: AssetImage('assets/connection/menu/music.png'),
            ),
          ),
        ),
        Spacer(),
        Flexible(
          flex: 4,
          child: DropDownMenu(
            selectedValue: "Thumb+Index",
            options: const ["Thumb+Index", "Thumb+Middle", "Thumb+Ring"],
            leadingIcon: const Image(
              image: AssetImage('assets/connection/menu/hand.png'),
            ),
          ),
        ),
        Spacer(),
        Flexible(
          flex: 4,
          child: DropDownMenu(
            selectedValue: "Sound1",
            options: const ["Sound1", "Sound2", "Sound3"],
            leadingIcon: const Image(
              image: AssetImage('assets/connection/menu/sound1.png'),
            ),
          ),
        ),
      ],
    );
  }

  /// "hand" label
  Widget _buildHandLabel() {
    return Row(
      children: const [
        Spacer(flex: 1),
        Flexible(
          flex: 6,
          child: Text("hand", style: TextStyle(color: Colors.black)),
        ),
      ],
    );
  }

  /// Hand buttons (Left/Right) and Configure button
  Widget _buildHandButtons() {
    return Row(
      children: [
        SizedBox(
          child: Column(
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                children: [
                  HandButton(
                    label: "Left",
                    onPressed: () {},
                    backgroundColor: const Color(0xFFACA9A9),
                  ),
                  const SizedBox(width: 30),
                  HandButton(
                    label: "Right",
                    onPressed: () {},
                    backgroundColor: const Color(0xFF71B8FF),
                  ),
                  const SizedBox(width: 110),
                  ConfigureButton(label: "Configure", onPressed: () {}),
                ],
              ),
            ],
          ),
        ),
      ],
    );
  }
}
