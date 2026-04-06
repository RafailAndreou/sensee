import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import '../../server/server.dart' as server_sync;
import '../actions/actiondetails.dart';

class SmartDeviceList extends StatefulWidget {
  final String deviceType;

  const SmartDeviceList({super.key, required this.deviceType});

  @override
  State<SmartDeviceList> createState() => _SmartDeviceListState();
}

class _SmartDeviceListState extends State<SmartDeviceList> {
  bool _isLoading = true;
  String? _error;
  List<dynamic> _devices = [];

  @override
  void initState() {
    super.initState();
    _fetchDevices();
  }

  Future<void> _fetchDevices() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final discoveredUrl = await server_sync.discoverServerSmart();
      if (discoveredUrl == null) {
        throw Exception("Could not discover server.");
      }

      // Reconstruct URL to point to /smart-devices
      final uri = Uri.parse(discoveredUrl);
      final fetchUrl = Uri(
        scheme: uri.scheme,
        host: uri.host,
        port: uri.port,
        path: '/smart-devices',
      );

      final response = await http.get(fetchUrl).timeout(const Duration(seconds: 5));
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        if (data['status'] == 'success') {
          // Filter devices by type (or keep all for now if type mapping fails)
          final allDevices = data['devices'] as List;
          setState(() {
            _devices = allDevices.where((d) => d['type'].toString().toLowerCase() == widget.deviceType.toLowerCase()).toList();
            _isLoading = false;
          });
        } else {
          throw Exception("Server returned failure status.");
        }
      } else {
        throw Exception("Server error ${response.statusCode}");
      }
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFEAEDF4),
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => Navigator.of(context).pop(),
        ),
        title: Text(
          'Select Smart ${widget.deviceType}',
          style: const TextStyle(fontWeight: FontWeight.w900),
        ),
      ),
      body: _buildBody(),
    );
  }

  Widget _buildBody() {
    if (_isLoading) {
      return const Center(child: CircularProgressIndicator());
    }

    if (_error != null) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.error_outline, size: 48, color: Colors.red),
              const SizedBox(height: 16),
              Text(
                "Failed to load devices\n$_error",
                textAlign: TextAlign.center,
                style: const TextStyle(fontSize: 16),
              ),
              const SizedBox(height: 24),
              ElevatedButton(
                onPressed: _fetchDevices,
                child: const Text("Retry"),
              )
            ],
          ),
        ),
      );
    }

    if (_devices.isEmpty) {
      return Center(
        child: Text(
          "No smart ${widget.deviceType}s found on the network.",
          style: TextStyle(color: Colors.grey[600], fontSize: 16),
        ),
      );
    }

    return ListView.builder(
      padding: const EdgeInsets.all(12),
      itemCount: _devices.length,
      itemBuilder: (context, index) {
        final device = _devices[index];
        return Card(
          elevation: 2,
          margin: const EdgeInsets.only(bottom: 12),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          child: ListTile(
            contentPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
            leading: Icon(_getIconForType(widget.deviceType), color: Colors.blue),
            title: Text(device['friendly_name'], style: const TextStyle(fontWeight: FontWeight.bold)),
            subtitle: Text(device['entity_id'], style: TextStyle(fontSize: 12, color: Colors.grey[600])),
            trailing: const Icon(Icons.add_circle, color: Colors.blue),
            onTap: () {
                Navigator.of(context).push(
                    MaterialPageRoute(
                        builder: (_) => ActionDetails(
                            deviceType: widget.deviceType,
                            brand: "${device['friendly_name']}",
                            connectionType: "smart",
                            entityId: device['entity_id'],
                        ),
                    ),
                );
            },
          ),
        );
      },
    );
  }

  IconData _getIconForType(String type) {
    switch (type.toLowerCase()) {
      case 'tv': return Icons.tv;
      case 'ac': return Icons.ac_unit;
      case 'light': return Icons.lightbulb;
      case 'fan': return Icons.air;
      default: return Icons.devices;
    }
  }
}
