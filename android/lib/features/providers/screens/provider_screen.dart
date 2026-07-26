import 'package:flutter/material.dart';
import '../../../services/api_service.dart';

class ProviderScreen extends StatefulWidget {
  final ApiService apiService;
  const ProviderScreen({super.key, required this.apiService});

  @override
  State<ProviderScreen> createState() => _ProviderScreenState();
}

class _ProviderScreenState extends State<ProviderScreen> {
  Map<String, dynamic> _providerData = {};
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    _loadProviders();
  }

  Future<void> _loadProviders() async {
    setState(() => _isLoading = true);
    final res = await widget.apiService.getProviders();
    setState(() {
      _isLoading = false;
      _providerData = res;
    });
  }

  Future<void> _switchProvider(String name) async {
    setState(() => _isLoading = true);
    await widget.apiService.switchProvider(name);
    await _loadProviders();
  }

  @override
  Widget build(BuildContext context) {
    final activeProvider = _providerData['active_provider'] ?? 'mock';
    final activeModel = _providerData['active_model'] ?? 'z-ai/glm-5.2';
    final connTest = _providerData['connection_test'] as Map? ?? {};
    final validProviders = _providerData['valid_providers'] as List? ?? ['mock', 'nvidia', 'openrouter', 'ollama'];

    return ListView(
      padding: const EdgeInsets.all(16.0),
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            const Text(
              'Provider Manager',
              style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: Color(0xFF4EC9B0)),
            ),
            IconButton(
              icon: const Icon(Icons.refresh, color: Color(0xFF4EC9B0)),
              onPressed: _loadProviders,
            ),
          ],
        ),
        const SizedBox(height: 12),

        // Active Provider Summary Card
        Card(
          color: const Color(0xFF252526),
          child: Padding(
            padding: const EdgeInsets.all(16.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    const Icon(Icons.check_circle, color: Color(0xFF4EC9B0)),
                    const SizedBox(width: 8),
                    Text(
                      'Active: ${activeProvider.toUpperCase()}',
                      style: const TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                Text('Model: $activeModel', style: const TextStyle(color: Colors.white70)),
                const SizedBox(height: 4),
                Text(
                  'Connection: ${connTest['connected'] == true ? 'Connected' : 'Offline / Test Failed'}',
                  style: TextStyle(
                    color: connTest['connected'] == true ? Colors.green : Colors.orangeAccent,
                  ),
                ),
                if (connTest['latency_ms'] != null)
                  Text('Latency: ${connTest['latency_ms']} ms', style: const TextStyle(color: Colors.white54, fontSize: 12)),
              ],
            ),
          ),
        ),

        const SizedBox(height: 16),
        const Text('Available Providers', style: TextStyle(color: Colors.white70, fontWeight: FontWeight.bold)),
        const SizedBox(height: 8),

        if (_isLoading) const LinearProgressIndicator(),

        for (var p in validProviders) ...[
          Card(
            color: p.toString() == activeProvider ? const Color(0x4D0E639C) : const Color(0xFF252526),
            margin: const EdgeInsets.symmetric(vertical: 4.0),
            child: ListTile(
              leading: Icon(
                Icons.psychology,
                color: p.toString() == activeProvider ? const Color(0xFF4EC9B0) : Colors.white38,
              ),
              title: Text(
                p.toString().toUpperCase(),
                style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
              ),
              subtitle: Text(
                p.toString() == activeProvider ? 'Currently active backend' : 'Tap to switch provider',
                style: TextStyle(color: p.toString() == activeProvider ? const Color(0xFF4EC9B0) : Colors.white54, fontSize: 12),
              ),
              trailing: p.toString() == activeProvider
                  ? const Icon(Icons.check, color: Color(0xFF4EC9B0))
                  : ElevatedButton(
                      onPressed: () => _switchProvider(p.toString()),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(0xFF252526),
                        foregroundColor: const Color(0xFF4EC9B0),
                      ),
                      child: const Text('Switch'),
                    ),
            ),
          ),
        ],
      ],
    );
  }
}
