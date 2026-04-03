import 'package:flutter/material.dart';
import 'package:surface_controller/globals/connectionslist.dart';
import 'package:surface_controller/screens/dashboard/dashboard.dart';

void main() async {
  // You can process the message here
  WidgetsFlutterBinding.ensureInitialized();
  await loadConfigurationsFromFile();

  runApp(MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      home: Scaffold(
        backgroundColor: const Color(0xFFEAEDF4),
        appBar: AppBar(
          title: const Text(
            'Sensee  Gesture dashboard',
            style: TextStyle(fontWeight: FontWeight.w900),
          ),
        ),
        body: Padding(padding: const EdgeInsets.all(16.0), child: Dashboard()),
      ),
    );
  }
}
