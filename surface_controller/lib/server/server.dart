import 'dart:convert';
import 'dart:io';
import '../irblaster.dart';

Future<String> waitForMessage() async {
  final server = await HttpServer.bind(InternetAddress.anyIPv4, 8080);
  print('Listening on port ${server.port}');

  await for (final req in server) {
    if (req.method == 'POST' && req.uri.path == '/receive') {
      final body = await utf8.decoder.bind(req).join();
      final data = jsonDecode(body) as Map<String, dynamic>;
      final message = data['message'].toString();
      print('📩 Received: $message');

      if (message == "up") {
        print('🔔 Calling blast() because message == up');
        blast(up);
      } else if (message == "down") {
        print('🔔 Calling blast() because message == down');
        blast(down);
      }

      req.response.statusCode = 200;
      req.response.write('OK');
      await req.response.close();
    } else {
      req.response.statusCode = 404;
      await req.response.close();
    }
  }

  // Just in case — should never really get here
  return '';
}

void main() async {
  String msg = await waitForMessage();
  print('✅ The received message was: $msg');
  // You can do whatever you want with `msg` here
}
