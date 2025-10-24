import 'package:flutter/material.dart';
import 'widgets/connection/connection.dart';
import 'addactionbutton.dart';
import 'menu.dart';
import '../../globals/connectionslist.dart';

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
          flex: 13,
          child: ValueListenableBuilder(
            valueListenable: connectionsList,
            builder: (context, value, child) {
              final connections = value;
              return SingleChildScrollView(
                child: Column(
                  children: [
                    for (final connectionId in connections) ...[
                      Connection(key: ValueKey(connectionId), id: connectionId),
                      SizedBox(height: 50),
                    ],
                  ],
                ),
              );
            },
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
