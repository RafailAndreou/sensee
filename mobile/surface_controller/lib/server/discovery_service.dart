import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:http/http.dart' as http;
import 'package:multicast_dns/multicast_dns.dart';
import 'first_success.dart';
import 'package:shared_preferences/shared_preferences.dart';

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
  Uri get voiceSettingsUri => _uriForPath('/voice-settings');
  Uri get voiceStatusUri => _uriForPath('/voice-status');
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

Future<bool> _probeClient(
  ServerClient client, {
  int timeoutMs = 900,
  DiscoveryCancellation? cancellation,
}) async {
  if (cancellation?.cancelled == true) return false;
  final transport = http.Client();
  cancellation?.add(transport.close);
  try {
    final response = await transport
        .get(client.pingUri)
        .timeout(Duration(milliseconds: timeoutMs));
    if (response.statusCode != 200) return false;
    final body = jsonDecode(response.body);
    return body is Map && body['status'] == 'ok' && body['service'] == 'sensee';
  } catch (_) {
    return false;
  } finally {
    transport.close();
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

Future<String?> discoverServer({
  int timeoutMs = 3000,
  DiscoveryCancellation? cancellation,
}) async {
  RawDatagramSocket? socket;
  try {
    socket = await RawDatagramSocket.bind(InternetAddress.anyIPv4, 0);
    if (cancellation?.cancelled == true) {
      socket.close();
      return null;
    }
    socket.broadcastEnabled = true;

    final data = utf8.encode(_discoveryToken);
    socket.send(data, InternetAddress('255.255.255.255'), _discoveryPort);

    final completer = Completer<String?>();
    final timer = Timer(Duration(milliseconds: timeoutMs), () {
      if (!completer.isCompleted) completer.complete(null);
      socket?.close();
    });

    cancellation?.add(() {
      timer.cancel();
      socket?.close();
      if (!completer.isCompleted) completer.complete(null);
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

    return await completer.future;
  } catch (_) {
    socket?.close();
    return null;
  }
}

Future<String?> discoverServerMDNS({
  int timeoutMs = 3000,
  DiscoveryCancellation? cancellation,
}) async {
  final client = MDnsClient();

  try {
    await client.start();
    if (cancellation?.cancelled == true) {
      client.stop();
      return null;
    }
    cancellation?.add(client.stop);
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

class DiscoveryCancellation {
  bool cancelled = false;
  final List<void Function()> _closers = [];
  void add(void Function() closer) {
    if (cancelled) {
      closer();
    } else {
      _closers.add(closer);
    }
  }

  void cancel() {
    cancelled = true;
    for (final closer in _closers) {
      closer();
    }
    _closers.clear();
  }
}

Future<String?> _discoverServerSmartInternal() async {
  if (_cachedClient != null && await _probeOrFresh(_cachedClient!)) {
    return _cachedClient!.configUri.toString();
  }
  invalidateServerClientCache();
  final cancellation = DiscoveryCancellation();
  final preferences = await SharedPreferences.getInstance();
  Future<ServerClient?> probe(ServerClient candidate) async =>
      await _probeClient(candidate, cancellation: cancellation)
      ? candidate
      : null;
  Future<ServerClient?> discover(Future<String?> result) async {
    final address = await result;
    if (address == null || cancellation.cancelled) return null;
    return probe(ServerClient.fromConfigurationUri(Uri.parse(address)));
  }

  try {
    final last = preferences.getString('sensee.lastAddress');
    final winner = await firstSuccessful<ServerClient>([
      if (last != null) probe(ServerClient(last)),
      discover(discoverServerMDNS(timeoutMs: 1500, cancellation: cancellation)),
      discover(discoverServer(timeoutMs: 1200, cancellation: cancellation)),
      for (final host in _commonServerHosts)
        for (final port in _commonServerPorts)
          probe(ServerClient('http://$host:$port')),
    ]);
    if (winner == null) return null;
    cancellation.cancel();
    _cachedClient = winner;
    _lastProbeOk = DateTime.now();
    await preferences.setString('sensee.lastAddress', winner.baseUrl);
    return winner.configUri.toString();
  } finally {
    cancellation.cancel();
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

    invalidateServerClientCache();
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
