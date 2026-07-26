import 'package:flutter/material.dart';
import '../../../services/api_service.dart';

class PluginScreen extends StatefulWidget {
  final ApiService apiService;
  const PluginScreen({super.key, required this.apiService});

  @override
  State<PluginScreen> createState() => _PluginScreenState();
}

class _PluginScreenState extends State<PluginScreen> {
  Map<String, dynamic> _pluginData = {};
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    _loadPlugins();
  }

  Future<void> _loadPlugins() async {
    setState(() => _isLoading = true);
    final res = await widget.apiService.getPlugins();
    setState(() {
      _isLoading = false;
      _pluginData = res;
    });
  }

  Future<void> _reloadPlugins() async {
    setState(() => _isLoading = true);
    await widget.apiService.reloadPlugins();
    _loadPlugins();
  }

  Future<void> _togglePlugin(String name, bool enable) async {
    setState(() => _isLoading = true);
    if (enable) {
      await widget.apiService.enablePlugin(name);
    } else {
      await widget.apiService.disablePlugin(name);
    }
    _loadPlugins();
  }

  @override
  Widget build(BuildContext context) {
    final tools = _pluginData['tools'] as List? ?? [];
    final plugins = _pluginData['plugins'] as List? ?? [];

    return ListView(
      padding: const EdgeInsets.all(16.0),
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            const Text(
              'Plugins & Capabilities',
              style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: Color(0xFF4EC9B0)),
            ),
            IconButton(
              icon: const Icon(Icons.refresh, color: Color(0xFF4EC9B0)),
              onPressed: _reloadPlugins,
            ),
          ],
        ),
        const SizedBox(height: 12),

        if (_isLoading) const LinearProgressIndicator(),

        const Text('Registered Capability Tools', style: TextStyle(color: Colors.white70, fontWeight: FontWeight.bold)),
        const SizedBox(height: 8),

        if (tools.isEmpty)
          const Card(
            color: Color(0xFF252526),
            child: Padding(
              padding: EdgeInsets.all(16.0),
              child: Text('No external tools registered', style: TextStyle(color: Colors.white38)),
            ),
          )
        else
          for (var t in tools)
            Card(
              color: const Color(0xFF252526),
              margin: const EdgeInsets.symmetric(vertical: 4.0),
              child: ListTile(
                leading: const Icon(Icons.extension, color: Color(0xFF4EC9B0)),
                title: Text(t.toString(), style: const TextStyle(color: Colors.white)),
                subtitle: const Text('Built-in execution capability', style: TextStyle(color: Colors.white54, fontSize: 12)),
              ),
            ),

        const SizedBox(height: 16),
        const Text('Dynamic Subsystem Plugins', style: TextStyle(color: Colors.white70, fontWeight: FontWeight.bold)),
        const SizedBox(height: 8),

        if (plugins.isEmpty)
          const Card(
            color: Color(0xFF252526),
            child: Padding(
              padding: EdgeInsets.all(16.0),
              child: Text('No dynamic plugins loaded', style: TextStyle(color: Colors.white38)),
            ),
          )
        else
          for (var p in plugins)
            Card(
              color: const Color(0xFF252526),
              margin: const EdgeInsets.symmetric(vertical: 4.0),
              child: SwitchListTile(
                title: Text(p is Map ? (p['name'] ?? p.toString()) : p.toString(), style: const TextStyle(color: Colors.white)),
                value: p is Map ? (p['enabled'] ?? true) : true,
                activeTrackColor: const Color(0xFF4EC9B0),
                onChanged: (val) => _togglePlugin(p is Map ? (p['name'] ?? p.toString()) : p.toString(), val),
              ),
            ),
      ],
    );
  }
}
