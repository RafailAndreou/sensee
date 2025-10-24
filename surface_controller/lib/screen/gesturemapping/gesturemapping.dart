import 'package:flutter/material.dart';
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
        Flexible(
          flex: 4,
          child: ListView(
            children: [
              SizedBox(child: Connection()),
              SizedBox(height: 50),
              SizedBox(child: Connection()),
            ],
          ),
        ),
        Spacer(),
        Flexible(
          flex: 4,
          child: Row(
            children: [
              Flexible(flex: 4, child: AddActionButton(title: "Add Action")),
            ],
          ),
        ),
      ],
    );
  }
}
