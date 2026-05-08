import 'dart:async';

import 'package:flutter/material.dart';
import 'package:surface_controller/globals/connectionslist.dart';
import 'package:surface_controller/globals/global.dart';
import 'package:surface_controller/globals/locale.dart';
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
  Timer? _swapAnimTimer;
  bool _syncInFlight = false;
  int? _dragOverIndex;
  Set<int> _justSwappedIds = {};

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
    _swapAnimTimer?.cancel();
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
          return ValueListenableBuilder<String>(
            valueListenable: appLocale,
            builder: (context, _, __) {
              return Center(
                child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 24),
                  child: Container(
                    width: double.infinity,
                    constraints: const BoxConstraints(maxWidth: 420),
                    padding: const EdgeInsets.all(24),
                    decoration: BoxDecoration(
                      color: Theme.of(context).cardColor,
                      borderRadius: BorderRadius.circular(20),
                      boxShadow: const [
                        BoxShadow(
                          color: Color.fromARGB(24, 0, 0, 0),
                          blurRadius: 16,
                          offset: Offset(0, 8),
                        ),
                      ],
                    ),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        const Icon(
                          Icons.dashboard_customize_outlined,
                          size: 44,
                          color: Colors.blue,
                        ),
                        const SizedBox(height: 12),
                        Text(
                          t('dashboard_empty_title'),
                          textAlign: TextAlign.center,
                          style: const TextStyle(
                            fontSize: 22,
                            fontWeight: FontWeight.w800,
                          ),
                        ),
                        const SizedBox(height: 10),
                        Text(
                          t('dashboard_empty_subtitle'),
                          textAlign: TextAlign.center,
                          style: const TextStyle(fontSize: 15),
                        ),
                        const SizedBox(height: 16),
                        Text(
                          t('dashboard_empty_steps'),
                          textAlign: TextAlign.center,
                          style: TextStyle(
                            fontSize: 14,
                            color: Theme.of(
                              context,
                            ).textTheme.bodySmall?.color,
                            height: 1.35,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              );
            },
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

            final card = DashboardCard(
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

            return DragTarget<int>(
              onWillAcceptWithDetails: (details) =>
                  details.data != connectionId,
              onAcceptWithDetails: (details) {
                final fromIndex = savedIds.indexOf(details.data);
                _swapCards(fromIndex, index, savedIds);
              },
              onLeave: (_) => setState(() => _dragOverIndex = null),
              onMove: (_) {
                if (_dragOverIndex != index) {
                  setState(() => _dragOverIndex = index);
                }
              },
              builder: (context, candidateData, _) {
                final isHovered =
                    _dragOverIndex == index && candidateData.isNotEmpty;
                return LongPressDraggable<int>(
                  data: connectionId,
                  feedback: Material(
                    color: Colors.transparent,
                    child: Opacity(
                      opacity: 0.9,
                      child: Transform.scale(scale: 1.05, child: card),
                    ),
                  ),
                  childWhenDragging: Opacity(opacity: 0.3, child: card),
                  child: _justSwappedIds.contains(connectionId)
                      ? TweenAnimationBuilder<double>(
                          key: ValueKey('swap_$connectionId'),
                          tween: Tween(begin: 0.82, end: 1.0),
                          duration: const Duration(milliseconds: 400),
                          curve: Curves.elasticOut,
                          builder: (_, scale, child) =>
                              Transform.scale(scale: scale, child: child),
                          child: card,
                        )
                      : AnimatedScale(
                          scale: isHovered ? 1.04 : 1.0,
                          duration: const Duration(milliseconds: 150),
                          child: card,
                        ),
                );
              },
            );
          },
        );
      },
    );
  }

  void _swapCards(int fromSavedIndex, int toSavedIndex, List<int> savedIds) {
    final fromId = savedIds[fromSavedIndex];
    final toId = savedIds[toSavedIndex];
    final fullList = List<int>.from(connectionsList.value);
    final fullFromIndex = fullList.indexOf(fromId);
    final fullToIndex = fullList.indexOf(toId);
    fullList[fullFromIndex] = toId;
    fullList[fullToIndex] = fromId;

    _swapAnimTimer?.cancel();
    _swapAnimTimer = Timer(const Duration(milliseconds: 450), () {
      if (mounted) setState(() => _justSwappedIds = {});
    });

    setState(() {
      _dragOverIndex = null;
      _justSwappedIds = {fromId, toId};
    });
    connectionsList.value = fullList;
    saveConfigsToFile();
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
                title: Text(t('dashboard_delete')),
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
                  title: Text(t('dashboard_change_brand')),
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
