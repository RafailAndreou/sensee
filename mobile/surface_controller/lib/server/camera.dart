import 'package:flutter/material.dart';
import 'package:webview_flutter/webview_flutter.dart';
import 'package:surface_controller/screens/dashboard/widgets/dashboardnavigation.dart';
import 'package:surface_controller/server/server.dart' as server_discovery;
import 'auth_http.dart' as auth;

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
    final client = await server_discovery.getServerClient();
    if (!mounted) return;
    if (client == null) {
      setState(() {
        _loadingMessage = 'Could not discover the Sensee server.';
      });
      return;
    }

    final baseUri = Uri.parse(client.baseUrl);
    final key = await auth.getPairingKey(baseUri);
    if (!mounted) return;
    if (key == null || !await auth.isPaired(baseUri)) {
      if (mounted) {
        setState(
          () => _loadingMessage =
              'Pair with Sensee on the dashboard to view the camera.',
        );
      }
      return;
    }
    await WebViewCookieManager().setCookie(
      WebViewCookie(
        name: 'sensee_access',
        value: key,
        domain: baseUri.host,
        path: '/',
      ),
    );
    if (!mounted) return;

    setState(() {
      _loadingMessage = 'Loading video...';
      _controller = WebViewController()
        ..setJavaScriptMode(JavaScriptMode.disabled)
        ..loadRequest(baseUri.resolve('/preview'));
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
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
