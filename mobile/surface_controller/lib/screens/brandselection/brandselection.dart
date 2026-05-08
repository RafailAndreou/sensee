import 'package:flutter/material.dart';
import 'dart:async';
import 'package:surface_controller/globals/connectionslist.dart';
import 'package:surface_controller/globals/global.dart';
import 'package:surface_controller/globals/locale.dart';
import 'package:surface_controller/server/server.dart' as server_sync;
import '../actions/actiondetails.dart';

class BrandSelection extends StatefulWidget {
  final String deviceType;
  final int? editingConnectionId;

  const BrandSelection({
    super.key,
    required this.deviceType,
    this.editingConnectionId,
  });

  @override
  State<BrandSelection> createState() => _BrandSelectionState();
}

class _BrandSelectionState extends State<BrandSelection> {
  late List<String> allBrands;
  late List<String> filteredBrands;
  final TextEditingController _searchController = TextEditingController();

  @override
  void initState() {
    super.initState();
    allBrands = _getBrandsForDeviceType(widget.deviceType);
    filteredBrands = List.from(allBrands);
    _searchController.addListener(_filterBrands);
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  List<String> _getBrandsForDeviceType(String deviceType) {
    switch (deviceType.toLowerCase()) {
      case 'tv':
        return [
          'Samsung',
          'LG',
          'Sony',
          'Panasonic',
          'Philips',
          'TCL',
          'Hisense',
          'Sharp',
          'Vizio',
          'Toshiba',
        ];
      case 'ac':
        return [
          'Daikin',
          'Carrier',
          'Trane',
          'Midea',
          'Gree',
          'AUX',
          'Haier',
          'Panasonic',
          'LG',
          'Whirlpool',
        ];
      case 'light':
        return [
          'Philips Hue',
          'Wyze',
          'LIFX',
          'Nanoleaf',
          'Meross',
          'Yeelight',
          'LEDVANCE',
          'Innr',
          'Elgato',
          'Eve',
        ];
      case 'fan':
        return [
          'Dyson',
          'Honeywell',
          'Lasko',
          'Vornado',
          'Westinghouse',
          'Dreo',
          'Midea',
          'Haier',
          'Delonghi',
          'Domo',
        ];
      default:
        return [];
    }
  }

  void _filterBrands() {
    final query = _searchController.text.toLowerCase();
    setState(() {
      filteredBrands = allBrands
          .where((brand) => brand.toLowerCase().contains(query))
          .toList();
    });
  }

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<String>(
      valueListenable: appLocale,
      builder: (context, _, __) {
        return Scaffold(
          backgroundColor: const Color.fromARGB(255, 255, 255, 255),
          appBar: AppBar(
            leading: IconButton(
              icon: const Icon(Icons.arrow_back),
              onPressed: () => Navigator.of(context).pop(),
            ),
            title: Text(
              tFormat('brand_screen_title', widget.deviceType),
              style: const TextStyle(fontWeight: FontWeight.w900),
            ),
          ),
          body: Column(
            children: [
              Padding(
                padding: const EdgeInsets.all(12.0),
                child: TextField(
                  controller: _searchController,
                  decoration: InputDecoration(
                    hintText: t('brand_search_hint'),
                    prefixIcon: const Icon(Icons.search),
                    suffixIcon: _searchController.text.isNotEmpty
                        ? IconButton(
                            icon: const Icon(Icons.clear),
                            onPressed: () {
                              _searchController.clear();
                            },
                          )
                        : null,
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(8),
                    ),
                  ),
                ),
              ),
              Expanded(
                child: filteredBrands.isEmpty
                    ? Center(
                        child: Text(
                          tFormat(
                            'brand_not_found',
                            _searchController.text,
                          ),
                        ),
                      )
                    : ListView.builder(
                        itemCount: filteredBrands.length,
                        itemBuilder: (context, index) {
                          return ListTile(
                            title: Text(filteredBrands[index]),
                            onTap: () async {
                              if (widget.editingConnectionId != null) {
                                final config = getConnectionConfig(
                                  widget.editingConnectionId!,
                                );
                                config.brand.value = filteredBrands[index];
                                connectionsList.value = List.from(
                                  connectionsList.value,
                                );
                                saveConfigsToFile();

                                if (!mounted) return;
                                Navigator.of(
                                  context,
                                ).popUntil((route) => route.isFirst);

                                unawaited(server_sync.sendAllConfigurations());
                                return;
                              }

                              Navigator.of(context).push(
                                MaterialPageRoute(
                                  builder: (_) => ActionDetails(
                                    deviceType: widget.deviceType,
                                    brand: filteredBrands[index],
                                  ),
                                ),
                              );
                            },
                          );
                        },
                      ),
              ),
            ],
          ),
        );
      },
    );
  }
}
