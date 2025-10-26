import 'package:http/http.dart' as http;
import 'dart:convert';
import 'dart:io';
import 'dart:async';
import 'package:surface_controller/globals/global.dart';

const int _DISCOVERY_PORT = 54321;
const String _DISCOVERY_TOKEN = 'SENSEE_DISCOVER';

/// Broadcast a UDP discovery probe and wait for the first JSON reply.
/// Returns a full configuration POST URL like 'http://<ip>:<port>/configuration'
Future<String?> discoverServer({int timeoutMs = 3000}) async {
  RawDatagramSocket? socket;
  try {
    print('[Discovery] Starting UDP discovery on port $_DISCOVERY_PORT...');
    socket = await RawDatagramSocket.bind(InternetAddress.anyIPv4, 0);

    // Enable broadcast
    socket.broadcastEnabled = true;

    print(
      '[Discovery] Socket bound to ${socket.address.address}:${socket.port}',
    );

    // Send broadcast probe
    final data = utf8.encode(_DISCOVERY_TOKEN);
    final bytesSent = socket.send(
      data,
      InternetAddress('255.255.255.255'),
      _DISCOVERY_PORT,
    );
    print(
      '[Discovery] Sent $bytesSent bytes to 255.255.255.255:$_DISCOVERY_PORT',
    );

    final completer = Completer<String?>();
    final timer = Timer(Duration(milliseconds: timeoutMs), () {
      print('[Discovery] Timeout after ${timeoutMs}ms - no response received');
      if (!completer.isCompleted) completer.complete(null);
      socket?.close();
    });

    socket.listen((event) {
      if (event == RawSocketEvent.read) {
        final datagram = socket?.receive();
        if (datagram != null) {
          print(
            '[Discovery] Received ${datagram.data.length} bytes from ${datagram.address.address}:${datagram.port}',
          );
          try {
            final resp = utf8.decode(datagram.data);
            print('[Discovery] Response: $resp');
            final decoded = jsonDecode(resp);
            final ip = decoded['ip'] ?? datagram.address.address;
            final port = decoded['port'] ?? 8000;
            final url = 'http://$ip:$port/configuration';
            print('[Discovery] ✅ Server found at $url');
            if (!completer.isCompleted) completer.complete(url);
          } catch (e) {
            print('[Discovery] JSON parse error: $e, using fallback');
            // If reply was not JSON, fallback to using sender address
            final ip = datagram.address.address;
            final url = 'http://$ip:8000/configuration';
            if (!completer.isCompleted) completer.complete(url);
          } finally {
            timer.cancel();
            socket?.close();
          }
        }
      }
    });

    return completer.future;
  } catch (e) {
    print('[Discovery] ❌ Exception: $e');
    socket?.close();
    return null;
  }
}

Future<void> sendConfiguration(ConnectionConfig config) async {
  final configData = {
    "brand": config.brand.value,
    "action": config.action.value,
    "gesture": config.gesture.value,
    "sound": config.sound.value,
    "hand": config.hand.value,
  };

  try {
    final discovered = await discoverServer();

    if (discovered == null) {
      print(
        "❌ Failed to discover server. Make sure the server is running and accessible on the network.",
      );
      return;
    }

    final response = await http.post(
      Uri.parse(discovered),
      headers: {"Content-Type": "application/json"},
      body: jsonEncode(configData),
    );

    if (response.statusCode == 200) {
      print("✅ Configuration sent successfully to $discovered!");
    } else {
      print("⚠️ Server error (${response.statusCode}) from $discovered");
    }
  } catch (e) {
    print("❌ Failed to send configuration: $e");
  }
}
