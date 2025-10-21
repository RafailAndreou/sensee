import 'package:flutter/material.dart';
import 'search.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      home: Scaffold(
        body: Search(
          onChanged: (value) {
            // Handle search input changes
          },
        ),
      ),
    );
  }
}
