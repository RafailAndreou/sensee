import 'package:flutter/material.dart';
import 'widgets/connection/connection.dart';
import 'addactionbutton.dart';
import 'menu.dart';
import 'language_toggle.dart';
import '../../globals/connectionslist.dart';
import '../../globals/locale.dart';
import '../../server/server.dart';

class Gesturemapping extends StatelessWidget {
  const Gesturemapping({super.key});

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<String>(
      valueListenable: currentLanguage,
      builder: (context, lang, _) {
        return Column(
          children: [
            const Flexible(flex: 4, child: Menu()),
            const Spacer(flex: 1),
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
                          Connection(
                            key: ValueKey(connectionId),
                            id: connectionId,
                          ),
                          const SizedBox(height: 50),
                        ],
                      ],
                    ),
                  );
                },
              ),
            ),
            const Spacer(),
            Flexible(
              flex: 4,
              child: Row(
                children: [
                  Flexible(
                    flex: 4,
                    child: AddActionButton(title: tr('addAction', lang)),
                  ),
                  const Spacer(flex: 1),
                  TextButton(
                    child: Text(tr('applyApiChanges', lang)),
                    onPressed: () {
                      getApiStatus();
                    },
                  ),
                ],
              ),
            ),
            const SizedBox(height: 12),
            Flexible(flex: 1, child: Row(children: [const LanguageToggle()])),
          ],
        );
      },
    );
  }
}
