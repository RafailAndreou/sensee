import 'package:flutter/material.dart';
import 'buttons.dart';
import 'package:surface_controller/server/camera.dart';
import 'package:surface_controller/globals/locale.dart';

class Menu extends StatelessWidget {
  const Menu({super.key});

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<String>(
      valueListenable: currentLanguage,
      builder: (context, lang, _) {
        return Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Flexible(
              flex: 9,
              child: CustomButton(
                title: tr('gestureMapping', lang),
                icon: Image.asset(
                  'assets/gesturemapping.png',
                  width: 15,
                  height: 15,
                ),
              ),
            ),
            const Spacer(flex: 1),
            Flexible(
              flex: 9,
              child: CustomButton(
                title: tr('liveCamera', lang),
                icon: Image.asset(
                  'assets/surfacezone.png',
                  width: 20,
                  height: 20,
                ),
                onPressed: () {
                  Navigator.of(
                    context,
                  ).push(MaterialPageRoute(builder: (context) => VideoPage()));
                },
              ),
            ),
            const Spacer(),
            Flexible(
              flex: 9,
              child: CustomButton(
                title: tr('deviceActions', lang),
                icon: Image.asset(
                  'assets/deviceaction.png',
                  width: 20,
                  height: 20,
                ),
              ),
            ),
          ],
        );
      },
    );
  }
}
