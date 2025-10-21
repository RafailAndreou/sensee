// ignore_for_file: avoid_print
import 'package:flutter/material.dart';
import '../../../brands/configurationscreen.dart';
import 'package:surface_controller/global.dart';

class DropDownMenu extends StatelessWidget {
  final String selectedValue;
  final List<String> options;
  final Widget leadingIcon;
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
  });

  @override
  Widget build(BuildContext context) {
    return DropdownMenu<String>(
      leadingIcon: leadingIcon,
      menuStyle: MenuStyle(visualDensity: VisualDensity.standard),
      width: 105,
      textStyle: const TextStyle(
        color: Colors.black,
        fontSize: 10,
        overflow: TextOverflow.visible,
      ),
      inputDecorationTheme: const InputDecorationTheme(
        constraints: BoxConstraints(maxHeight: 37, maxWidth: 103),
        isDense: true,

        suffixIconColor: Color.fromARGB(255, 52, 52, 196),
        suffixIconConstraints: BoxConstraints(maxWidth: 35),
        prefixIconConstraints: BoxConstraints(
          maxWidth: 30,
          maxHeight: 30,
          minHeight: 30,
          minWidth: 20,
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
      dropdownMenuEntries: options
          .map(
            (option) => DropdownMenuEntry<String>(value: option, label: option),
          )
          .toList(),
      onSelected: (String? value) {
        // Handle selection change
        print('Selected: $value');
        if (value == "Sound1" || value == "Sound2" || value == "Sound3") {
          sound.value = value ?? '';
        }
        if (value == "Thumb+Index" ||
            value == "Thumb+Middle" ||
            value == "Thumb+Ring") {
          gesture.value = value ?? '';
        }
        if (value == "TV:Turn On" ||
            value == "TV:Turn Off" ||
            value == "TV:Increase Volume" ||
            value == "TV:Decrease Volume") {
          action.value = value ?? '';
          Navigator.of(context).push(
            MaterialPageRoute(
              builder: (context) => const ConfigurationScreen(),
            ),
          );
          // You can add additional logic here if needed
        }

        if (actions.contains(value)) {
          action.value = value ?? '';
        }
      },
    );
  }
}
