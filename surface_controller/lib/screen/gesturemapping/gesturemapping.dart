import 'package:flutter/material.dart';
import 'buttons.dart';
import 'widgets/connection/connection.dart';
import 'addactionbutton.dart';
import 'menu.dart';

class Gesturemapping extends StatelessWidget {
  const Gesturemapping({super.key});

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Flexible(flex: 4, child: Menu()),
        Spacer(flex: 1),
        // keep the connection widget at its intended height
        Flexible(flex: 4, child: const SizedBox(child: Connection())),
        Spacer(),
        Flexible(
          flex: 4,
          child: Row(
            children: [
              Spacer(),
              Flexible(flex: 4, child: AddActionButton(title: "Add Action")),
            ],
          ),
        ),
        Flexible(
          flex: 1,
          child: CustomButton(
            title: "Test",
            icon: Image.asset("assets/deviceaction.png"),
          ),
        ),
      ],
    );
  }
}
