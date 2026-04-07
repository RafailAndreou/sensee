import 'package:flutter/widgets.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'dart:io';
import 'dart:async';
import 'package:surface_controller/globals/global.dart';
import 'package:multicast_dns/multicast_dns.dart';

const int _DISCOVERY_PORT = 54321;
const String _DISCOVERY_TOKEN = 'SENSEE_DISCOVER';
const List<int> _COMMON_SERVER_PORTS = <int>[8000, 8001, 8002, 8003, 8004];
const List<String> _COMMON_SERVER_HOSTS = <String>[
  'sensee.local',
  '127.0.0.1',
  '10.0.2.2',
];

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

Future<void> sendAllConfigurations() async {
  // 1. Convert the Map of configs into a List of JSON objects
  final List<Map<String, dynamic>> allConfigsData = [];

  connectionConfigs.forEach((id, config) {
    allConfigsData.add({
      "id": config.id.value.toString(),
      "connectionType": config.connectionType.value,
      "entityId": config.entityId.value,
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
      connectionConfigs.forEach((id, config) => config.isSynced.value = true);
    } else {
      print("⚠️ Server error (${response.statusCode})");
      connectionConfigs.forEach((id, config) => config.isSynced.value = false);
    }
  } catch (e) {
    print("❌ Failed to send configurations: $e");
    connectionConfigs.forEach((id, config) => config.isSynced.value = false);
  }
}

Future<void> sendConfiguration(ConnectionConfig config) async {
  await sendAllConfigurations();
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

/// Cache the server URL after the first successful discovery.
String? _cachedServerUrl;
Future<String?>? _discoveryInFlight;

String _toConfigurationUrl(String baseUrl) {
  if (baseUrl.endsWith('/configuration')) {
    return baseUrl;
  }
  return '$baseUrl/configuration';
}

String _toBaseUrl(String configurationUrl) {
  return configurationUrl.replaceFirst('/configuration', '');
}

Future<bool> _probeServerBaseUrl(String baseUrl, {int timeoutMs = 900}) async {
  try {
    final response = await http
        .get(Uri.parse(_toConfigurationUrl(baseUrl)))
        .timeout(Duration(milliseconds: timeoutMs));
    return response.statusCode == 200 || response.statusCode == 405;
  } catch (_) {
    return false;
  }
}

/// Try mDNS first, fallback to UDP discovery, then fallback to static IP
Future<String?> discoverServerSmart() async {
  if (_discoveryInFlight != null) {
    return _discoveryInFlight;
  }

  _discoveryInFlight = _discoverServerSmartInternal();
  try {
    return await _discoveryInFlight;
  } finally {
    _discoveryInFlight = null;
  }
}

Future<String?> _discoverServerSmartInternal() async {
  // 0. INSTANT PATH: Return cached URL if still reachable.
  if (_cachedServerUrl != null) {
    final cachedBase = _toBaseUrl(_cachedServerUrl!);
    if (await _probeServerBaseUrl(cachedBase)) {
      return _cachedServerUrl;
    }
    _cachedServerUrl = null;
  }

  // 1. FAST PATH: probe known host candidates and common ports.
  for (final host in _COMMON_SERVER_HOSTS) {
    for (final port in _COMMON_SERVER_PORTS) {
      final base = 'http://$host:$port';
      if (await _probeServerBaseUrl(base)) {
        _cachedServerUrl = _toConfigurationUrl(base);
        return _cachedServerUrl;
      }
    }
  }

  // Avoid mDNS/UDP fallback here: on some platforms this throws
  // (reusePort unsupported) and the backend currently does not answer UDP discovery.
  print('[Discovery] Direct probes failed for known hosts/ports.');
  return _cachedServerUrl;
}

Future<bool> isServerReachable({
  int timeoutMs = 1200,
  bool discoverIfUnknown = false,
}) async {
  try {
    if (_cachedServerUrl != null) {
      final cachedBase = _toBaseUrl(_cachedServerUrl!);
      if (await _probeServerBaseUrl(cachedBase, timeoutMs: timeoutMs)) {
        return true;
      }
    }

    for (final host in _COMMON_SERVER_HOSTS) {
      for (final port in _COMMON_SERVER_PORTS) {
        final base = 'http://$host:$port';
        if (await _probeServerBaseUrl(base, timeoutMs: timeoutMs)) {
          _cachedServerUrl = _toConfigurationUrl(base);
          return true;
        }
      }
    }

    if (!discoverIfUnknown) {
      return false;
    }

    return await discoverServerSmart() != null;
  } catch (_) {
    return false;
  }
}

// ---------------- Home Assistant Setup API ----------------

Future<Map<String, dynamic>?> getHAConfig() async {
  try {
    final baseUrl = await discoverServerSmart();
    if (baseUrl == null) return null;
    final url = baseUrl.replaceFirst('/configuration', '/ha/config');
    final response = await http.get(Uri.parse(url));
    if (response.statusCode == 200) return jsonDecode(response.body);
  } catch (e) {
    print('❌ Error getting HA config: $e');
  }
  return null;
}

Future<bool> saveHAConfig(String url, String token) async {
  try {
    final baseUrl = await discoverServerSmart();
    if (baseUrl == null) return false;
    final targetUrl = baseUrl.replaceFirst('/configuration', '/ha/config');
    final response = await http.post(
      Uri.parse(targetUrl),
      headers: {"Content-Type": "application/json"},
      body: jsonEncode({"url": url, "token": token}),
    );
    return response.statusCode == 200;
  } catch (e) {
    print('❌ Error saving HA config: $e');
    return false;
  }
}

Future<List<dynamic>> getHADiscovered() async {
  try {
    final baseUrl = await discoverServerSmart();
    if (baseUrl == null) return [];
    final url = baseUrl.replaceFirst('/configuration', '/ha/discovered');
    final response = await http.get(Uri.parse(url));
    if (response.statusCode == 200) {
      final decoded = jsonDecode(response.body);
      return decoded['flows'] ?? [];
    }
  } catch (e) {
    print('❌ Error fetching discovered HA devices: $e');
  }
  return [];
}

Future<Map<String, dynamic>?> startHAPairing(String handler) async {
  try {
    final baseUrl = await discoverServerSmart();
    if (baseUrl == null) return null;
    final url = baseUrl.replaceFirst('/configuration', '/ha/pair/start');
    final response = await http.post(
      Uri.parse(url),
      headers: {"Content-Type": "application/json"},
      body: jsonEncode({"handler": handler}),
    );
    if (response.statusCode == 200) {
      final decoded = jsonDecode(response.body);
      return decoded['result'];
    }
  } catch (e) {
    print('❌ Error starting HA pairing: $e');
  }
  return null;
}

Future<Map<String, dynamic>?> submitHAPairingStep(
  String flowId,
  Map<String, dynamic> userInput,
) async {
  try {
    final baseUrl = await discoverServerSmart();
    if (baseUrl == null) return null;
    final url = baseUrl.replaceFirst('/configuration', '/ha/pair/submit');
    final response = await http.post(
      Uri.parse(url),
      headers: {"Content-Type": "application/json"},
      body: jsonEncode({"flow_id": flowId, "user_input": userInput}),
    );
    if (response.statusCode == 200) {
      final decoded = jsonDecode(response.body);
      return decoded['result'];
    }
  } catch (e) {
    print('❌ Error submitting HA pairing step: $e');
  }
  return null;
}
