import 'package:flutter/material.dart';
import 'package:surface_controller/globals/sizes.dart';

class Gesturesettings extends StatefulWidget {
  const Gesturesettings({super.key});

  @override
  State<Gesturesettings> createState() => _GesturesettingsState();
}

class _GesturesettingsState extends State<Gesturesettings> {
  bool _wakeEnabled = false;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFEAEDF4),
      appBar: AppBar(
        title: const Text(
          "Gesture Settings",
          style: TextStyle(fontSize: 27, fontWeight: FontWeight.w500),
        ),
      ),
      body: Container(
        // container takes 90% of the body
        margin: const EdgeInsets.all(16),
        width: getProportionalHeight(context, 500),
        height: getProportionalHeight(context, 600),
        // use decoration to keep rounded corners and background color
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: Colors.black12, width: 2),
        ),
        padding: const EdgeInsets.all(24),
        child: SingleChildScrollView(
          child: Column(
            children: [
              const Text(
                'Wake-up Gesture',
                style: TextStyle(fontSize: 24, fontWeight: FontWeight.w700),
              ),
              const SizedBox(height: 16),
              Row(
                children: [
                  const Icon(Icons.back_hand, size: 40),
                  const SizedBox(width: 16),
                  Expanded(
                    child: Text(
                      "Enable Wake-up Gesture",
                      style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                  ),
                  // toggle switch similar to the provided image
                  Switch.adaptive(
                    value: _wakeEnabled,
                    activeColor: Colors.white,
                    activeTrackColor: Colors.blue,
                    onChanged: (val) {
                      setState(() {
                        _wakeEnabled = val;
                      });
                    },
                  ),
                ],
              ),
              SizedBox(height: 70),
              _scrollDownButton(context),
            ],
          ),
        ),
      ),
    );
  }

  Widget _scrollDownButton(BuildContext context) {
    return FractionallySizedBox(
      widthFactor: 1,
      child: Container(
        height: 65,
        padding: const EdgeInsets.symmetric(horizontal: 13),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: Colors.black, width: 3),
        ),
        child: DropdownButtonHideUnderline(
          child: DropdownButton<String>(
            isExpanded: true,
            borderRadius: BorderRadius.circular(12),
            icon: const Icon(Icons.keyboard_arrow_down_rounded),
            onChanged: (value) => print("Selected: $value"),
            value: "Open Hand",
            items: [
              DropdownMenuItem(value: "Open Hand", child: Text("Open Hand")),
              DropdownMenuItem(
                value: "Closed Fist",
                child: Text("Closed Fist"),
              ),
              DropdownMenuItem(
                value: "Thumbs+Index",
                child: Text("Thumbs + Index"),
              ),
              DropdownMenuItem(
                value: "Middle+Thumb",
                child: Text("Middle + Thumb"),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
