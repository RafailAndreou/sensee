import 'package:flutter/material.dart';

class Search extends StatefulWidget {
  final ValueChanged<String> onChanged;

  const Search({super.key, required this.onChanged});

  @override
  State<Search> createState() => _SearchState();
}

class _SearchState extends State<Search> {
  final List<String> _allBrands = const [
    'Samsung',
    'Sony',
    'LG',
    'Panasonic',
    'TCL',
    'Philips',
    'Hisense',
    'Vizio',
    'Sharp',
    'RCA',
  ];

  late List<String> _filteredBrands;
  final TextEditingController _controller = TextEditingController();

  @override
  void initState() {
    super.initState();
    _filteredBrands = List.from(_allBrands);
    _controller.addListener(_onSearchChanged);
  }

  @override
  void dispose() {
    _controller.removeListener(_onSearchChanged);
    _controller.dispose();
    super.dispose();
  }

  void _onSearchChanged() {
    final query = _controller.text.toLowerCase();
    setState(() {
      if (query.isEmpty) {
        _filteredBrands = List.from(_allBrands);
      } else {
        _filteredBrands = _allBrands
            .where((b) => b.toLowerCase().contains(query))
            .toList(growable: false);
      }
    });
    widget.onChanged(_controller.text);
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(16.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          TextField(
            controller: _controller,
            autofocus: true,
            enableInteractiveSelection: false,
            autocorrect: false,
            enableSuggestions: false,
            contextMenuBuilder: (context, editableTextState) =>
                const SizedBox.shrink(),
            decoration: InputDecoration(
              prefixIcon: const Icon(Icons.search),
              hintText: 'Search brand',
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(8.0),
              ),
            ),
          ),
          const SizedBox(height: 12.0),
          Expanded(
            child: _filteredBrands.isEmpty
                ? const Center(child: Text('No brands found'))
                : ListView.separated(
                    itemCount: _filteredBrands.length,
                    separatorBuilder: (context, index) => const Divider(),
                    itemBuilder: (context, index) {
                      final brand = _filteredBrands[index];
                      return ListTile(
                        title: Text(brand),
                        onTap: () => widget.onChanged(brand),
                      );
                    },
                  ),
          ),
        ],
      ),
    );
  }
}
