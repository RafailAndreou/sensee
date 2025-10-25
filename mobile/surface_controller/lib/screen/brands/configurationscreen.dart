import 'package:flutter/material.dart';
import 'widgets/search.dart';
import 'package:surface_controller/globals/global.dart';

class ConfigurationScreen extends StatelessWidget {
  final ConnectionConfig config;

  const ConfigurationScreen({super.key, required this.config});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(Icons.home),
          onPressed: () {
            Navigator.of(context).popUntil((route) => route.isFirst);
          },
        ),
      ),
      body: Search(
        config: config,
        onChanged: (value) {
          // Handle search input changes
        },
      ),
    );
  }
}
