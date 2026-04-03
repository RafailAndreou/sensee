import 'package:flutter/material.dart';
import 'package:webview_flutter/webview_flutter.dart';
import 'package:surface_controller/redesign/screens/dashboard/widgets/dashboardnavigation.dart';
import 'package:surface_controller/redesign/server/server.dart'
    as server_discovery;

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
    // Try mDNS first, fallback to UDP, then fallback to static IP
    String? discovered = await server_discovery.discoverServerSmart();

    final pageUrl = discovered == null
        ? 'http://sensee.local:8000'
        : discovered.replaceFirst('/configuration', '');

    setState(() {
      _loadingMessage = 'Loading video from $pageUrl';
      _controller = WebViewController()
        ..setJavaScriptMode(JavaScriptMode.unrestricted)
        ..loadRequest(Uri.parse(pageUrl));
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFEAEDF4),
      appBar: AppBar(
        automaticallyImplyLeading: false,
        title: const Text('Video Stream'),
      ),
      body: _controller == null
          ? Center(child: Text(_loadingMessage ?? 'Starting...'))
          : WebViewWidget(controller: _controller!),
      bottomNavigationBar: const SafeArea(
        top: false,
        child: Padding(
          padding: EdgeInsets.fromLTRB(0, 8, 0, 16),
          child: DashBoardNavigation(selectedTab: DashboardTab.camera),
        ),
      ),
    );
  }
}
