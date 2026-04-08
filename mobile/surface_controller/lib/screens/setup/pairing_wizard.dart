import 'package:flutter/material.dart';
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

    // We scan for a few seconds
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
          const SnackBar(content: Text("Failed to start pairing.")),
        );
      }
    }
  }

  void _showPinDialog() {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => AlertDialog(
        title: const Text("Enter PIN"),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text("A PIN code should appear on your TV. Please enter it below:"),
            const SizedBox(height: 20),
            TextField(
              controller: _pinController,
              keyboardType: TextInputType.number,
              decoration: const InputDecoration(
                border: OutlineInputBorder(),
                labelText: "PIN Code",
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text("Cancel"),
          ),
          ElevatedButton(
            onPressed: () => _submitPin(),
            child: const Text("Verify"),
          ),
        ],
      ),
    );
  }

  Future<void> _submitPin() async {
    if (_currentFlowId == null) return;
    
    final pin = _pinController.text.trim();
    if (pin.isEmpty) return;

    Navigator.pop(context); // Close dialog
    setState(() => _isPairing = true);

    final result = await submitHAPairingStep(_currentFlowId!, {"code": pin});

    if (mounted) {
      setState(() => _isPairing = false);
      if (result != null && result['type'] == 'create_entry') {
        _showSuccess();
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text("Pairing failed. Check the PIN and try again.")),
        );
      }
    }
  }

  void _showSuccess() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text("Success!"),
        content: const Text("Your TV is now linked to Sensee. You can now set up gestures for it."),
        actions: [
          ElevatedButton(
            onPressed: () {
              Navigator.pop(context); // Close dialog
              Navigator.pop(context); // Go back to device type selection
            },
            child: const Text("Finish"),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFEAEDF4),
      appBar: AppBar(
        title: const Text("Find New Devices"),
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
                        Text("Scanning your network for ${widget.deviceType}s..."),
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
                        const Icon(Icons.search_off, size: 64, color: Colors.grey),
                        const SizedBox(height: 16),
                        Text("No new ${widget.deviceType}s found on your network."),
                        const SizedBox(height: 24),
                        ElevatedButton(
                          onPressed: _startDiscovery,
                          child: const Text("Try Again"),
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
                      // Android TV usually shows under 'androidtv_remote'
                      final name = flow['context']['title'] ?? "Unknown Device";
                      final handler = flow['handler'];

                      return Card(
                        margin: const EdgeInsets.only(bottom: 12),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)),
                        child: ListTile(
                          contentPadding: const EdgeInsets.all(16),
                          leading: const Icon(Icons.tv, color: Colors.blue, size: 32),
                          title: Text(name, style: const TextStyle(fontWeight: FontWeight.bold)),
                          subtitle: Text("Type: ${handler.replaceAll('_', ' ')}"),
                          trailing: const Icon(Icons.add_circle, color: Colors.blue),
                          onTap: () => _initiatePairing(handler),
                        ),
                      );
                    },
                  ),
                ),
            ],
          ),
    );
  }
}
