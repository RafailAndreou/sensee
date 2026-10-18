import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../../server/auth_http.dart' as http;
import '../../server/discovery_service.dart';
import '../../server/config_service.dart';
import '../../globals/global.dart';
import '../../globals/connectionslist.dart';

class EngineTools extends StatefulWidget {
  const EngineTools({super.key});
  @override
  State<EngineTools> createState() => _EngineToolsState();
}

class _EngineToolsState extends State<EngineTools> {
  final _fields = <String, TextEditingController>{};
  final _name = TextEditingController();
  final _json = TextEditingController();
  final _ratio = TextEditingController();
  final _depth = TextEditingController();
  Map<String, dynamic>? _settings;
  Map<String, dynamic> _tools = {};
  List<String> _profiles = [];
  String? _reviewedServer;
  bool _calibrated = false;
  bool _busy = false;
  String? _error;
  ServerClient? _client;
  Uri _uri(String path) => Uri.parse(_client!.baseUrl).resolve(path);

  @override
  void initState() {
    super.initState();
    _run(_load);
  }

  @override
  void dispose() {
    for (final field in [..._fields.values, _name, _json, _ratio, _depth]) {
      field.dispose();
    }
    super.dispose();
  }

  Future<dynamic> _get(String path) async {
    final r = await http.get(_uri(path));
    if (r.statusCode != 200) {
      throw Exception('Request failed (${r.statusCode})');
    }
    return jsonDecode(r.body);
  }

  Future<dynamic> _post(String path, Object payload) async {
    final r = await http.post(
      _uri(path),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode(payload),
    );
    if (r.statusCode == 412) {
      throw Exception(
        'Changed on another client. Your edits are preserved. Copy them before reloading.',
      );
    }
    if (r.statusCode != 200) throw Exception(r.body);
    return jsonDecode(r.body);
  }

