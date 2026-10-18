"""Session safety boundary and bounded, credential-free engine diagnostics."""
import threading
import time
import weakref
from collections import Counter, deque

lock = threading.RLock()
_diagnostics_lock = threading.RLock()
epoch = 0
test_mode = False
invalidated_ms = -1
_listeners = weakref.WeakSet()
_recent = deque(maxlen=64)
_rejections = Counter()
_metrics = {}


def register(callback):
    with lock:
        _listeners.add(callback)


def invalidate(reason):
    global epoch, invalidated_ms
    with lock:
        epoch += 1
        invalidated_ms = time.monotonic_ns() // 1_000_000
        for callback in list(_listeners):
            callback()
        record('invalidated', reason=reason)


def set_test_mode(enabled):
    global test_mode
    with lock:
        if test_mode != enabled:
            test_mode = enabled
            invalidate('test_mode')


def record(decision, **details):
    with _diagnostics_lock:
        _recent.append({'time': round(time.monotonic(), 3), 'decision': decision, **details})
        if decision == 'rejected':
            _rejections[details.get('reason', 'unknown')] += 1


def metric(**values):
    with _diagnostics_lock:
        _metrics.update(values)


def snapshot():
    with lock, _diagnostics_lock:
        age = _metrics.get('observation_timestamp_ms')
        return {'testMode': test_mode, 'epoch': epoch, 'metrics': dict(_metrics),
                'observationAgeMs': None if age is None else max(0, time.monotonic_ns() // 1_000_000 - age),
                'rejections': dict(_rejections), 'recent': list(_recent)}
