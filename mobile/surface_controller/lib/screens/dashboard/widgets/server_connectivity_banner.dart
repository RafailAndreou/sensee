import 'dart:async';

import 'package:flutter/material.dart';
import 'package:surface_controller/server/server.dart' as server_sync;

class ServerConnectivityBanner extends StatefulWidget {
  const ServerConnectivityBanner({super.key});

  @override
  State<ServerConnectivityBanner> createState() =>
      _ServerConnectivityBannerState();
}

class _ServerConnectivityBannerState extends State<ServerConnectivityBanner> {
  bool? _isConnected;
  Timer? _timer;
  bool _refreshInFlight = false;
  bool _autoSyncInFlight = false;

  @override
  void initState() {
    super.initState();
    _refreshConnectivity();
    _timer = Timer.periodic(
      const Duration(seconds: 4),
      (_) => _refreshConnectivity(),
    );
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  Future<void> _refreshConnectivity({bool discoverIfUnknown = false}) async {
    if (_refreshInFlight) {
      return;
    }

    final wasOnline = _isConnected == true;

    _refreshInFlight = true;
    final reachable = await server_sync.isServerReachable(
      discoverIfUnknown: discoverIfUnknown,
    );
    _refreshInFlight = false;

    if (!mounted) {
      return;
    }
    setState(() {
      _isConnected = reachable;
    });

    final becameOnline = !wasOnline && reachable;
    if (becameOnline && !_autoSyncInFlight) {
      _autoSyncInFlight = true;
      try {
        await server_sync.sendAllConfigurations();
      } finally {
        _autoSyncInFlight = false;
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final isChecking = _isConnected == null;
    final isOnline = _isConnected == true;

    final Color backgroundColor = isChecking
        ? const Color(0xFFE5E7EB)
        : isOnline
        ? const Color(0xFFDFF5E7)
        : const Color(0xFFFFE3E3);

    final Color foregroundColor = isChecking
        ? const Color(0xFF374151)
        : isOnline
        ? const Color(0xFF166534)
        : const Color(0xFF991B1B);

    final IconData icon = isChecking
        ? Icons.sync
        : isOnline
        ? Icons.cloud_done
        : Icons.cloud_off;

    final String text = isChecking
        ? 'Checking Python server connection...'
        : isOnline
        ? 'Connected to Python server'
        : 'Disconnected from Python server';

    return AnimatedContainer(
      duration: const Duration(milliseconds: 220),
      margin: const EdgeInsets.fromLTRB(16, 10, 16, 6),
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      decoration: BoxDecoration(
        color: backgroundColor,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: foregroundColor.withValues(alpha: 0.25)),
      ),
      child: Row(
        children: [
          Icon(icon, size: 18, color: foregroundColor),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              text,
              style: TextStyle(
                fontWeight: FontWeight.w700,
                color: foregroundColor,
              ),
            ),
          ),
          if (!isOnline)
            TextButton(
              onPressed: () => _refreshConnectivity(discoverIfUnknown: true),
              child: const Text('Retry'),
            ),
        ],
      ),
    );
  }
}
