import 'package:flutter/material.dart';
import 'package:surface_controller/globals/global.dart';

class Search extends StatefulWidget {
  final ValueChanged<String> onChanged;
  const Search({super.key, required this.onChanged});

  @override
  State<Search> createState() => _SearchState();
}

class _SearchState extends State<Search> {
  final tvBrands = const [
    "Samsung",
    "Panasonic",
    "Sony",
    "LG",
    "Philips",
    "Toshiba",
    "Vizio",
  ];

  List<String> filteredTvBrands = [];

  @override
  void initState() {
    super.initState();
    filteredTvBrands = tvBrands; // show all initially (optional)
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        SearchBar(
          autoFocus: true,
          hintText: "Brand",
          onChanged: (value) {
            setState(() {
              filteredTvBrands = tvBrands
                  .where(
                    (brand) =>
                        brand.toLowerCase().contains(value.toLowerCase()),
                  )
                  .toList();
            });
          },
        ),
        Expanded(
          child: ListView.builder(
            itemCount: filteredTvBrands.length,
            itemBuilder: (context, index) {
              return ListTile(
                title: Text(filteredTvBrands[index]),
                onTap: () {
                  Navigator.of(context).popUntil((route) => route.isFirst);
                  print(filteredTvBrands[index]);
                  brand.value = filteredTvBrands[index];
                },
              );
            },
          ),
        ),
      ],
    );
  }
}
