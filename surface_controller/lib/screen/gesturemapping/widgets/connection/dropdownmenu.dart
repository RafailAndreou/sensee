// ignore_for_file: avoid_print
import 'package:flutter/material.dart';
import '../../../brands/configurationscreen.dart';
import 'package:surface_controller/global.dart';

class DropDownMenu extends StatelessWidget {
  final String selectedValue;
  final List<String> options;
  final Widget leadingIcon;

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
        contentPadding: EdgeInsets.only(top: 5, bottom: 5),

        suffixIconColor: Color.fromARGB(255, 52, 52, 196),
        suffixIconConstraints: BoxConstraints(maxWidth: 27),
        prefixIconConstraints: BoxConstraints(maxWidth: 15),

        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.all(Radius.circular(5)),
          borderSide: BorderSide(
            color: Color.fromARGB(255, 255, 255, 255),
            width: 1.0,
          ),
        ),
        filled: true,
        fillColor: Color.fromARGB(255, 255, 255, 255),
      ),
      initialSelection: selectedValue,
      dropdownMenuEntries: options
          .map(
            (option) => DropdownMenuEntry<String>(value: option, label: option),
          )
          .toList(),
      onSelected: (String? value) {
        // Handle selection change
        action.value = value ?? '';
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
      },
    );
  }
}
