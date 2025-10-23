import 'package:flutter/material.dart';
import 'widgets/connection/connection.dart';
import 'addactionbutton.dart';
import 'menu.dart';
import 'package:surface_controller/server/camera.dart';

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
        TextButton(
          onPressed: () {
            Navigator.of(
              context,
            ).push(MaterialPageRoute(builder: (context) => VideoPage()));
          },
          child: const Text("Test Button"),
        ),
      ],
    );
  }
}
