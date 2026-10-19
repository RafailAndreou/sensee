import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:surface_controller/globals/gestures.dart';
import 'package:surface_controller/globals/locale.dart';
import 'package:surface_controller/screens/cameraSettings/camera_settings.dart';
import 'package:surface_controller/screens/gesturesettings/gesture_settings.dart';

void main() {
  setUp(() => SharedPreferences.setMockInitialValues({}));
  test('Flutter accepts the shared aliases as actual selector values', () {
    final aliases =
        jsonDecode(
              File('../../testdata/gesture_aliases.json').readAsStringSync(),
            )
            as Map;
    for (final e in aliases.entries) {
      expect(normalizeGestureName(e.key as String), e.value);
      expect(wakeGestureName(e.key as String), e.value);
      expect(supportedGestures, contains(e.value));
    }
  });

  testWidgets(
    'camera server load preserves a URL typed while the request is pending',
    (tester) async {
      final remote = Completer<Map<String, dynamic>?>();
      await tester.pumpWidget(
        MaterialApp(
          home: CameraSettingsScreen(
            loadLocal: () async => {
              'useNetwork': true,
              'streamUrl': 'local camera',
            },
            loadRemote: () => remote.future,
          ),
        ),
      );
      await tester.pump();
      await tester.enterText(find.byType(TextField), 'user draft camera');
      remote.complete({'useNetwork': false, 'streamUrl': 'late server camera'});
      await tester.pumpAndSettle();
      expect(find.text('user draft camera'), findsOneWidget);
      expect(find.text('late server camera'), findsNothing);
      expect(tester.widget<Switch>(find.byType(Switch)).value, isTrue);
    },
  );

  testWidgets('even the first local load cannot overwrite a user edit', (
    tester,
  ) async {
    final local = Completer<Map<String, dynamic>>();
    await tester.pumpWidget(
      MaterialApp(
        home: CameraSettingsScreen(
          loadLocal: () => local.future,
          loadRemote: () async => null,
        ),
      ),
    );
    await tester.tap(find.byType(Switch));
    await tester.pump();
    await tester.enterText(
      find.byType(TextField),
      'draft before local storage',
    );
    local.complete({'useNetwork': true, 'streamUrl': 'late stored camera'});
    await tester.pumpAndSettle();
    expect(find.text('draft before local storage'), findsOneWidget);
  });

  for (final success in [false, true]) {
    testWidgets(
      'camera pending save ($success) keeps later edits and its original payload',
      (tester) async {
        final saved = Completer<bool>();
        String? sentUrl;
        await tester.pumpWidget(
          MaterialApp(
            home: CameraSettingsScreen(
              loadLocal: () async => {
                'useNetwork': true,
                'streamUrl': 'original',
              },
              loadRemote: () async => null,
              saveRemote: (network, url) {
                sentUrl = url;
                return saved.future;
              },
            ),
          ),
        );
        await tester.pumpAndSettle();
        await tester.enterText(find.byType(TextField), 'saved snapshot');
        await tester.tap(find.text(t('camera_save')));
        await tester.pump();
        await tester.pump();
        expect(sentUrl, 'saved snapshot');
        await tester.enterText(find.byType(TextField), 'later unsaved edit');
        saved.complete(success);
        await tester.pumpAndSettle();
        expect(find.text('later unsaved edit'), findsOneWidget);
        if (!success) expect(find.byType(SnackBar), findsOneWidget);
        expect(tester.takeException(), isNull);
      },
    );
  }

  testWidgets(
    'browser-saved Fist loads into Flutter wake selector without assertion',
    (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Gesturesettings(
            loadLocal: () async => {'selectedGesture': 'Open Hand'},
            loadRemote: () async => {
              'wakeEnabled': true,
              'selectedGesture': 'Closed_Fist',
            },
          ),
        ),
      );
      await tester.pumpAndSettle();
      final dropdown = tester.widget<DropdownButton<String>>(
        find.byType(DropdownButton<String>),
      );
      expect(dropdown.value, 'Fist');
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets('wake load preserves a choice edited during the server request', (
    tester,
  ) async {
    final remote = Completer<Map<String, dynamic>?>();
    await tester.pumpWidget(
      MaterialApp(
        home: Gesturesettings(
          loadLocal: () async => {
            'wakeEnabled': true,
            'selectedGesture': 'Open Hand',
          },
          loadRemote: () => remote.future,
        ),
      ),
    );
    await tester.pumpAndSettle();
    tester
        .widget<DropdownButton<String>>(find.byType(DropdownButton<String>))
        .onChanged!('Victory');
    await tester.pump();
    remote.complete({'wakeEnabled': true, 'selectedGesture': 'Fist'});
    await tester.pumpAndSettle();
    expect(
      tester
          .widget<DropdownButton<String>>(find.byType(DropdownButton<String>))
          .value,
      'Victory',
    );
  });
}
