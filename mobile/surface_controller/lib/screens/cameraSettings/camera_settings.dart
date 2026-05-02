import 'package:flutter/material.dart';
import 'package:surface_controller/globals/sizes.dart';
import 'package:surface_controller/server/config_service.dart';

class CameraSettingsScreen extends StatefulWidget {
  const CameraSettingsScreen({super.key});

  @override
  State<CameraSettingsScreen> createState() => _CameraSettingsScreenState();
}

class _CameraSettingsScreenState extends State<CameraSettingsScreen> {
  bool _useNetwork = false;
  final TextEditingController _urlController = TextEditingController();
  bool _saving = false;

  @override
  void initState() {
    super.initState();
    _loadSettings();
  }

  @override
  void dispose() {
    _urlController.dispose();
    super.dispose();
  }

  Future<void> _loadSettings() async {
    final local = await loadCameraSettingsLocal();
    if (mounted) {
      setState(() {
        _useNetwork = local['useNetwork'] ?? false;
        _urlController.text = local['streamUrl'] ?? '';
      });
    }

    final server = await loadCameraSettings();
    if (server != null && mounted) {
      setState(() {
        _useNetwork = server['useNetwork'] ?? false;
        _urlController.text = server['streamUrl'] ?? '';
      });
      await saveCameraSettingsLocal(
        useNetwork: _useNetwork,
        streamUrl: _urlController.text,
      );
    }
  }

  Future<void> _save() async {
    setState(() => _saving = true);
    await saveCameraSettingsLocal(
      useNetwork: _useNetwork,
      streamUrl: _urlController.text.trim(),
    );
    await sendCameraSettings(
      useNetwork: _useNetwork,
      streamUrl: _urlController.text.trim(),
    );
    if (mounted) {
      setState(() => _saving = false);
      Navigator.pop(context);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFEAEDF4),
      appBar: AppBar(
        title: const Text(
          'Camera Settings',
          style: TextStyle(fontSize: 27, fontWeight: FontWeight.w500),
        ),
      ),
      body: Column(
        children: [
          Container(
            margin: const EdgeInsets.all(16),
            width: getProportionalHeight(context, 500),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: Colors.black12, width: 2),
            ),
            padding: const EdgeInsets.all(24),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Camera Source',
                  style: TextStyle(fontSize: 24, fontWeight: FontWeight.w700),
                ),
                const SizedBox(height: 16),
                Row(
                  children: [
                    const Icon(Icons.wifi, size: 40),
                    const SizedBox(width: 16),
                    const Expanded(
                      child: Text(
                        'Use Network Camera',
                        style: TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ),
                    Switch.adaptive(
                      value: _useNetwork,
                      activeTrackColor: Colors.blue,
                      onChanged: (val) => setState(() => _useNetwork = val),
                    ),
                  ],
                ),
                const SizedBox(height: 24),
                AnimatedOpacity(
                  opacity: _useNetwork ? 1.0 : 0.35,
                  duration: const Duration(milliseconds: 200),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'Stream URL',
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.w300,
                        ),
                      ),
                      const SizedBox(height: 8),
                      TextField(
                        controller: _urlController,
                        enabled: _useNetwork,
                        keyboardType: TextInputType.url,
                        decoration: InputDecoration(
                          hintText: 'rtsp://192.168.1.100:554/stream',
                          border: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(12),
                            borderSide:
                                const BorderSide(color: Colors.black12),
                          ),
                          enabledBorder: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(12),
                            borderSide: const BorderSide(
                              color: Colors.black12,
                              width: 1.5,
                            ),
                          ),
                        ),
                      ),
                      const SizedBox(height: 12),
                      Text(
                        'Supports RTSP (rtsp://) and HTTP(S) streams.\n'
                        'For Home Assistant cameras, use the stream URL\n'
                        'from the camera entity\'s attributes.',
                        style: TextStyle(
                          fontSize: 13,
                          color: Colors.grey[600],
                          height: 1.5,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
          TextButton(
            style: TextButton.styleFrom(
              backgroundColor: Colors.blue,
              padding: const EdgeInsets.symmetric(
                horizontal: 100,
                vertical: 12,
              ),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(8),
              ),
            ),
            onPressed: _saving ? null : _save,
            child: _saving
                ? const SizedBox(
                    width: 20,
                    height: 20,
                    child: CircularProgressIndicator(
                      color: Colors.white,
                      strokeWidth: 2,
                    ),
                  )
                : const Text(
                    'Save Settings',
                    style: TextStyle(color: Colors.white),
                  ),
          ),
        ],
      ),
    );
  }
}
