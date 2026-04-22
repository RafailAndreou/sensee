import 'package:flutter/material.dart';
import '../../server/server.dart';

class HASettings extends StatefulWidget {
  const HASettings({super.key});

  @override
  State<HASettings> createState() => _HASettingsState();
}

class _HASettingsState extends State<HASettings> {
  final TextEditingController _urlController = TextEditingController();
  final TextEditingController _tokenController = TextEditingController();
  bool _isLoading = true;
  bool _isSaving = false;

  bool _tokenAlreadySaved = false;

  @override
  void initState() {
    super.initState();
    _loadCurrentConfig();
  }

  Future<void> _loadCurrentConfig() async {
    final config = await getHAConfig();
    if (mounted && config != null) {
      setState(() {
        _urlController.text = config['url'] ?? "";
        // A non-empty masked token means a token is already stored on the server.
        _tokenAlreadySaved =
            (config['token'] as String? ?? '').isNotEmpty;
        _isLoading = false;
      });
    } else if (mounted) {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _saveConfig() async {
    final url = _urlController.text.trim();
    final token = _tokenController.text.trim();

    // Require both fields unless the token was previously saved and the user
    // chose to leave the field blank (meaning "keep the existing token").
    if (url.isEmpty || (token.isEmpty && !_tokenAlreadySaved)) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("Please enter a valid URL and Token")),
      );
      return;
    }

    setState(() => _isSaving = true);
    final success = await saveHAConfig(url, token);

    if (mounted) {
      setState(() => _isSaving = false);
      if (success) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text("Home Assistant settings saved!")),
        );
        Navigator.pop(context);
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text("Failed to save settings. Check your connection.")),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFEAEDF4),
      appBar: AppBar(
        title: const Text("Server Settings"),
      ),
      body: _isLoading
        ? const Center(child: CircularProgressIndicator())
        : SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  "Home Assistant Connection",
                  style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 8),
                const Text(
                  "Set the URL and Access Token for your Home Assistant server.",
                  style: TextStyle(color: Colors.grey),
                ),
                const SizedBox(height: 32),
                TextField(
                  controller: _urlController,
                  decoration: const InputDecoration(
                    labelText: "Home Assistant URL",
                    hintText: "http://192.168.1.50:8123",
                    border: OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 20),
                TextField(
                  controller: _tokenController,
                  obscureText: true,
                  decoration: InputDecoration(
                    labelText: "Long-Lived Access Token",
                    hintText: _tokenAlreadySaved
                        ? "Leave blank to keep existing token"
                        : "Enter your HA Token here...",
                    border: const OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 40),
                SizedBox(
                  width: double.infinity,
                  height: 56,
                  child: ElevatedButton(
                    onPressed: _isSaving ? null : _saveConfig,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.blue,
                      foregroundColor: Colors.white,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)),
                    ),
                    child: _isSaving
                      ? const CircularProgressIndicator(color: Colors.white)
                      : const Text("Save Settings", style: TextStyle(fontSize: 18)),
                  ),
                ),
              ],
            ),
          ),
    );
  }
}
