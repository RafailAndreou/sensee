import 'package:flutter/material.dart';
import 'package:surface_controller/globals/locale.dart';
import 'package:surface_controller/globals/sizes.dart';
import 'package:surface_controller/screens/settings/voice_settings_screen.dart';
import 'package:surface_controller/server/config_service.dart';

class VoiceModeCard extends StatefulWidget {
  const VoiceModeCard({super.key});

  @override
  State<VoiceModeCard> createState() => _VoiceModeCardState();
}

class _VoiceModeCardState extends State<VoiceModeCard> {
  bool _enabled = false;
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final data = await loadVoiceSettings();
    if (!mounted) return;
    setState(() {
      _loading = false;
      _enabled = data?['enabled'] == true;
    });
  }

  Future<void> _toggle(bool val) async {
    setState(() => _enabled = val);
    final current = await loadVoiceSettings() ?? {};
    await saveVoiceSettings({...current, 'enabled': val});
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return ValueListenableBuilder<String>(
      valueListenable: appLocale,
      builder: (context, _, __) {
        return Container(
          width: getProportionalWidth(context, 350),
          decoration: BoxDecoration(
            color: Theme.of(context).cardColor,
            borderRadius: BorderRadius.circular(12),
            boxShadow: const [
              BoxShadow(color: Colors.black12, blurRadius: 5, offset: Offset(0, 2)),
            ],
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              // ── Toggle row ────────────────────────────────────────
              Padding(
                padding: const EdgeInsets.fromLTRB(16, 14, 16, 14),
                child: Row(
                  children: [
                    Icon(Icons.mic, size: 32, color: _enabled ? Colors.green : null),
                    const SizedBox(width: 16),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            t('voice_title'),
                            style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w600),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            t('voice_description'),
                            style: TextStyle(
                              fontSize: 13,
                              color: Theme.of(context).textTheme.bodySmall?.color,
                            ),
                          ),
                        ],
                      ),
                    ),
                    Switch(
                      value: _enabled,
                      activeColor: Colors.green,
                      onChanged: _loading ? null : _toggle,
                    ),
                  ],
                ),
              ),
              // ── Configure row ─────────────────────────────────────
              Divider(
                height: 1,
                thickness: 1,
                color: isDark
                    ? Colors.white.withOpacity(0.07)
                    : Colors.black.withOpacity(0.07),
              ),
              InkWell(
                borderRadius: const BorderRadius.vertical(bottom: Radius.circular(12)),
                onTap: () {
                  Navigator.of(context).push(
                    MaterialPageRoute(builder: (_) => const VoiceSettingsScreen()),
                  );
                },
                child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                  child: Row(
                    children: [
                      Icon(
                        Icons.tune,
                        size: 18,
                        color: Theme.of(context).textTheme.bodySmall?.color,
                      ),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Text(
                          t('voice_configure'),
                          style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w500),
                        ),
                      ),
                      Icon(
                        Icons.chevron_right,
                        color: Theme.of(context).textTheme.bodySmall?.color,
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}
