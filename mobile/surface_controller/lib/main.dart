import 'package:flutter/material.dart';
import 'package:surface_controller/globals/app_theme.dart';
import 'package:surface_controller/globals/connectionslist.dart';
import 'package:surface_controller/globals/locale.dart';
import 'package:surface_controller/screens/dashboard/dashboard.dart';
import 'package:surface_controller/screens/dashboard/widgets/server_connectivity_banner.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await loadConfigurationsFromFile();
  await initLocale();
  await initTheme();
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<String>(
      valueListenable: appLocale,
      builder: (context, _, __) {
        return ValueListenableBuilder<String>(
          valueListenable: appTheme,
          builder: (context, theme, __) {
            return MaterialApp(
              debugShowCheckedModeBanner: false,
              theme: lightTheme,
              darkTheme: darkTheme,
              themeMode:
                  theme == 'dark' ? ThemeMode.dark : ThemeMode.light,
              home: Scaffold(
                appBar: AppBar(
                  title: Text(
                    t('app_title'),
                    style: const TextStyle(fontWeight: FontWeight.w700),
                  ),
                ),
                body: const Column(
                  children: [
                    ServerConnectivityBanner(),
                    Expanded(
                      child: Padding(
                        padding: EdgeInsets.fromLTRB(16, 8, 16, 16),
                        child: Dashboard(),
                      ),
                    ),
                  ],
                ),
              ),
            );
          },
        );
      },
    );
  }
}
