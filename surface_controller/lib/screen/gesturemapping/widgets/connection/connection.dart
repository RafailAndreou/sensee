import 'package:flutter/material.dart';
import 'package:surface_controller/globals/connectionslist.dart';
import 'dropdownmenu.dart';
import 'handbutton.dart';
import 'configurebutton.dart';
import 'package:surface_controller/globals/global.dart';
import 'package:surface_controller/configue.dart';
import 'package:surface_controller/server/server.dart';
import 'package:surface_controller/globals/sizes.dart';
import 'removebutton.dart';

class Connection extends StatefulWidget {
  Connection({super.key, required this.id}) {
    debugPrint("Connection created with id: $id");
  }
  final int id;

  @override
  State<Connection> createState() => _ConnectionState();
}

class _ConnectionState extends State<Connection> {
  // Selected state for hand buttons: none, left, right, or both.
  HandSelection _selected = HandSelection.none;

  // Get this connection's configuration
  late final ConnectionConfig config;

  @override
  void initState() {
    super.initState();
    config = getConnectionConfig(widget.id);
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: const Color(0xFFE9E9E9),
        boxShadow: [
          BoxShadow(
            color: const Color.fromARGB(255, 141, 133, 232),
            spreadRadius: 2,
            blurRadius: 5,
            offset: const Offset(0, 3), // changes position of shadow
          ),
        ],
        borderRadius: BorderRadius.circular(5),
        border: Border.all(
          color: const Color.fromARGB(75, 86, 81, 81),
          width: 2,
        ),
      ),
      child: Column(
        children: [
          _buildTopRow(),
          SizedBox(height: getProportionalHeight(context, 10)),
          _buildMenuRow(),
          SizedBox(height: getProportionalHeight(context, 20)),
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
          flex: 6,
          child: DropDownMenu(
            selectedValue: "Play Music",
            options: const [
              "Play Music",
              "Open AC",
              "AC:cold",
              "AC:Hot",
              "TV:Turn On",
              "TV:Turn Off",
              "TV:Increase Volume",
              "TV:Decrease Volume",
            ],
            leadingIcon: const Image(
              image: AssetImage('assets/connection/menu/music.png'),
            ),
            config: config,
          ),
        ),
        Spacer(),
        Flexible(
          flex: 6,
          child: DropDownMenu(
            selectedValue: "Test",
            options: const ["Thumb+Index", "Thumb+Middle", "Thumb+Ring"],
            leadingIcon: const Image(
              image: AssetImage('assets/connection/menu/hand.png'),
            ),
            config: config,
          ),
        ),
        Spacer(),
        Flexible(
          flex: 6,
          child: DropDownMenu(
            selectedValue: "Sound1",
            options: const ["Sound1", "Sound2", "Sound3"],
            leadingIcon: const Image(
              image: AssetImage('assets/connection/menu/sound1.png'),
            ),
            config: config,
          ),
        ),
        Spacer(),
      ],
    );
  }

  /// "hand" label
  Widget _buildHandLabel() {
    return Row(
      children: const [
        Spacer(flex: 1),
        Flexible(
          flex: 7,
          child: Text("Gesture Hand ", style: TextStyle(color: Colors.black)),
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
                  const SizedBox(width: 10),
                  HandButton(
                    label: "Left",
                    onPressed: () {
                      setState(() => _selected = HandSelection.left);
                      config.hand.value = "Left";
                    },
                    backgroundColor:
                        (_selected == HandSelection.left ||
                            _selected == HandSelection.both)
                        ? const Color.fromARGB(255, 152, 209, 255)
                        : const Color.fromARGB(255, 255, 255, 255),
                  ),
                  const SizedBox(width: 5),
                  HandButton(
                    label: "Right",
                    onPressed: () {
                      setState(() => _selected = HandSelection.right);
                      config.hand.value = "Right";
                    },
                    backgroundColor:
                        (_selected == HandSelection.right ||
                            _selected == HandSelection.both)
                        ? const Color.fromARGB(255, 152, 209, 255)
                        : Colors.white,
                  ),
                  const SizedBox(width: 5),
                  HandButton(
                    label: "Both",
                    onPressed: () {
                      setState(() => _selected = HandSelection.both);
                      config.hand.value = "both";
                    },
                    backgroundColor: _selected == HandSelection.both
                        ? const Color.fromARGB(255, 152, 209, 255)
                        : Colors.white,
                  ),
                  const SizedBox(width: 20),
                  RemoveButton(
                    onPressed: () {
                      removeConnection(widget.id);
                      debugPrint("Removed connection with id: ${widget.id}");
                    },
                  ),
                  const SizedBox(width: 5),
                  ConfigureButton(
                    label: "Configure",
                    onPressed: () {
                      sendConfiguration(config);
                      print_config(config);
                    },
                  ),
                ],
              ),

              ValueListenableBuilder<String>(
                valueListenable: config.brand,
                builder: (context, value, child) => Text(value),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

enum HandSelection { none, left, right, both }
