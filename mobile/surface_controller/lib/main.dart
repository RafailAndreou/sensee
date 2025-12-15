import 'package:flutter/material.dart';
import 'screen/gesturemapping/gesturemapping.dart';
import 'globals/connectionslist.dart';
import 'globals/locale.dart';

void main() async {
  // You can process the message here
  WidgetsFlutterBinding.ensureInitialized();
  await loadConfigurationsFromFile();

  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<String>(
      valueListenable: currentLanguage,
      builder: (context, lang, _) {
        return MaterialApp(
          debugShowCheckedModeBanner: false,
          home: Scaffold(
            appBar: AppBar(title: Text(tr('appTitle', lang))),
            body: const Padding(
              padding: EdgeInsets.all(16.0),
              child: Gesturemapping(),
            ),
          ),
        );
      },
    );
  }
}
