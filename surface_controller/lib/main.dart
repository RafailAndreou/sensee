import 'package:flutter/material.dart';
import 'gesturemapping/gesturemapping.dart';
import 'server/server.dart';
import 'irblaster.dart';

void main() {
  // Start the HTTP server in the background
  waitForMessage().then((message) {
    print('✅ Server received message: $message');
    if (message == "click") {
      blast(up);
    }
    // You can process the message here
  });

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
        body: Gesturemapping(),
      ),
    );
  }
}
