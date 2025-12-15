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
import 'package:surface_controller/globals/locale.dart';

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

    // Initialize hand selection from saved config
    final handValue = config.hand.value.toLowerCase();
    if (handValue == 'left') {
      _selected = HandSelection.left;
    } else if (handValue == 'right') {
      _selected = HandSelection.right;
    } else if (handValue == 'both') {
      _selected = HandSelection.both;
    } else {
      _selected = HandSelection.none;
    }
  }

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<String>(
      valueListenable: currentLanguage,
      builder: (context, lang, _) {
        return Container(
          decoration: BoxDecoration(
            color: const Color(0xFFE9E9E9),
            gradient: const LinearGradient(
              colors: [
                Color.fromARGB(255, 240, 240, 255),
                Color.fromARGB(255, 220, 220, 255),
              ],
            ),
            boxShadow: const [
              BoxShadow(
                color: Color.fromARGB(255, 141, 133, 232),
                spreadRadius: 2,
                blurRadius: 5,
                offset: Offset(0, 3),
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
              _buildTopRow(lang),
              SizedBox(height: getProportionalHeight(context, 10)),
              _buildMenuRow(lang),
              SizedBox(height: getProportionalHeight(context, 20)),
              _buildHandLabel(lang),
              _buildHandButtons(lang),
              _buildBrandDisplay(),
            ],
          ),
        );
      },
    );
  }

  /// Top row with icon labels (Action, Gesture, Play Music)
  Widget _buildTopRow(String lang) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceEvenly,
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Spacer(),
        Flexible(
          flex: 4,
          child: Row(
            children: [
              const Image(
                image: AssetImage('assets/connection/action.png'),
                width: 18,
                height: 37,
              ),
              const SizedBox(width: 5),
              Text(
                tr('action', lang),
                style: const TextStyle(color: Colors.black),
              ),
            ],
          ),
        ),
        Flexible(
          flex: 4,
          child: Row(
            children: [
              const Image(
                image: AssetImage('assets/connection/okhand.png'),
                width: 18,
                height: 37,
              ),
              const SizedBox(width: 5),
              Text(
                tr('gesture', lang),
                style: const TextStyle(color: Colors.black),
              ),
            ],
          ),
        ),
        Flexible(
          flex: 4,
          child: Row(
            children: [
              const Image(
                image: AssetImage('assets/connection/sound.png'),
                width: 18,
                height: 37,
              ),
              const SizedBox(width: 5),
              Text(
                tr('playMusic', lang),
                style: const TextStyle(color: Colors.black),
              ),
            ],
          ),
        ),
      ],
    );
  }

  /// Row with three dropdown menus
  Widget _buildMenuRow(String lang) {
    final actionOptions = [
      tr('playMusicAction', lang),
      tr('openAc', lang),
      tr('acCold', lang),
      tr('acHot', lang),
      tr('tvTurnOn', lang),
      tr('tvTurnOff', lang),
      tr('tvIncreaseVolume', lang),
      tr('tvDecreaseVolume', lang),
    ];
    final gestureOptions = [
      tr('thumbIndex', lang),
      tr('thumbMiddle', lang),
      tr('thumbRing', lang),
    ];
    final soundOptions = [
      tr('sound1', lang),
      tr('sound2', lang),
      tr('sound3', lang),
    ];

    return Row(
      children: [
        const Spacer(),
        Flexible(
          flex: 6,
          child: DropDownMenu(
            selectedValue: tr('playMusicAction', lang),
            options: actionOptions,
            leadingIcon: const Image(
              image: AssetImage('assets/connection/menu/music.png'),
            ),
            config: config,
          ),
        ),
        const Spacer(),
        Flexible(
          flex: 6,
          child: DropDownMenu(
            selectedValue: "Test",
            options: gestureOptions,
            leadingIcon: const Image(
              image: AssetImage('assets/connection/menu/hand.png'),
            ),
            config: config,
          ),
        ),
        const Spacer(),
        Flexible(
          flex: 6,
          child: DropDownMenu(
            selectedValue: tr('sound1', lang),
            options: soundOptions,
            leadingIcon: const Image(
              image: AssetImage('assets/connection/menu/sound1.png'),
            ),
            config: config,
          ),
        ),
        const Spacer(),
      ],
    );
  }

  /// "hand" label
  Widget _buildHandLabel(String lang) {
    return Row(
      children: [
        const Spacer(flex: 1),
        Flexible(
          flex: 7,
          child: Text(
            tr('gestureHand', lang),
            style: const TextStyle(color: Colors.black),
          ),
        ),
      ],
    );
  }

  /// Hand buttons (Left/Right) and Configure button
  Widget _buildHandButtons(String lang) {
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: Row(
        children: [
          const SizedBox(width: 10),
          HandButton(
            label: tr('left', lang),
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
            label: tr('right', lang),
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
            label: tr('both', lang),
            onPressed: () {
              setState(() => _selected = HandSelection.both);
              config.hand.value = "both";
            },
            backgroundColor: _selected == HandSelection.both
                ? const Color.fromARGB(255, 152, 209, 255)
                : Colors.white,
          ),
          const SizedBox(width: 15),
          RemoveButton(
            label: tr('remove', lang),
            onPressed: () {
              removeConnection(widget.id);
              debugPrint("Removed connection with id: ${widget.id}");
              writeCountConnections(countConnections());
              readCountConnections().then((value) {
                debugPrint("Read from file: $value");
              });
              configuesToJson();
              saveConfigsToFile();
            },
          ),
          const SizedBox(width: 5),
          ConfigureButton(
            label: tr('configure', lang),
            onPressed: () {
              sendAllConfigurations();
              print_config(config);
              writeCountConnections(countConnections());
              readCountConnections().then((value) {
                debugPrint("Read from file: $value");
              });
              configuesToJson();
              saveConfigsToFile();
            },
          ),
          const SizedBox(width: 10),
        ],
      ),
    );
  }

  /// Brand display
  Widget _buildBrandDisplay() {
    return ValueListenableBuilder<String>(
      valueListenable: config.brand,
      builder: (context, value, child) => Text(value),
    );
  }
}

enum HandSelection { none, left, right, both }
