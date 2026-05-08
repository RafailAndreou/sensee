import 'package:flutter/material.dart';
import 'package:surface_controller/globals/locale.dart';
import '../../server/server.dart';
import 'dart:async';

class PairingWizard extends StatefulWidget {
  final String deviceType;

  const PairingWizard({super.key, required this.deviceType});

  @override
  State<PairingWizard> createState() => _PairingWizardState();
}

class _PairingWizardState extends State<PairingWizard> {
  bool _isScanning = true;
  List<dynamic> _discoveredFlows = [];
  String? _currentFlowId;
  bool _isPairing = false;
  final TextEditingController _pinController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _startDiscovery();
  }

  @override
  void dispose() {
    _pinController.dispose();
    super.dispose();
  }

  Future<void> _startDiscovery() async {
    setState(() {
      _isScanning = true;
      _discoveredFlows = [];
    });

    final flows = await getHADiscovered();

    if (mounted) {
      setState(() {
        _discoveredFlows = flows;
        _isScanning = false;
      });
    }
  }

  Future<void> _initiatePairing(String handler) async {
    setState(() => _isPairing = true);

    final result = await startHAPairing(handler);

    if (mounted) {
      if (result != null && result.containsKey('flow_id')) {
        setState(() {
          _currentFlowId = result['flow_id'];
          _isPairing = false;
        });
        _showPinDialog();
      } else {
        setState(() => _isPairing = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(t('pairing_failed_start'))),
        );
      }
    }
  }

  void _showPinDialog() {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => AlertDialog(
        title: Text(t('pairing_pin_title')),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(t('pairing_pin_content')),
            const SizedBox(height: 20),
            TextField(
              controller: _pinController,
              keyboardType: TextInputType.number,
              decoration: InputDecoration(
                border: const OutlineInputBorder(),
                labelText: t('pairing_pin_label'),
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: Text(t('pairing_cancel')),
          ),
          ElevatedButton(
            onPressed: () => _submitPin(),
            child: Text(t('pairing_verify')),
          ),
        ],
      ),
    );
  }

  Future<void> _submitPin() async {
    if (_currentFlowId == null) return;

    final pin = _pinController.text.trim();
    if (pin.isEmpty) return;

    Navigator.pop(context);
    setState(() => _isPairing = true);

    final result = await submitHAPairingStep(_currentFlowId!, {"code": pin});

    if (mounted) {
      setState(() => _isPairing = false);
      if (result != null && result['type'] == 'create_entry') {
        _showSuccess();
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(t('pairing_failed_pin'))),
        );
      }
    }
  }

  void _showSuccess() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(t('pairing_success_title')),
        content: Text(t('pairing_success_content')),
        actions: [
          ElevatedButton(
            onPressed: () {
              Navigator.pop(context);
              Navigator.pop(context);
            },
            child: Text(t('pairing_finish')),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<String>(
      valueListenable: appLocale,
      builder: (context, _, __) {
        return Scaffold(
          backgroundColor: const Color(0xFFEAEDF4),
          appBar: AppBar(
            title: Text(t('pairing_title')),
          ),
          body: _isPairing
              ? const Center(child: CircularProgressIndicator())
              : Column(
                  children: [
                    if (_isScanning)
                      Padding(
                        padding: const EdgeInsets.all(40.0),
                        child: Center(
                          child: Column(
                            children: [
                              const CircularProgressIndicator(),
                              const SizedBox(height: 20),
                              Text(
                                tFormat(
                                  'pairing_scanning',
                                  widget.deviceType,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    if (!_isScanning && _discoveredFlows.isEmpty)
                      Expanded(
                        child: Center(
                          child: Column(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              const Icon(
                                Icons.search_off,
                                size: 64,
                                color: Colors.grey,
                              ),
                              const SizedBox(height: 16),
                              Text(
                                tFormat(
                                  'pairing_none_found',
                                  widget.deviceType,
                                ),
                              ),
                              const SizedBox(height: 24),
                              ElevatedButton(
                                onPressed: _startDiscovery,
                                child: Text(t('pairing_try_again')),
                              ),
                            ],
                          ),
                        ),
                      ),
                    if (!_isScanning && _discoveredFlows.isNotEmpty)
                      Expanded(
                        child: ListView.builder(
                          padding: const EdgeInsets.all(16),
                          itemCount: _discoveredFlows.length,
                          itemBuilder: (context, index) {
                            final flow = _discoveredFlows[index];
                            final name =
                                flow['context']['title'] ?? "Unknown Device";
                            final handler = flow['handler'];

                            return Card(
                              margin: const EdgeInsets.only(bottom: 12),
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(15),
                              ),
                              child: ListTile(
                                contentPadding: const EdgeInsets.all(16),
                                leading: const Icon(
                                  Icons.tv,
                                  color: Colors.blue,
                                  size: 32,
                                ),
                                title: Text(
                                  name,
                                  style: const TextStyle(
                                    fontWeight: FontWeight.bold,
                                  ),
                                ),
                                subtitle: Text(
                                  "Type: ${handler.replaceAll('_', ' ')}",
                                ),
                                trailing: const Icon(
                                  Icons.add_circle,
                                  color: Colors.blue,
                                ),
                                onTap: () => _initiatePairing(handler),
                              ),
                            );
                          },
                        ),
                      ),
                  ],
                ),
        );
      },
    );
  }
}
