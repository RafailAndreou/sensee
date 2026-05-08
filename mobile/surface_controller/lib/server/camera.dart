import 'package:flutter/material.dart';
import 'package:webview_flutter/webview_flutter.dart';
import 'package:surface_controller/screens/dashboard/widgets/dashboardnavigation.dart';
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
    final client = await server_discovery.getServerClient();
    if (client == null) {
      setState(() {
        _loadingMessage = 'Could not discover the Sensee server.';
      });
      return;
    }

    final pageUrl = client.videoUri.toString();
    final html = _buildVideoPageHtml(pageUrl);

    setState(() {
      _loadingMessage = 'Loading video from $pageUrl';
      _controller = WebViewController()
        ..setJavaScriptMode(JavaScriptMode.unrestricted)
        ..loadHtmlString(html);
    });
  }

  String _buildVideoPageHtml(String streamUrl) {
    return '''
<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8" />
    <meta
      name="viewport"
      content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no"
    />
    <style>
      html, body {
        margin: 0;
        width: 100%;
        height: 100%;
        background: #000;
        overflow: hidden;
      }
      img {
        width: 100vw;
        height: 100vh;
        object-fit: contain;
        display: block;
      }
    </style>
  </head>
  <body>
    <img src="$streamUrl" alt="Sensee live preview" />
  </body>
</html>
''';
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
