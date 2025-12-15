import 'package:flutter/material.dart';
import 'package:surface_controller/globals/locale.dart';

class LanguageToggle extends StatelessWidget {
  const LanguageToggle({super.key});

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<String>(
      valueListenable: currentLanguage,
      builder: (context, lang, _) {
        final bool isGreek = lang == 'el';
        final String asset = isGreek
            ? 'assets/language/uk.png'
            : 'assets/language/greece.png'; // Show the flag of the target language
        final String label = isGreek ? 'English' : 'Ελληνικά';

        return TextButton(
          style: TextButton.styleFrom(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
            backgroundColor: const Color(0xFFE9E9E9),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(8),
            ),
          ),
          onPressed: toggleLanguage,
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Image.asset(asset, width: 22, height: 22),
              const SizedBox(width: 8),
              Text(
                label,
                style: const TextStyle(color: Colors.black, fontSize: 11),
              ),
            ],
          ),
        );
      },
    );
  }
}
