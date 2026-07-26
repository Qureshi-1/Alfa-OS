import 'package:flutter/material.dart';
import '../../../services/api_service.dart';

class DeveloperScreen extends StatefulWidget {
  final ApiService apiService;
  const DeveloperScreen({super.key, required this.apiService});

  @override
  State<DeveloperScreen> createState() => _DeveloperScreenState();
}

class _DeveloperScreenState extends State<DeveloperScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  Map<String, dynamic> _statusData = {};
  List<String> _logs = [];
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    _loadDeveloperData();
  }

  Future<void> _loadDeveloperData() async {
    setState(() => _isLoading = true);
    final statusRes = await widget.apiService.getStatus();
    final logsRes = await widget.apiService.getLogs(lines: 100);

    setState(() {
      _isLoading = false;
      _statusData = statusRes;
      _logs = (logsRes['logs'] as List?)?.map((e) => e.toString()).toList() ?? [];
    });
  }

  void _testEchoWorker() async {
    setState(() => _isLoading = true);
    final res = await widget.apiService.executeWorker('echo_worker', {'message': 'Telemetry Ping from Flutter'});
    _loadDeveloperData();
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('EchoWorker Result: ${res['output']}')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        // Tab Header
        TabBar(
          controller: _tabController,
          indicatorColor: const Color(0xFF4EC9B0),
          labelColor: const Color(0xFF4EC9B0),
          unselectedLabelColor: Colors.white54,
          tabs: const [
            Tab(icon: Icon(Icons.analytics), text: 'Cognitive Stats'),
            Tab(icon: Icon(Icons.terminal), text: 'Session Logs'),
          ],
        ),

        if (_isLoading) const LinearProgressIndicator(),

        Expanded(
          child: TabBarView(
            controller: _tabController,
            children: [
              _buildStatsInspector(),
              _buildLogViewer(),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildStatsInspector() {
    final executive = _statusData['executive'] as Map? ?? {};
    final reflection = _statusData['reflection'] as Map? ?? {};
    final learning = _statusData['learning'] as Map? ?? {};
    final memory = _statusData['memory'] as Map? ?? {};
    final workers = _statusData['workers'] as Map? ?? {};

    return ListView(
      padding: const EdgeInsets.all(16.0),
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            const Text(
              'Runtime Telemetry & Diagnostics',
              style: TextStyle(color: Color(0xFF4EC9B0), fontSize: 18, fontWeight: FontWeight.bold),
            ),
            IconButton(
              icon: const Icon(Icons.refresh, color: Color(0xFF4EC9B0)),
              onPressed: _loadDeveloperData,
            ),
          ],
        ),
        const SizedBox(height: 12),

        _buildMetricCard(
          'Active Provider',
          '${_statusData['provider']} (${_statusData['model']})',
          Icons.psychology,
          const Color(0xFF4EC9B0),
        ),
        _buildMetricCard(
          'Executive Controller',
          'Completed: ${executive['completed'] ?? 0} | Active: ${executive['active'] ?? 0}',
          Icons.account_tree,
          const Color(0xFF0E639C),
        ),
        _buildMetricCard(
          'Worker Framework v0.3',
          'Registered: ${workers['worker_count'] ?? 0} | Executions: ${workers['total_executions'] ?? 0}',
          Icons.engineering,
          Colors.orangeAccent,
          trailing: TextButton(
            onPressed: _testEchoWorker,
            child: const Text('RUN ECHO', style: TextStyle(color: Color(0xFF4EC9B0), fontSize: 11)),
          ),
        ),
        _buildMetricCard(
          'Reflection Engine',
          'Evaluations: ${reflection['total_reflections'] ?? 0} | Quality: ${(reflection['avg_quality'] as num?)?.toStringAsFixed(2) ?? "0.0"}',
          Icons.assessment,
          Colors.amber,
        ),
        _buildMetricCard(
          'Learning Engine',
          'Lessons Stored: ${learning['total_lessons'] ?? 0} | Confidence: ${(learning['avg_confidence'] as num?)?.toStringAsFixed(2) ?? "0.0"}',
          Icons.school,
          Colors.green,
        ),
        _buildMetricCard(
          'Memory Manager',
          'Working: ${memory['working_count'] ?? 0} | Persistent: ${memory['persistent_count'] ?? 0}',
          Icons.storage,
          Colors.purpleAccent,
        ),
      ],
    );
  }

  Widget _buildMetricCard(String title, String subtitle, IconData icon, Color color, {Widget? trailing}) {
    return Card(
      color: const Color(0xFF252526),
      margin: const EdgeInsets.symmetric(vertical: 6.0),
      child: ListTile(
        leading: Icon(icon, color: color),
        title: Text(title, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
        subtitle: Text(subtitle, style: const TextStyle(color: Colors.white70)),
        trailing: trailing,
      ),
    );
  }

  Widget _buildLogViewer() {
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.all(8.0),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text('Tail Log (${_logs.length} lines)', style: const TextStyle(color: Colors.white70)),
              IconButton(
                icon: const Icon(Icons.refresh, color: Color(0xFF4EC9B0)),
                onPressed: _loadDeveloperData,
              ),
            ],
          ),
        ),
        Expanded(
          child: Container(
            margin: const EdgeInsets.all(8.0),
            padding: const EdgeInsets.all(12.0),
            decoration: BoxDecoration(
              color: Colors.black,
              borderRadius: BorderRadius.circular(8.0),
              border: Border.all(color: Colors.white12),
            ),
            child: _logs.isEmpty
                ? const Center(child: Text('No session log entries available', style: TextStyle(color: Colors.white38)))
                : ListView.builder(
                    itemCount: _logs.length,
                    itemBuilder: (context, index) {
                      final line = _logs[index];
                      return SelectableText(
                        line,
                        style: const TextStyle(
                          color: Color(0xFF4EC9B0),
                          fontFamily: 'monospace',
                          fontSize: 11,
                        ),
                      );
                    },
                  ),
          ),
        ),
      ],
    );
  }
}
