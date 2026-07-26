import 'package:flutter/material.dart';
import '../../../services/api_service.dart';

class SettingsScreen extends StatefulWidget {
  final ApiService apiService;
  const SettingsScreen({super.key, required this.apiService});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  final TextEditingController _apiKeyController = TextEditingController();
  final TextEditingController _modelController = TextEditingController();
  final TextEditingController _backendUrlController = TextEditingController();

  String _selectedProvider = 'mock';
  double _temperature = 0.7;
  bool _memoryEnabled = true;
  String _loggingLevel = 'INFO';
  String _theme = 'dark';
  bool _isLoading = false;
  String? _statusMessage;

  @override
  void initState() {
    super.initState();
    _backendUrlController.text = widget.apiService.baseUrl;
    _loadSettings();
  }

  Future<void> _loadSettings() async {
    setState(() => _isLoading = true);
    final res = await widget.apiService.getSettings();
    setState(() {
      _isLoading = false;
      _selectedProvider = res['provider'] ?? 'mock';
      _modelController.text = res['model'] ?? 'z-ai/glm-5.2';
      _temperature = (res['temperature'] as num?)?.toDouble() ?? 0.7;
      _memoryEnabled = res['memory_enabled'] ?? true;
      _loggingLevel = res['logging_level'] ?? 'INFO';
      _theme = res['theme'] ?? 'dark';
    });
  }

  Future<void> _saveSettings() async {
    setState(() {
      _isLoading = true;
      _statusMessage = null;
    });

    final newBackendUrl = _backendUrlController.text.trim();
    if (newBackendUrl.isNotEmpty) {
      await widget.apiService.setCustomBaseUrl(newBackendUrl);
    }

    final payload = <String, dynamic>{
      'provider': _selectedProvider,
      'model': _modelController.text.trim(),
      'temperature': _temperature,
      'memory_enabled': _memoryEnabled,
      'logging_level': _loggingLevel,
      'theme': _theme,
    };

    if (_apiKeyController.text.trim().isNotEmpty) {
      payload['api_key'] = _apiKeyController.text.trim();
    }

    final res = await widget.apiService.updateSettings(payload);

    setState(() {
      _isLoading = false;
      if (res['success'] == true) {
        _statusMessage = 'Settings saved and persisted successfully!';
        _apiKeyController.clear();
      } else {
        _statusMessage = 'Error saving settings: ${res['error']}';
      }
    });

    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(_statusMessage ?? 'Settings updated')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(16.0),
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            const Text(
              'Alfa COS Configuration',
              style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: Color(0xFF4EC9B0)),
            ),
            if (_isLoading) const CircularProgressIndicator(strokeWidth: 2),
          ],
        ),
        const SizedBox(height: 16),

        Card(
          color: const Color(0xFF252526),
          child: Padding(
            padding: const EdgeInsets.all(12.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('Backend Server URL', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
                const SizedBox(height: 4),
                const Text(
                  'Auto-detected: 10.0.2.2 (Emulator) / 127.0.0.1 (Desktop)',
                  style: TextStyle(color: Colors.white54, fontSize: 11),
                ),
                const SizedBox(height: 8),
                TextField(
                  controller: _backendUrlController,
                  style: const TextStyle(color: Colors.white),
                  decoration: const InputDecoration(
                    hintText: 'e.g. http://10.0.2.2:8000',
                    border: OutlineInputBorder(),
                  ),
                ),
              ],
            ),
          ),
        ),

        const SizedBox(height: 12),

        Card(
          color: const Color(0xFF252526),
          child: Padding(
            padding: const EdgeInsets.all(12.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('AI Provider', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
                DropdownButton<String>(
                  value: _selectedProvider,
                  isExpanded: true,
                  dropdownColor: const Color(0xFF252526),
                  style: const TextStyle(color: Colors.white),
                  items: const [
                    DropdownMenuItem(value: 'mock', child: Text('Mock Provider (Offline)')),
                    DropdownMenuItem(value: 'nvidia', child: Text('NVIDIA Build API')),
                    DropdownMenuItem(value: 'openrouter', child: Text('OpenRouter API')),
                    DropdownMenuItem(value: 'ollama', child: Text('Ollama Local API')),
                  ],
                  onChanged: (val) {
                    if (val != null) setState(() => _selectedProvider = val);
                  },
                ),
              ],
            ),
          ),
        ),

        const SizedBox(height: 12),

        Card(
          color: const Color(0xFF252526),
          child: Padding(
            padding: const EdgeInsets.all(12.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('Model Name', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
                const SizedBox(height: 8),
                TextField(
                  controller: _modelController,
                  style: const TextStyle(color: Colors.white),
                  decoration: const InputDecoration(
                    border: OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 12),
                const Text('API Key (Masked on Save)', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
                const SizedBox(height: 8),
                TextField(
                  controller: _apiKeyController,
                  obscureText: true,
                  style: const TextStyle(color: Colors.white),
                  decoration: const InputDecoration(
                    hintText: 'Enter API Key to update...',
                    border: OutlineInputBorder(),
                  ),
                ),
              ],
            ),
          ),
        ),

        const SizedBox(height: 12),

        Card(
          color: const Color(0xFF252526),
          child: Padding(
            padding: const EdgeInsets.all(12.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Temperature: ${_temperature.toStringAsFixed(2)}',
                  style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
                ),
                Slider(
                  value: _temperature,
                  min: 0.0,
                  max: 1.0,
                  divisions: 20,
                  activeColor: const Color(0xFF4EC9B0),
                  onChanged: (val) => setState(() => _temperature = val),
                ),
              ],
            ),
          ),
        ),

        const SizedBox(height: 12),

        Card(
          color: const Color(0xFF252526),
          child: Column(
            children: [
              SwitchListTile(
                title: const Text('Memory Manager Enabled', style: TextStyle(color: Colors.white)),
                subtitle: const Text('Store and retrieve episodic turn history', style: TextStyle(color: Colors.white54, fontSize: 12)),
                value: _memoryEnabled,
                activeTrackColor: const Color(0xFF4EC9B0),
                onChanged: (val) => setState(() => _memoryEnabled = val),
              ),
              ListTile(
                title: const Text('Logging Level', style: TextStyle(color: Colors.white)),
                trailing: DropdownButton<String>(
                  value: _loggingLevel,
                  dropdownColor: const Color(0xFF252526),
                  style: const TextStyle(color: Colors.white),
                  items: const [
                    DropdownMenuItem(value: 'DEBUG', child: Text('DEBUG')),
                    DropdownMenuItem(value: 'INFO', child: Text('INFO')),
                    DropdownMenuItem(value: 'WARNING', child: Text('WARNING')),
                    DropdownMenuItem(value: 'ERROR', child: Text('ERROR')),
                  ],
                  onChanged: (val) {
                    if (val != null) setState(() => _loggingLevel = val);
                  },
                ),
              ),
            ],
          ),
        ),

        const SizedBox(height: 20),

        ElevatedButton.icon(
          onPressed: _saveSettings,
          icon: const Icon(Icons.save),
          label: const Text('Save Settings'),
          style: ElevatedButton.styleFrom(
            backgroundColor: const Color(0xFF4EC9B0),
            foregroundColor: Colors.black,
            padding: const EdgeInsets.symmetric(vertical: 14),
          ),
        ),
      ],
    );
  }
}
