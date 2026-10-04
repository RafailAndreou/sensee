import 'dart:async';

import 'package:flutter/material.dart';
import 'package:surface_controller/globals/locale.dart';
import 'package:surface_controller/server/server.dart' as server_sync;
import 'package:surface_controller/server/auth_http.dart' as auth;

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
  bool _isPaired = false;

  @override
  void initState() {
    super.initState();
    auth.pairingRequired.addListener(_onPairingRequired);
    _refreshConnectivity();
    _timer = Timer.periodic(
      const Duration(seconds: 4),
      (_) => _refreshConnectivity(),
    );
  }

  @override
  void dispose() {
    _timer?.cancel();
    auth.pairingRequired.removeListener(_onPairingRequired);
    super.dispose();
  }

  void _onPairingRequired() {
    if (mounted && auth.pairingRequired.value) {
      setState(() => _isPaired = false);
    }
  }

  Future<void> _pair() async {
    final client = await server_sync.getServerClient();
    if (client == null || !mounted) return;
    var enteredKey = '';
    final key = await showDialog<String>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Pair with Sensee'),
        content: TextField(
          onChanged: (value) => enteredKey = value,
          obscureText: true,
          autofocus: true,
          decoration: const InputDecoration(
            labelText: 'Pairing key',
            helperText: 'Shown in the Sensee engine window',
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, enteredKey),
            child: const Text('Pair'),
          ),
        ],
      ),
    );
    if (key == null || key.trim().isEmpty) return;
    try {
      final ok = await auth.pairWithServer(Uri.parse(client.baseUrl), key);
      if (!mounted) return;
      if (!ok) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Pairing failed. Check the key and try again.'),
          ),
        );
      }
      await _refreshConnectivity();
    } catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text('Could not pair: $error')));
      }
    }
  }

  Future<void> _refreshConnectivity({
    bool discoverIfUnknown = false,
    bool showChecking = false,
  }) async {
    if (showChecking && mounted) {
      setState(() {
        _isConnected = null;
      });
    }

    if (_refreshInFlight) {
      return;
    }

    final wasOnline = _isConnected == true && _isPaired;

    _refreshInFlight = true;
    final reachable = await server_sync.isServerReachable(
      discoverIfUnknown: discoverIfUnknown,
    );
    final client = reachable ? await server_sync.getServerClient() : null;
    final paired =
        client != null && await auth.isPaired(Uri.parse(client.baseUrl));
    _refreshInFlight = false;

    if (!mounted) {
      return;
    }
    setState(() {
      _isConnected = reachable;
      _isPaired = paired;
    });

    final becameOnline = !wasOnline && reachable && paired;
    if (becameOnline && !_autoSyncInFlight) {
      _autoSyncInFlight = true;
      try {
        await server_sync.pullLatestConfigurationsFromServer();
      } finally {
        _autoSyncInFlight = false;
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<String>(
      valueListenable: appLocale,
      builder: (context, _, __) {
        final isChecking = _isConnected == null;
        final isOnline = _isConnected == true && _isPaired;
        final needsPairing = _isConnected == true && !_isPaired;

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
            ? t('banner_checking')
            : isOnline
            ? t('banner_online')
            : needsPairing
            ? 'Pair with Sensee to continue'
            : t('banner_offline');

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
                  onPressed: needsPairing
                      ? _pair
                      : () => _refreshConnectivity(
                          discoverIfUnknown: true,
                          showChecking: true,
                        ),
                  child: Text(needsPairing ? 'Pair' : t('banner_retry')),
                ),
            ],
          ),
        );
      },
    );
  }
}
