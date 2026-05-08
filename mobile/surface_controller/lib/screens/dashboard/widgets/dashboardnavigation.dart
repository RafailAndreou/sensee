import 'package:flutter/material.dart';
import 'package:surface_controller/globals/locale.dart';
import 'package:surface_controller/server/camera.dart';
import 'package:surface_controller/screens/settings/settings.dart';

enum DashboardTab { dashboard, camera, settings }

class DashBoardNavigation extends StatelessWidget {
  const DashBoardNavigation({
    super.key,
    this.selectedTab = DashboardTab.dashboard,
  });

  final DashboardTab selectedTab;

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final defaultColor = isDark ? Colors.white : Colors.black87;

    return ValueListenableBuilder<String>(
      valueListenable: appLocale,
      builder: (context, _, __) {
        return Row(
          mainAxisAlignment: MainAxisAlignment.spaceAround,
          children: [
            GestureDetector(
              onTap: () {
                if (selectedTab == DashboardTab.dashboard) return;
                Navigator.of(context).popUntil((route) => route.isFirst);
              },
              child: Column(
                mainAxisSize: MainAxisSize.min,
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Image(
                    image: AssetImage(
                      selectedTab == DashboardTab.dashboard
                          ? 'assets/redesign/dashboard-active.png'
                          : 'assets/redesign/dashboard-inactive.png',
                    ),
                    color: isDark ? Colors.white : null,
                    colorBlendMode: BlendMode.srcIn,
                  ),
                  Text(
                    t('nav_dashboard'),
                    style: TextStyle(
                      fontWeight: FontWeight.w900,
                      color: defaultColor,
                    ),
                  ),
                ],
              ),
            ),
            GestureDetector(
              onTap: () {
                if (selectedTab == DashboardTab.camera) return;
                Navigator.of(
                  context,
                ).push(MaterialPageRoute(builder: (_) => const VideoPage()));
              },
              child: Column(
                mainAxisSize: MainAxisSize.min,
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Image(
                    image: const AssetImage('assets/redesign/Camera.png'),
                    color: selectedTab == DashboardTab.camera
                        ? Colors.blue
                        : (isDark ? Colors.white : null),
                    colorBlendMode: BlendMode.srcIn,
                  ),
                  Text(
                    t('nav_camera'),
                    style: TextStyle(
                      fontWeight: FontWeight.w900,
                      color: selectedTab == DashboardTab.camera
                          ? Colors.blue
                          : defaultColor,
                    ),
                  ),
                ],
              ),
            ),
            GestureDetector(
              onTap: () {
                if (selectedTab == DashboardTab.settings) return;
                Navigator.of(
                  context,
                ).push(MaterialPageRoute(builder: (_) => const Settings()));
              },
              child: Column(
                mainAxisSize: MainAxisSize.min,
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Image(
                    image: const AssetImage('assets/redesign/settings.png'),
                    color: isDark ? Colors.white : null,
                    colorBlendMode: BlendMode.srcIn,
                  ),
                  Text(
                    t('nav_settings'),
                    style: TextStyle(color: defaultColor),
                  ),
                ],
              ),
            ),
          ],
        );
      },
    );
  }
}
