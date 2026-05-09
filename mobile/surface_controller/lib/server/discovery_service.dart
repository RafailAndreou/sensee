import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:multicast_dns/multicast_dns.dart';

const int _discoveryPort = 54321;
const String _discoveryToken = 'SENSEE_DISCOVER';
const List<int> _commonServerPorts = <int>[8000, 8001, 8002, 8003, 8004];
const List<String> _commonServerHosts = <String>[
  'sensee.local',
  '127.0.0.1',
  '10.0.2.2',
];

class ServerClient {
  const ServerClient(this.baseUrl);

  final String baseUrl;

  Uri _uriForPath(String path) {
    return Uri.parse(baseUrl).resolve(path);
  }

  Uri get configUri => _uriForPath('/configuration');
  Uri get currentConfigUri => _uriForPath('/current');
  Uri get gestureSettingsUri => _uriForPath('/gesture-settings');
  Uri get cameraSettingsUri => _uriForPath('/camera-settings');
  Uri get ironmanParamsUri => _uriForPath('/ironman-params');
  Uri get haCamerasUri => _uriForPath('/ha/cameras');
  Uri get haConfigUri => _uriForPath('/ha/config');
  Uri get haDiscoveredUri => _uriForPath('/ha/discovered');
  Uri get haPairStartUri => _uriForPath('/ha/pair/start');
  Uri get haPairSubmitUri => _uriForPath('/ha/pair/submit');
  Uri get pingUri => _uriForPath('/ping');
  Uri get smartDevicesUri => _uriForPath('/smart-devices');
  Uri get videoUri => _uriForPath('/video');

  static ServerClient fromConfigurationUri(Uri configurationUri) {
    final segments = List<String>.from(configurationUri.pathSegments);
    if (segments.isNotEmpty && segments.last == 'configuration') {
      segments.removeLast();
    }

    final String basePath = segments.isEmpty ? '' : '/${segments.join('/')}';
    final baseUri = configurationUri.replace(
      path: basePath,
      query: null,
      fragment: null,
    );

    return ServerClient(baseUri.toString());
  }
}

ServerClient? _cachedClient;
Future<String?>? _discoveryInFlight;
DateTime? _lastProbeOk;
const Duration _probeFreshness = Duration(seconds: 2);

void invalidateServerClientCache() {
  _cachedClient = null;
  _lastProbeOk = null;
}

Future<bool> _probeClient(ServerClient client, {int timeoutMs = 900}) async {
  try {
    final response = await http
        .get(client.pingUri)
        .timeout(Duration(milliseconds: timeoutMs));
    return response.statusCode == 200;
  } catch (_) {
    return false;
  }
}

Future<bool> _probeOrFresh(ServerClient client, {int timeoutMs = 900}) async {
  final now = DateTime.now();
  if (_lastProbeOk != null && now.difference(_lastProbeOk!) < _probeFreshness) {
    return true;
  }
  final ok = await _probeClient(client, timeoutMs: timeoutMs);
  if (ok) _lastProbeOk = now;
  return ok;
}

Future<String?> discoverServer({int timeoutMs = 3000}) async {
  RawDatagramSocket? socket;
  try {
    socket = await RawDatagramSocket.bind(InternetAddress.anyIPv4, 0);
    socket.broadcastEnabled = true;

    final data = utf8.encode(_discoveryToken);
    socket.send(data, InternetAddress('255.255.255.255'), _discoveryPort);

    final completer = Completer<String?>();
    final timer = Timer(Duration(milliseconds: timeoutMs), () {
      if (!completer.isCompleted) completer.complete(null);
      socket?.close();
    });

    socket.listen((event) {
      if (event != RawSocketEvent.read) return;

      final datagram = socket?.receive();
      if (datagram == null) return;

      try {
        final resp = utf8.decode(datagram.data);
        final decoded = jsonDecode(resp);
        final ip = decoded['ip'] ?? datagram.address.address;
        final port = decoded['port'] ?? 8000;
        final client = ServerClient('http://$ip:$port');
        if (!completer.isCompleted) {
          completer.complete(client.configUri.toString());
        }
      } catch (_) {
        final client = ServerClient('http://${datagram.address.address}:8000');
        if (!completer.isCompleted) {
          completer.complete(client.configUri.toString());
        }
      } finally {
        timer.cancel();
        socket?.close();
      }
    });

    return completer.future;
  } catch (_) {
    socket?.close();
    return null;
  }
}

