import 'package:surface_controller/globals/global.dart';

void print_config(ConnectionConfig config) {
  print(
    config.brand.value +
        " " +
        config.action.value +
        " " +
        config.gesture.value +
        " " +
        config.sound.value +
        " " +
        config.hand.value,
  );
}
