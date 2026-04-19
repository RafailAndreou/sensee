# AI Assistant Guidelines: Sensee Project

This document serves as a strict set of architectural and stylistic guidelines for any AI assistant or developer contributing to the Sensee codebase.

The current codebase is highly pragmatic, thread-safe, and optimized for edge devices (Raspberry Pi). Future contributions **must not introduce overhead, redundant logic, or typical "AI slop."**

## Core Philosophy

1. **Respect Edge Constraints:** The system runs real-time computer vision alongside network transport. CPU cycles and memory are precious.
2. **Event-Driven Over Polling:** Threads must sleep when idle and wake instantly.
3. **No "AI Slop":** Avoid overly verbose logic, unnecessary `while True: time.sleep(0.01)` loops, redundant object instantiation, and over-engineered abstractions.

---

## 1. Concurrency and Threading

- **Strict Event-Driven State:** Always use `threading.Condition` or `threading.Event` to signal between threads. Do not write naive polling loops to check for new frames or states.
- **Decouple High-Latency Operations:** Keep camera/CV processing completely decoupled from action execution threads. Network requests (like Home Assistant calls) must never freeze the camera stream.

## 2. Queue and Data Management

- **Handle Queue Blocking Gracefully:** When using fixed-size queues (e.g., `Queue(maxsize=1)`), always account for backpressure. If an action thread is busy, use `.put_nowait()` and catch `queue.Full` to discard stale actions rather than blocking the producer thread.
- **Drop Stale Data:** In real-time CV pipelines, it is better to drop a frame or an old gesture than to build up latency. Maintain patterns like `collections.deque(maxlen=1)` for frame/gesture buffers.

## 3. Memory and Garbage Collection

- **Smart Caching:** Use `functools.lru_cache` for repetitive string normalization or high-frequency functional calculations to prevent spamming the garbage collector.
- **Avoid Object Churn:** Do not instantiate new objects inside tight loops (like the frame capture loop) unless absolutely necessary.

## 4. Network and External APIs

- **Idiomatic Concurrency:** When writing network discovery or fallback logic (e.g., in Dart), use language-idiomatic patterns like racing futures (`Future.any()`) rather than sequential timeouts.
- **Debounce and Throttle:** High-frequency physical inputs (like gestures for volume control) must be explicitly debounced using time locks to prevent flooding external APIs (like Home Assistant).

## 5. What NOT to Do (Anti-Patterns)

- **DO NOT** add unnecessary `try/except` blocks that silently swallow critical errors without logging.
- **DO NOT** add `time.sleep()` inside worker loops unless it is part of an explicit keep-alive or fallback mechanism. Rely on blocking queue gets or event waits.
- **DO NOT** add massive class hierarchies. Stick to dataclasses and simple, stateless functions where possible.
  """)
