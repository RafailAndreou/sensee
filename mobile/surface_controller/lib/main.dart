import 'package:flutter/material.dart';
import 'screen/gesturemapping/gesturemapping.dart';
import 'globals/connectionslist.dart';

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
        appBar: AppBar(title: const Text('Sensee Smart Controller')),
        body: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Gesturemapping(),
        ),
      ),
    );
  }
}
