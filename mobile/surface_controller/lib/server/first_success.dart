import 'dart:async';

/// A failed probe must not win a race against a reachable server.
Future<T?> firstSuccessful<T>(Iterable<Future<T?>> attempts) {
  final probes = attempts.toList();
  if (probes.isEmpty) return Future<T?>.value(null);
  final allFailed = Completer<T?>();
  var remaining = probes.length;
  return Future.any<T?>(
    probes.map((probe) async {
      final value = await probe;
      if (value != null) return value;
      remaining -= 1;
      if (remaining == 0) allFailed.complete(null);
      return allFailed.future;
    }),
  );
}
