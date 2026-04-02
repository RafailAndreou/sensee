import 'package:flutter/material.dart';
import 'package:surface_controller/redesign/screens/dashboard/widgets/dashboardcard.dart';
import 'package:surface_controller/redesign/screens/dashboard/widgets/dashboardnavigation.dart';
import 'package:surface_controller/redesign/screens/devicetype/devicetype.dart';

class Dashboard extends StatelessWidget {
  const Dashboard({super.key});

  @override
  Widget build(BuildContext context) {
    return Stack(
      children: [
        Column(
          children: const [
            Expanded(flex: 2, child: DashboardCard()),
            Expanded(flex: 5, child: SizedBox()),
            Divider(thickness: 1, color: Colors.black87),
            Expanded(flex: 1, child: DashBoardNavigation()),
            SizedBox(height: 32),
          ],
        ),
        Positioned(bottom: 150, right: 18, child: _settingsButton(context)),
      ],
    );
  }

  Widget _settingsButton(BuildContext context) {
    return IconButton.filled(
      onPressed: () {
        Navigator.of(
          context,
        ).push(MaterialPageRoute(builder: (_) => const DeviceType()));
        // TODO: Hook up settings action.
      },
      icon: const Icon(Icons.add),
      style: IconButton.styleFrom(
        iconSize: 30,
        backgroundColor: Colors.blue,
        foregroundColor: Colors.white,
      ),
    );
  }
}
