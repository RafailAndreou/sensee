import 'package:flutter/material.dart';
import 'package:surface_controller/redesign/globals/connectionslist.dart';
import 'package:surface_controller/redesign/globals/global.dart';
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
          children: [
            Expanded(flex: 7, child: _dashboardCards()),
            const Divider(thickness: 1, color: Colors.black87),
            const Expanded(flex: 1, child: DashBoardNavigation()),
            const SizedBox(height: 32),
          ],
        ),
        Positioned(bottom: 150, right: 18, child: _settingsButton(context)),
      ],
    );
  }

  Widget _dashboardCards() {
    return ValueListenableBuilder<List<int>>(
      valueListenable: connectionsList,
      builder: (context, ids, _) {
        final savedIds = ids.where((id) {
          final config = getConnectionConfig(id);
          return config.brand.value.isNotEmpty &&
              config.action.value.isNotEmpty;
        }).toList();

        if (savedIds.isEmpty) {
          return const Center(child: DashboardCard());
        }

        return GridView.builder(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 8),
          itemCount: savedIds.length,
          gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
            crossAxisCount: 2,
            crossAxisSpacing: 12,
            mainAxisSpacing: 12,
            childAspectRatio: 0.95,
          ),
          itemBuilder: (context, index) {
            final config = getConnectionConfig(savedIds[index]);
            return DashboardCard(
              brandName: config.brand.value,
              deviceType: config.sound.value.isEmpty
                  ? 'Tv'
                  : config.sound.value,
              actionName: config.action.value,
              gestureName: config.gesture.value.isEmpty
                  ? 'Thumb and index'
                  : config.gesture.value,
            );
          },
        );
      },
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
