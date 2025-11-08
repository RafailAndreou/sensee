import 'package:flutter/material.dart';
import 'package:webview_flutter/webview_flutter.dart';
import 'package:surface_controller/server/server.dart' as server_discovery;

class VideoPage extends StatefulWidget {
  const VideoPage({super.key});

  @override
  State<VideoPage> createState() => _VideoPageState();
}

class _VideoPageState extends State<VideoPage> {
  WebViewController? _controller;
  String? _loadingMessage = 'Discovering server...';

  @override
  void initState() {
    super.initState();
    _initControllerAndLoad();
  }

  Future<void> _initControllerAndLoad() async {
    // Try mDNS first, fallback to UDP
    String? discovered = await server_discovery.discoverServerSmart();

    if (discovered == null) {
      setState(() {
        _loadingMessage =
            'Could not discover server. Please make sure the server is running.';
      });
      return;
    }

    final videoUrl = discovered.replaceFirst('/configuration', '/video');

    setState(() {
      _loadingMessage = 'Loading video from $videoUrl';
      _controller = WebViewController()
        ..setJavaScriptMode(JavaScriptMode.unrestricted)
        ..loadRequest(Uri.parse(videoUrl));
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Video Stream')),
      body: _controller == null
          ? Center(child: Text(_loadingMessage ?? 'Starting...'))
          : WebViewWidget(controller: _controller!),
    );
  }
}
