import 'dart:async';

import 'package:flutter/material.dart';
import 'package:surface_controller/globals/connectionslist.dart';
import 'package:surface_controller/globals/global.dart';
import 'package:surface_controller/server/server.dart' as server_sync;
import 'package:surface_controller/screens/actions/actiondetails.dart';
import 'package:surface_controller/screens/brandselection/brandselection.dart';
import 'package:surface_controller/screens/dashboard/widgets/dashboardcard.dart';
import 'package:surface_controller/screens/dashboard/widgets/dashboardnavigation.dart';
import 'package:surface_controller/screens/devicetype/devicetype.dart';

class Dashboard extends StatefulWidget {
  const Dashboard({super.key});

  @override
  State<Dashboard> createState() => _DashboardState();
}

class _DashboardState extends State<Dashboard> {
  Timer? _syncTimer;
  bool _syncInFlight = false;

  @override
  void initState() {
    super.initState();
    _pullLatestServerConfigs();
    _syncTimer = Timer.periodic(
      const Duration(seconds: 2),
      (_) => _pullLatestServerConfigs(),
    );
  }

  @override
  void dispose() {
    _syncTimer?.cancel();
    super.dispose();
  }

  Future<void> _pullLatestServerConfigs() async {
    if (_syncInFlight) {
      return;
    }
    _syncInFlight = true;
    await server_sync.pullLatestConfigurationsFromServer();
    _syncInFlight = false;
  }

  @override
  Widget build(BuildContext context) {
    return Stack(
      children: [
        Column(
          children: [
            Expanded(flex: 7, child: _dashboardCards()),
            const Divider(thickness: 1, color: Colors.black87),
            const Expanded(
              flex: 1,
              child: DashBoardNavigation(selectedTab: DashboardTab.dashboard),
            ),
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
          final deviceType = _deviceTypeForConfig(config);
          return config.action.value.isNotEmpty &&
              (config.brand.value.isNotEmpty || deviceType == 'PC');
        }).toList();

        if (savedIds.isEmpty) {
          return Center(
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 24),
              child: Container(
                width: double.infinity,
                constraints: const BoxConstraints(maxWidth: 420),
                padding: const EdgeInsets.all(24),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(20),
                  boxShadow: const [
                    BoxShadow(
                      color: Color.fromARGB(24, 0, 0, 0),
                      blurRadius: 16,
                      offset: Offset(0, 8),
                    ),
                  ],
                ),
                child: const Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(
                      Icons.dashboard_customize_outlined,
                      size: 44,
                      color: Colors.blue,
                    ),
                    SizedBox(height: 12),
                    Text(
                      'Dashboard is empty',
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        fontSize: 22,
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                    SizedBox(height: 10),
                    Text(
                      'Get started by adding your first device mapping.',
                      textAlign: TextAlign.center,
                      style: TextStyle(fontSize: 15, color: Colors.black87),
                    ),
                    SizedBox(height: 16),
                    Text(
                      '1. Tap the + button\n2. Choose a device type\n3. Select a brand or smart device\n4. Pick action, gesture, and hand\n5. Save to create your first card',
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        fontSize: 14,
                        color: Colors.black54,
                        height: 1.35,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          );
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
            final connectionId = savedIds[index];
            final deviceType = _deviceTypeForConfig(config);
            return DashboardCard(
              brandName: config.brand.value,
              deviceType: deviceType,
              actionName: config.action.value,
              gestureName: config.gesture.value.isEmpty
                  ? 'Thumb and index'
                  : config.gesture.value,
              isSynced: config.isSynced,
              onTap: () {
                Navigator.of(context).push(
                  MaterialPageRoute(
                    builder: (_) => ActionDetails(
                      deviceType: deviceType,
                      brand: config.brand.value,
                      editingConnectionId: connectionId,
                      connectionType: config.connectionType.value,
                      entityId: config.entityId.value,
                    ),
                  ),
                );
              },
              onMoreTap: () =>
                  _showCardActions(context, connectionId, deviceType),
            );
          },
        );
      },
    );
  }

  String _deviceTypeForConfig(ConnectionConfig config) {
    if (config.sound.value.isEmpty) {
      return 'Tv';
    }

    return config.sound.value;
  }

  Future<void> _showCardActions(
    BuildContext context,
    int connectionId,
    String deviceType,
  ) async {
    await showModalBottomSheet<void>(
      context: context,
      builder: (sheetContext) {
        return SafeArea(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              ListTile(
                leading: const Icon(Icons.delete_outline),
                title: const Text('Delete'),
                onTap: () async {
                  Navigator.of(sheetContext).pop();
                  removeConnection(connectionId);
                  await saveConfigsToFile();
                  await server_sync.sendAllConfigurations();
                },
              ),
              if (deviceType != 'PC')
                ListTile(
                  leading: const Icon(Icons.edit_outlined),
                  title: const Text('Change brand'),
                  onTap: () {
                    Navigator.of(sheetContext).pop();
                    Navigator.of(context).push(
                      MaterialPageRoute(
                        builder: (_) => BrandSelection(
                          deviceType: deviceType,
                          editingConnectionId: connectionId,
                        ),
                      ),
                    );
                  },
                ),
            ],
          ),
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
