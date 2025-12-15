import 'package:flutter/widgets.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'dart:io';
import 'dart:async';
import 'package:surface_controller/globals/global.dart';
import 'package:multicast_dns/multicast_dns.dart';

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

/// Simple GET request to sensee.local:8000/api
Future<Map<String, dynamic>?> getApiStatus() async {
  try {
    print('[API] Fetching status from sensee.local:8000/api...');
    final response = await http
        .get(Uri.parse('http://sensee.local:8000/api'))
        .timeout(const Duration(seconds: 3));

    if (response.statusCode == 200) {
      print('[API] ✅ Response received');
      return jsonDecode(response.body) as Map<String, dynamic>;
    } else {
      print('[API] ⚠️ Server returned ${response.statusCode}');
      return null;
    }
  } catch (e) {
    print('[API] ❌ Failed to fetch: $e');
    return null;
  }
}

Future<void> sendAllConfigurations() async {
  // 1. Convert the Map of configs into a List of JSON objects
  final List<Map<String, dynamic>> allConfigsData = [];

  connectionConfigs.forEach((id, config) {
    allConfigsData.add({
      "id": config.id.value.toString(),
      "brand": config.brand.value,
      "action": config.action.value,
      "gesture": config.gesture.value,
      "sound": config.sound.value,
      "hand": config.hand.value,
    });
  });

  debugPrint('[Config] Sending ${allConfigsData.length} configurations...');

  try {
    final discovered = await discoverServerSmart();

    if (discovered == null) {
      print("❌ Failed to discover server.");
      return;
    }

    final response = await http.post(
      Uri.parse(discovered),
      headers: {"Content-Type": "application/json"},
      // 2. Encode the LIST (not a single object) as the body
      body: jsonEncode(allConfigsData),
    );

    if (response.statusCode == 200) {
      print("✅ All configurations sent successfully!");
    } else {
      print("⚠️ Server error (${response.statusCode})");
    }
  } catch (e) {
    print("❌ Failed to send configurations: $e");
  }
}

Future<void> sendConfiguration(ConnectionConfig config) async {
  final configData = {
    "id": config.id.value.toString(),
    "brand": config.brand.value,
    "action": config.action.value,
    "gesture": config.gesture.value,
    "sound": config.sound.value,
    "hand": config.hand.value,
  };

  debugPrint('[Config] Full payload: $configData'); // ✅ Add this
  // debugPrint('[Config] ID value: ${config.id.value}'); // ✅ And this

  try {
    final discovered = await discoverServerSmart();

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

/// Discover server using mDNS (sensee.local)
/// Returns a full configuration POST URL like 'http://<ip>:<port>/configuration'
// inside mobile/surface_controller/lib/server/server.dart

Future<String?> discoverServerMDNS({int timeoutMs = 3000}) async {
  final MDnsClient client = MDnsClient();
  await client.start();

  try {
    print('[mDNS] Looking for _sensee._tcp.local...');

    await for (final PtrResourceRecord ptr
        in client
            .lookup<PtrResourceRecord>(
              ResourceRecordQuery.serverPointer('_sensee._tcp.local'),
            )
            .timeout(Duration(milliseconds: timeoutMs))) {
      print('[mDNS] Found service: ${ptr.domainName}');

      // Resolve the SRV record to get the port and hostname
      await for (final SrvResourceRecord srv
          in client
              .lookup<SrvResourceRecord>(
                ResourceRecordQuery.service(ptr.domainName),
              )
              .timeout(Duration(milliseconds: 1000))) {
        print('[mDNS] SRV: ${srv.target}:${srv.port}');

        // --- NEW LOGIC START ---
        // Instead of looking up the IP, use the hostname directly.
        String hostname = srv.target;

        // MDNS hostnames often end with a dot (e.g., "sensee.local."), remove it.
        if (hostname.endsWith('.')) {
          hostname = hostname.substring(0, hostname.length - 1);
        }

        final url = 'http://$hostname:${srv.port}/configuration';
        print('[mDNS] ✅ Server found at $url (using hostname)');

        client.stop();
        return url;
        // --- NEW LOGIC END ---
      }
    }

    print('[mDNS] ❌ No server found');
    client.stop();
    return null;
  } catch (e) {
    print('[mDNS] ❌ Error: $e');
    client.stop();
    return null;
  }
}

/// Try mDNS first, fallback to UDP discovery, then fallback to static IP
Future<String?> discoverServerSmart() async {
  // 1. FAST PATH: Just trust the OS resolver (like the browser does)
  // If "sensee.local" works in Chrome, this will work immediately.
  try {
    print(
      '[Discovery] 🚀 Trying direct connection to http://sensee.local:8000...',
    );
    final directUrl = 'http://sensee.local:8000/configuration';
    // Send a quick HEAD or GET request to verify it's actually there
    final response = await http
        .get(Uri.parse(directUrl))
        .timeout(const Duration(milliseconds: 1500));
    if (response.statusCode == 200 || response.statusCode == 405) {
      print('[Discovery] ✅ Direct connection successful!');
      return directUrl;
    }
  } catch (e) {
    print('[Discovery] Direct connection failed, falling back to scanning...');
  }

  // 2. SLOW PATH: Scan the network (your existing logic)
  print('[Discovery] Scanning mDNS...');
  String? result = await discoverServerMDNS(timeoutMs: 2000);
  if (result != null) return result;

  print('[Discovery] Scanning UDP...');
  result = await discoverServer(timeoutMs: 3000);
  return result;
}