  Future<void> _run(Future<void> Function() action) async {
    if (_busy) return;
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await action();
    } catch (e) {
      if (mounted) setState(() => _error = '$e');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _load() async {
    _client = await getServerClient();
    if (_client == null) throw Exception('Engine unavailable');
    final settings = Map<String, dynamic>.from(await _get('/engine-settings'));
    _tools = Map<String, dynamic>.from(await _get('/engine-tools'));
    _profiles = (await _get('/profiles') as Map).keys.cast<String>().toList();
    await http.get(
      _uri('/configuration'),
      rememberRevision:
          !connectionConfigs.values.any((c) => !c.isSynced.value) &&
          pendingDeletedConnectionIds.isEmpty,
    );
    if (!mounted) return;
    _settings = settings;
    for (final entry in settings.entries) {
      if (entry.value is num) {
        _fields[entry.key] = TextEditingController(text: '${entry.value}');
      }
    }
    final calibration = settings['calibration'] as Map;
    _calibrated = calibration['enabled'] == true;
    _ratio.text = '${calibration['contactRatio']}';
    _depth.text = '${calibration['depthRatio']}';
  }

  Future<void> _refresh() async {
    _tools = Map<String, dynamic>.from(await _get('/engine-tools'));
  }

  Future<void> _save() async {
    final settings = {
      ..._settings!,
      for (final e in _fields.entries) e.key: int.parse(e.value.text),
      'calibration': {
        'enabled': _calibrated,
        'contactRatio': double.parse(_ratio.text),
        'depthRatio': double.parse(_depth.text),
      },
    };
    await _post('/engine-settings', settings);
    _settings = settings;
    await _refresh();
  }

  Future<void> _profile(String operation) async {
    var name = _name.text.trim();
    if (operation == 'export') {
      final profiles = await _get('/profiles') as Map;
      if (!profiles.containsKey(name)) {
        throw Exception('Select a saved profile');
      }
      _json.text = const JsonEncoder.withIndent(
        '  ',
      ).convert({'name': name, 'configurations': profiles[name]});
      return;
    }
    final imported = operation == 'import' ? jsonDecode(_json.text) as Map : {};
    if (name.isEmpty) name = '${imported['name'] ?? ''}';
    final result = await _post('/profiles', {
      'name': name,
      'operation': operation,
      if (operation == 'import') 'configurations': imported['configurations'],
    });
    _profiles = (result['profiles'] as Map).keys.cast<String>().toList();
    if (operation == 'load') await pullLatestConfigurationsFromServer();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Engine tools')),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          if (_busy) const LinearProgressIndicator(),
          if (_error != null)
            SelectableText(_error!, style: const TextStyle(color: Colors.red)),
          if (_settings == null && !_busy)
            TextButton(
              onPressed: () => _run(_load),
              child: const Text('Retry'),
            ),
          if (_settings != null) ...[
            const Text('Performance', style: TextStyle(fontSize: 22)),
            for (final e in _fields.entries)
              TextField(
                controller: e.value,
                enabled: !_busy,
                keyboardType: TextInputType.number,
                decoration: InputDecoration(labelText: e.key),
              ),
            const SizedBox(height: 20),
            const Text(
              'Hand contact calibration',
              style: TextStyle(fontSize: 22),
            ),
            const Text(
              'Keep one hand visible. Touch thumb to index for 30 observations, then separate them for 30 observations. Refresh diagnostics to check progress.',
            ),
            SwitchListTile(
              title: const Text('Use saved calibration'),
              value: _calibrated,
              onChanged: _busy ? null : (v) => setState(() => _calibrated = v),
            ),
            TextField(
              controller: _ratio,
              decoration: const InputDecoration(labelText: 'Contact ratio'),
              keyboardType: TextInputType.number,
            ),
            TextField(
              controller: _depth,
              decoration: const InputDecoration(labelText: 'Depth ratio'),
              keyboardType: TextInputType.number,
            ),
            Wrap(
              spacing: 8,
              children: [
                for (final phase in ['contact', 'open'])
                  OutlinedButton(
                    onPressed: _busy
                        ? null
                        : () => _run(() async {
                            await _post('/calibration/$phase', {});
                            await _refresh();
                          }),
                    child: Text(
                      phase == 'contact'
                          ? '1. Sample touching'
                          : '2. Sample separated',
                    ),
                  ),
                OutlinedButton(
                  onPressed: _busy
                      ? null
                      : () => _run(() async {
                          await _refresh();
                          final result = _tools['calibration']?['result'];
                          if (result == null) {
                            throw Exception(
                              'Complete both sampling steps first',
                            );
                          }
                          _calibrated = true;
                          _ratio.text = '${result['contactRatio']}';
                          _depth.text = '${result['depthRatio']}';
                        }),
                  child: const Text('Apply samples'),
                ),
              ],
            ),
            FilledButton(
              onPressed: _busy ? null : () => _run(_save),
              child: const Text('Save engine settings'),
            ),
            const SizedBox(height: 20),
            SwitchListTile(
              title: const Text('Session test mode'),
              subtitle: const Text(
                'Displays intended actions. Blocks device, cursor, keyboard and voice output until disabled or engine restart.',
              ),
              value: _tools['testMode'] == true,
              onChanged: _busy
                  ? null
                  : (v) => _run(() async {
                      await _post('/test-mode', {'enabled': v});
                      await _refresh();
                    }),
            ),
            const Text('Mapping conflicts', style: TextStyle(fontSize: 22)),
            ValueListenableBuilder<String?>(
              valueListenable: configurationSyncError,
              builder: (_, value, _) => Text(
                value ??
                    'Review the server version before retrying your local edits.',
              ),
            ),
            OutlinedButton(
              onPressed: _busy
                  ? null
                  : () => _run(() async {
                      final current = await _get('/configuration');
                      _reviewedServer = const JsonEncoder.withIndent(
                        '  ',
                      ).convert(current);
                    }),
              child: const Text('Review latest server mappings'),
            ),
            if (_reviewedServer != null) ...[
              const Text('Server mappings'),
              SelectableText(_reviewedServer!),
              const Text('Local mappings'),
              SelectableText(
                const JsonEncoder.withIndent('  ').convert([
                  for (final c in connectionConfigs.values)
                    {
                      'id': c.id.value,
                      'entityId': c.entityId.value,
                      'action': c.action.value,
                      'gesture': c.gesture.value,
                      'hand': c.hand.value,
                    },
                ]),
              ),
              FilledButton(
                onPressed: _busy
                    ? null
                    : () => _run(() async {
                        await sendAllConfigurations();
                        if (configurationSyncError.value != null) {
                          throw Exception(configurationSyncError.value);
                        }
                      }),
                child: const Text('Retry local mappings'),
              ),
            ],
            const Text('Mapping profiles', style: TextStyle(fontSize: 22)),
            Text('Saved: ${_profiles.join(', ')}'),
            TextField(
              controller: _name,
              decoration: const InputDecoration(labelText: 'Profile name'),
            ),
            Wrap(
              spacing: 8,
              children: [
                for (final op in ['save', 'load', 'delete', 'export', 'import'])
                  OutlinedButton(
                    onPressed: _busy ? null : () => _run(() => _profile(op)),
                    child: Text(op),
                  ),
              ],
            ),
            TextField(
              controller: _json,
              minLines: 4,
              maxLines: 10,
              decoration: const InputDecoration(
                labelText: 'Profile JSON (paste to import)',
              ),
            ),
            TextButton(
              onPressed: () =>
                  Clipboard.setData(ClipboardData(text: _json.text)),
              child: const Text('Copy JSON'),
            ),
            const SizedBox(height: 20),
            const Text('Diagnostics', style: TextStyle(fontSize: 22)),
            OutlinedButton(
              onPressed: _busy ? null : () => _run(_refresh),
              child: const Text('Refresh diagnostics'),
            ),
            SelectableText(const JsonEncoder.withIndent('  ').convert(_tools)),
          ],
        ],
      ),
    );
  }
}
