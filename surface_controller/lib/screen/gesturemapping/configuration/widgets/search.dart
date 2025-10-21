import 'package:flutter/material.dart';

class Search extends StatelessWidget {
  final ValueChanged<String> onChanged;

  const Search({super.key, required this.onChanged});

  @override
  Widget build(BuildContext context) {
    return SearchBar(onChanged: onChanged, autoFocus: true, hintText: "Brand");
  }
}
