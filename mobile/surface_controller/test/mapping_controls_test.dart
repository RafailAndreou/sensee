import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:surface_controller/screens/actions/widgets/actionselectorcard.dart';
import 'package:surface_controller/globals/connectionslist.dart';
import 'package:surface_controller/globals/global.dart';

void main() {
  testWidgets(
    'capabilities restrict actions and expanded gestures are selectable',
    (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: ActionSelectorCard(
              deviceType: 'Light',
              brand: 'Switch',
              availableActions: ['Turn on', 'Turn off'],
            ),
          ),
        ),
      );
      final dropdowns = tester
          .widgetList<DropdownButton<String>>(
            find.byType(DropdownButton<String>),
          )
          .toList();
      expect(dropdowns.first.items!.map((e) => e.value), [
        'Turn on',
        'Turn off',
      ]);
      final gestures = dropdowns[1].items!.map((e) => e.value);
      expect(
        gestures,
        containsAll([
          'Thumb+Ring',
          'Thumb+Pinky',
          'Victory',
          'Thumb Up',
          'Thumb Down',
          'Pointing Up',
        ]),
      );
    },
  );

  test('server snapshots preserve unsaved edits to an existing mapping', () {
    connectionConfigs.clear();
    final local = getConnectionConfig(1);
    local.id.value = 1;
    local.action.value = 'Turn off';
    local.isSynced.value = false;
    applyServerConfigurationsSnapshot([
      {'id': '1', 'action': 'Turn on'},
    ]);
    expect(local.action.value, 'Turn off');
    expect(local.isSynced.value, isFalse);
    connectionConfigs.clear();
  });
}
