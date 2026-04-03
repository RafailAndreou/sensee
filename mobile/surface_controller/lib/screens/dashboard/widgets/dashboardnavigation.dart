import 'package:flutter/material.dart';
import 'package:surface_controller/server/camera.dart';

enum DashboardTab { dashboard, camera, settings }

class DashBoardNavigation extends StatelessWidget {
  const DashBoardNavigation({
    super.key,
    this.selectedTab = DashboardTab.dashboard,
  });

  final DashboardTab selectedTab;

  @override
  Widget build(BuildContext context) {
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
              ),
              Text(
                "Dashboard",
                style: TextStyle(
                  fontWeight: FontWeight.w900,
                  color: selectedTab == DashboardTab.dashboard
                      ? Colors.black
                      : Colors.black87,
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
                color: selectedTab == DashboardTab.camera ? Colors.blue : null,
              ),
              Text(
                "Camera",
                style: TextStyle(
                  fontWeight: FontWeight.w900,
                  color: selectedTab == DashboardTab.camera
                      ? Colors.blue
                      : Colors.black,
                ),
              ),
            ],
          ),
        ),
        GestureDetector(
          onTap: () {
            // Handle settings tap
          },
          child: Column(
            mainAxisSize: MainAxisSize.min,
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Image(image: AssetImage("assets/redesign/settings.png")),
              const Text("Settings"),
            ],
          ),
        ),
      ],
    );
  }
}
