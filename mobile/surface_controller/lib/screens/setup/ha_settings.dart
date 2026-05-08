import 'package:flutter/material.dart';
import 'package:surface_controller/globals/locale.dart';
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
        _tokenAlreadySaved = (config['token'] as String? ?? '').isNotEmpty;
        _isLoading = false;
      });
    } else if (mounted) {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _saveConfig() async {
    final url = _urlController.text.trim();
    final token = _tokenController.text.trim();

    if (url.isEmpty || (token.isEmpty && !_tokenAlreadySaved)) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(t('ha_err_missing_fields'))),
      );
      return;
    }

    setState(() => _isSaving = true);
    final success = await saveHAConfig(url, token);

    if (mounted) {
      setState(() => _isSaving = false);
      if (success) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(t('ha_success'))),
        );
        Navigator.pop(context);
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(t('ha_err_save_failed'))),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<String>(
      valueListenable: appLocale,
      builder: (context, _, __) {
        return Scaffold(
          appBar: AppBar(
            title: Text(
              t('ha_title'),
              style: const TextStyle(fontWeight: FontWeight.w700),
            ),
          ),
          body: _isLoading
              ? const Center(child: CircularProgressIndicator())
              : SingleChildScrollView(
                  padding: const EdgeInsets.all(24),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        t('ha_section_title'),
                        style: const TextStyle(
                          fontSize: 22,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        t('ha_section_subtitle'),
                        style: const TextStyle(color: Colors.grey),
                      ),
                      const SizedBox(height: 32),
                      TextField(
                        controller: _urlController,
                        decoration: InputDecoration(
                          labelText: t('ha_url_label'),
                          hintText: "http://192.168.1.50:8123",
                          border: const OutlineInputBorder(),
                        ),
                      ),
                      const SizedBox(height: 20),
                      TextField(
                        controller: _tokenController,
                        obscureText: true,
                        decoration: InputDecoration(
                          labelText: t('ha_token_label'),
                          hintText: _tokenAlreadySaved
                              ? t('ha_token_hint_existing')
                              : t('ha_token_hint_new'),
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
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(15),
                            ),
                          ),
                          child: _isSaving
                              ? const CircularProgressIndicator(
                                  color: Colors.white,
                                )
                              : Text(
                                  t('ha_save'),
                                  style: const TextStyle(fontSize: 18),
                                ),
                        ),
                      ),
                    ],
                  ),
                ),
        );
      },
    );
  }
}
