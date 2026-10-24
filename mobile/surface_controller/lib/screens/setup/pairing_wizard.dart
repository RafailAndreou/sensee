import 'package:flutter/material.dart';
import 'package:surface_controller/globals/locale.dart';
import '../../server/server.dart';

class PairingWizard extends StatefulWidget {
  final String deviceType;
  const PairingWizard({super.key, required this.deviceType});

  @override
  State<PairingWizard> createState() => _PairingWizardState();
}

class _PairingWizardState extends State<PairingWizard> {
  bool _busy = false;
  List<dynamic> _flows = [];
  Map<String, dynamic>? _step;
  String? _error;
  final Map<String, TextEditingController> _controllers = {};
  final Map<String, bool> _booleans = {};
  final _formKey = GlobalKey<FormState>();

  @override
  void initState() {
    super.initState();
    _discover();
  }

  @override
  void dispose() {
    for (final controller in _controllers.values) {
      controller.dispose();
    }
    super.dispose();
  }

  Future<void> _discover() async {
    setState(() {
      _busy = true;
      _error = null;
      _step = null;
      _flows = [];
    });
    try {
      final flows = await getHADiscovered();
      if (mounted) setState(() => _flows = flows);
    } catch (error) {
      if (mounted) setState(() => _error = error.toString());
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _run(Future<Map<String, dynamic>?> Function() request) async {
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final result = await request();
      if (!mounted) return;
      if (result == null)
        throw Exception(
          'Cannot pair. Check Home Assistant connectivity and administrator permissions.',
        );
      if (result['type'] == 'create_entry') {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text(t('pairing_success_content'))));
        Navigator.pop(context);
        return;
      }
      for (final controller in _controllers.values) {
        controller.dispose();
      }
      _controllers.clear();
      _booleans.clear();
      for (final field in (result['data_schema'] as List? ?? [])) {
        final name = field['name'] as String;
        if (field['type'] == 'boolean') {
          _booleans[name] = field['default'] == true;
        } else {
          _controllers[name] = TextEditingController(
            text:
                (field['default'] ??
                        field['description']?['suggested_value'] ??
                        '')
                    .toString(),
          );
        }
      }
      setState(() => _step = result);
    } catch (error) {
      if (mounted) setState(() => _error = error.toString());
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  void _submit() {
    if (!_formKey.currentState!.validate()) return;
    final input = <String, dynamic>{..._booleans};
    for (final field in (_step!['data_schema'] as List? ?? [])) {
      final name = field['name'] as String;
      if (field['type'] == 'boolean') continue;
      final value = _controllers[name]!.text.trim();
      if (value.isEmpty && field['required'] != true) continue;
      input[name] = field['type'] == 'integer'
          ? int.parse(value)
          : field['type'] == 'float'
          ? double.parse(value)
          : value;
    }
    _run(() => submitHAPairingStep(_step!['flow_id'] as String, input));
  }

  Widget _stepForm() {
    final step = _step!;
    if (step['type'] == 'abort') {
      return Text('Pairing stopped: ${step['reason'] ?? 'unknown reason'}');
    }
    final fields = step['data_schema'] as List? ?? [];
    final supported =
        step['type'] == 'form' &&
        fields.every(
          (field) =>
              [
                'string',
                'integer',
                'float',
                'boolean',
              ].contains(field['type']) ||
              (field['type'] == null && field['selector']?['text'] != null),
        );
    if (!supported) {
      return const Text(
        'Complete this setup step in Home Assistant, then refresh devices in Sensee.',
      );
    }
    return Form(
      key: _formKey,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text(
            (step['description_placeholders']?['name'] ?? step['step_id'] ?? '')
                .toString(),
          ),
          for (final entry in (step['errors'] as Map? ?? {}).entries)
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 8),
              child: Text(
                '${entry.key}: ${entry.value}',
                style: const TextStyle(color: Colors.red),
              ),
            ),
          for (final field in fields)
            if (field['type'] == 'boolean')
              CheckboxListTile(
                title: Text(field['name'] as String),
                value: _booleans[field['name']],
                onChanged: (value) => setState(
                  () => _booleans[field['name'] as String] = value ?? false,
                ),
              )
            else
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 10),
                child: TextFormField(
                  controller: _controllers[field['name']],
                  // Android TV pairing codes may contain hexadecimal letters.
                  keyboardType: ['integer', 'float'].contains(field['type'])
                      ? TextInputType.number
                      : TextInputType.text,
                  decoration: InputDecoration(
                    border: const OutlineInputBorder(),
                    labelText: field['name'] == 'host'
                        ? 'TV IP address or hostname'
                        : field['name'] == 'pin'
                        ? 'PIN shown on TV'
                        : field['name'] as String,
                  ),
                  validator: (value) {
                    final text = value?.trim() ?? '';
                    if (field['required'] == true && text.isEmpty)
                      return 'Required';
                    if (text.isNotEmpty &&
                        field['type'] == 'integer' &&
                        int.tryParse(text) == null)
                      return 'Enter a whole number';
                    if (text.isNotEmpty &&
                        field['type'] == 'float' &&
                        double.tryParse(text) == null)
                      return 'Enter a number';
                    return null;
                  },
                ),
              ),
          ElevatedButton(onPressed: _submit, child: const Text('Continue')),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<String>(
      valueListenable: appLocale,
      builder: (context, _, child) => Scaffold(
        appBar: AppBar(title: Text(t('pairing_title'))),
        body: _busy
            ? const Center(child: CircularProgressIndicator())
            : ListView(
                padding: const EdgeInsets.all(24),
                children: [
                  if (_error != null)
                    Text(_error!, style: const TextStyle(color: Colors.red)),
                  if (_step != null)
                    _stepForm()
                  else ...[
                    if (_flows.isEmpty)
                      Text(tFormat('pairing_none_found', widget.deviceType)),
                    for (final flow in _flows)
                      Card(
                        child: ListTile(
                          leading: const Icon(Icons.devices),
                          title: Text(
                            (flow['context']?['title'] ??
                                    flow['context']?['title_placeholders']?['name'] ??
                                    flow['handler'] ??
                                    'Device')
                                .toString(),
                          ),
                          subtitle: Text((flow['handler'] ?? '').toString()),
                          onTap: () => _run(
                            () => flow['flow_id'] != null
                                ? getHAPairingFlow(flow['flow_id'] as String)
                                : startHAPairing(
                                    flow['handler'] as String,
                                    host: flow['host'] as String?,
                                  ),
                          ),
                        ),
                      ),
                    const SizedBox(height: 16),
                    ElevatedButton(
                      onPressed: () =>
                          _run(() => startHAPairing('androidtv_remote')),
                      child: const Text('Add Android TV by IP'),
                    ),
                  ],
                  TextButton(
                    onPressed: _discover,
                    child: Text(t('pairing_try_again')),
                  ),
                ],
              ),
      ),
    );
  }
}
