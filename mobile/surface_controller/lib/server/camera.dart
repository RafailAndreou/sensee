import 'package:flutter/material.dart';
import 'package:webview_flutter/webview_flutter.dart';

class VideoPage extends StatelessWidget {
  VideoPage({super.key});

  final controller = WebViewController()
    ..setJavaScriptMode(JavaScriptMode.unrestricted)
    ..loadRequest(Uri.parse('http://10.219.41.82:8000/video'));

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Video Stream')),
      body: WebViewWidget(controller: controller),
    );
  }
}
