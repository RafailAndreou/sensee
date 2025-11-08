// ignore_for_file: avoid_print
import 'package:flutter/material.dart';
import '../../../brands/configurationscreen.dart';
import 'package:surface_controller/globals/global.dart';
import 'package:surface_controller/globals/sizes.dart';

class DropDownMenu extends StatefulWidget {
  final String selectedValue;
  final List<String> options;
  final Widget leadingIcon;
  final ConnectionConfig config;
  final List<String> actions = const [
    "Play Music",
    "Open AC",
    "AC:cold",
    "AC:Hot",
    "TV:Turn on",
    "TV:Turn Off",
    "TV:Turn Off",
  ];

  const DropDownMenu({
    super.key,
    required this.selectedValue,
    required this.options,
    required this.leadingIcon,
    required this.config,
  });

  @override
  State<DropDownMenu> createState() => _DropDownMenuState();
}

class _DropDownMenuState extends State<DropDownMenu> {
  late String _currentValue;

  @override
  void initState() {
    super.initState();
    // Initialize the current value based on the config type
    _currentValue = _getInitialValue();
  }

  String _getInitialValue() {
    // Determine which config field is being used based on widget.options
    if (widget.options.contains("Sound1")) {
      // This is the sound dropdown
      final sound = widget.config.sound.value;
      return widget.options.contains(sound) ? sound : widget.selectedValue;
    } else if (widget.options.contains("Thumb+Index")) {
      // This is the gesture dropdown
      final gesture = widget.config.gesture.value;
      return widget.options.contains(gesture) ? gesture : widget.selectedValue;
    } else {
      // This is the action dropdown
      final action = widget.config.action.value;
      return widget.options.contains(action) ? action : widget.selectedValue;
    }
  }

  @override
  Widget build(BuildContext context) {
    return DropdownMenu<String>(
      initialSelection: _currentValue,
      leadingIcon: widget.leadingIcon,
      menuStyle: MenuStyle(visualDensity: VisualDensity.standard),
      width: 105,
      textStyle: const TextStyle(
        color: Colors.black,
        fontSize: 10,
        overflow: TextOverflow.visible,
      ),
      inputDecorationTheme: InputDecorationTheme(
        constraints: BoxConstraints(maxHeight: 37, maxWidth: 103),
        isDense: true,

        suffixIconColor: Color.fromARGB(255, 52, 52, 196),
        suffixIconConstraints: BoxConstraints(maxWidth: 35),
        prefixIconConstraints: BoxConstraints(
          maxWidth: getProportionalWidth(context, 30),
          maxHeight: getProportionalHeight(context, 30),
          minHeight: getProportionalHeight(context, 25),
          minWidth: getProportionalWidth(context, 20),
        ),

        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.all(Radius.circular(5)),
          borderSide: BorderSide(
            color: Color.fromARGB(255, 28, 219, 226),
            width: 2.0,
          ),
        ),
        filled: true,
        fillColor: Color.fromARGB(255, 255, 255, 255),
      ),
      hintText: "Add",
      dropdownMenuEntries: widget.options
          .map(
            (option) => DropdownMenuEntry<String>(value: option, label: option),
          )
          .toList(),
      onSelected: (String? value) {
        // Handle selection change
        print('Selected: $value');
        setState(() {
          _currentValue = value ?? widget.selectedValue;
        });

        if (value == "Sound1" || value == "Sound2" || value == "Sound3") {
          widget.config.sound.value = value ?? '';
        }
        if (value == "Thumb+Index" ||
            value == "Thumb+Middle" ||
            value == "Thumb+Ring") {
          widget.config.gesture.value = value ?? '';
        }
        if (value == "TV:Turn On" ||
            value == "TV:Turn Off" ||
            value == "TV:Increase Volume" ||
            value == "TV:Decrease Volume") {
          widget.config.action.value = value ?? '';
          Navigator.of(context).push(
            MaterialPageRoute(
              builder: (context) => ConfigurationScreen(config: widget.config),
            ),
          );
          // You can add additional logic here if needed
        }

        if (widget.actions.contains(value)) {
          widget.config.action.value = value ?? '';
        }
      },
    );
  }
}