Future<String?> discoverServerMDNS({int timeoutMs = 3000}) async {
  final client = MDnsClient();
  await client.start();

  try {
    await for (final PtrResourceRecord ptr
        in client
            .lookup<PtrResourceRecord>(
              ResourceRecordQuery.serverPointer('_sensee._tcp.local'),
            )
            .timeout(Duration(milliseconds: timeoutMs))) {
      await for (final SrvResourceRecord srv
          in client
              .lookup<SrvResourceRecord>(
                ResourceRecordQuery.service(ptr.domainName),
              )
              .timeout(const Duration(milliseconds: 1000))) {
        final String host = srv.target.endsWith('.')
            ? srv.target.substring(0, srv.target.length - 1)
            : srv.target;
        final discoveredClient = ServerClient('http://$host:${srv.port}');
        client.stop();
        return discoveredClient.configUri.toString();
      }
    }

    client.stop();
    return null;
  } catch (_) {
    client.stop();
    return null;
  }
}

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
  // 1. Check cached client first
  if (_cachedClient != null && await _probeOrFresh(_cachedClient!)) {
    return _cachedClient!.configUri.toString();
  }
  invalidateServerClientCache();

  // 2. The "Smart" part: Try mDNS first (Fast & Reliable)
  debugPrint("Attempting mDNS discovery...");
  final mdnsResult = await discoverServerMDNS(timeoutMs: 1500);
  if (mdnsResult != null) {
    _cachedClient = ServerClient.fromConfigurationUri(Uri.parse(mdnsResult));
    _lastProbeOk = DateTime.now();
    debugPrint("Found via mDNS: $mdnsResult");
    return mdnsResult;
  }

  // 3. Try UDP broadcast discovery before falling back to port scanning.
  debugPrint("mDNS failed, trying UDP discovery...");
  final udpResult = await discoverServer(timeoutMs: 1200);
  if (udpResult != null) {
    _cachedClient = ServerClient.fromConfigurationUri(Uri.parse(udpResult));
    _lastProbeOk = DateTime.now();
    debugPrint("Found via UDP discovery: $udpResult");
    return udpResult;
  }

  // 4. The Fallback: Concurrent port scanning (Fixes the 13.5s freeze)
  debugPrint("mDNS failed, falling back to concurrent pinging...");

  // Create a list of all possible combinations
  final List<ServerClient> candidates = [];
  for (final host in _commonServerHosts) {
    for (final port in _commonServerPorts) {
      candidates.add(ServerClient('http://$host:$port'));
    }
  }

  // Fire them all concurrently and catch the first one that responds
  try {
    final winningClient = await Future.any(
      candidates.map((candidate) async {
        if (await _probeClient(candidate)) {
          return candidate;
        }
        // Throwing an error removes this failed future from Future.any()
        throw Exception('Probe failed');
      }),
    );

    _cachedClient = winningClient;
    _lastProbeOk = DateTime.now();
    debugPrint("Found via fallback: ${winningClient.configUri}");
    return winningClient.configUri.toString();
  } catch (_) {
    // All probes failed
    debugPrint("All discovery methods failed.");
    return null;
  }
}

Future<bool> isServerReachable({
  int timeoutMs = 1200,
  bool discoverIfUnknown = false,
}) async {
  try {
    if (_cachedClient != null &&
        await _probeOrFresh(_cachedClient!, timeoutMs: timeoutMs)) {
      return true;
    }

    for (final host in _commonServerHosts) {
      for (final port in _commonServerPorts) {
        final candidate = ServerClient('http://$host:$port');
        if (await _probeClient(candidate, timeoutMs: timeoutMs)) {
          _cachedClient = candidate;
          _lastProbeOk = DateTime.now();
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

Future<ServerClient?> getServerClient() async {
  if (_cachedClient != null && await _probeOrFresh(_cachedClient!)) {
    return _cachedClient;
  }

  final discovered = await discoverServerSmart();
  if (discovered == null) {
    return null;
  }

  _cachedClient = ServerClient.fromConfigurationUri(Uri.parse(discovered));
  return _cachedClient;
}
