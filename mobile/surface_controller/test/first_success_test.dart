import 'dart:async';
import 'package:flutter_test/flutter_test.dart';
import 'package:surface_controller/server/first_success.dart';

void main() {
  test('a fast failed probe does not beat a reachable server', () async {
    final reachable = Completer<String?>();
    final result = firstSuccessful<String>([
      Future.value(null),
      reachable.future,
    ]);
    await Future<void>.delayed(Duration.zero);
    reachable.complete('sensee');
    expect(await result, 'sensee');
  });

  test('all failed probes return null', () async {
    expect(
      await firstSuccessful<String>([Future.value(null), Future.value(null)]),
      isNull,
    );
  });

  test('no candidates return null', () async {
    expect(await firstSuccessful<String>([]), isNull);
  });

  test('a slow unsuccessful probe does not delay a successful one', () async {
    final pending = Completer<String?>();
    final result = firstSuccessful<String>([
      pending.future,
      Future.value('sensee'),
    ]);
    expect(await result, 'sensee');
    pending.complete(null);
  });
}
