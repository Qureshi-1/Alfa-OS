import 'package:flutter/material.dart';
import '../../../core/theme.dart';
import '../../../services/api_service.dart';
import '../../../widgets/cos_components.dart';

class DashboardScreen extends StatefulWidget {
  final ApiService apiService;
  final void Function(int index)? onNavigate;
  const DashboardScreen({super.key, required this.apiService, this.onNavigate});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  Map<String, dynamic> _health = {};
  Map<String, dynamic> _status = {};
  Map<String, dynamic> _memory = {};
  Map<String, dynamic> _tasks = {};
  Map<String, dynamic> _providers = {};
  Map<String, dynamic> _plugins = {};
  List<String> _logs = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() => _loading = true);
    final results = await Future.wait([
      widget.apiService.checkHealth(),
      widget.apiService.getStatus(),
      widget.apiService.getMemory(),
      widget.apiService.getTaskList(),
      widget.apiService.getProviders(),
      widget.apiService.getPlugins(),
      widget.apiService.getLogs(lines: 24),
    ]);
    if (!mounted) return;
    setState(() {
      _health = results[0];
      _status = results[1];
      _memory = results[2];
      _tasks = results[3];
      _providers = results[4];
      _plugins = results[5];
      _logs = (results[6]['logs'] as List?)?.map((e) => e.toString()).toList() ?? [];
      _loading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    final memoryStats = _status['memory'] as Map? ?? _memory['stats'] as Map? ?? {};
    final workers = _status['workers'] as Map? ?? {};
    final executive = _status['executive'] as Map? ?? {};
    final activeTasks = _tasks['active'] as List? ?? [];
    final history = _tasks['history'] as List? ?? [];
    final tools = _plugins['tools'] as List? ?? [];
    final activeProvider = _providers['active_provider'] ?? _status['provider'] ?? 'unknown';
    final model = _providers['active_model'] ?? _status['model'] ?? 'unreported';
    final online = _health['status'] == 'ok';

    return RefreshIndicator(
      onRefresh: _load,
      child: ListView(
        padding: const EdgeInsets.all(18),
        children: [
          SectionHeader(
            title: 'Cognition Operating System',
            subtitle: 'Live command surface connected to ${widget.apiService.baseUrl}',
            trailing: Wrap(spacing: 8, children: [
              StatusChip(label: online ? 'Runtime online' : 'Runtime offline', icon: online ? Icons.bolt : Icons.cloud_off, color: online ? AlfaColors.mint : AlfaColors.danger),
              IconButton(onPressed: _load, icon: const Icon(Icons.refresh)),
            ]),
          ),
          if (_loading) const Padding(padding: EdgeInsets.only(top: 12), child: LinearProgressIndicator()),
          const SizedBox(height: 18),
          LayoutBuilder(builder: (context, constraints) {
            final wide = constraints.maxWidth > 920;
            final hero = GlassPanel(
              padding: const EdgeInsets.all(20),
              child: wide
                  ? Row(children: [_avatar(online), const SizedBox(width: 24), Expanded(child: _heroCopy(activeProvider, model)), const SizedBox(width: 16), _quickActions()])
                  : Column(crossAxisAlignment: CrossAxisAlignment.start, children: [_avatar(online), const SizedBox(height: 18), _heroCopy(activeProvider, model), const SizedBox(height: 14), _quickActions()]),
            );
            return hero;
          }),
          const SizedBox(height: 14),
          ResponsiveGrid(minTileWidth: 175, children: [
            MetricTile(label: 'Health', value: online ? 'OK' : 'OFF', icon: Icons.health_and_safety, color: online ? AlfaColors.mint : AlfaColors.danger, detail: _health['provider']?.toString()),
            MetricTile(label: 'Memory', value: '${memoryStats['working_count'] ?? (_memory['working_memory'] as List?)?.length ?? 0}', icon: Icons.memory, color: AlfaColors.cyan, detail: 'Persistent ${memoryStats['persistent_count'] ?? (_memory['persistent_memory'] as List?)?.length ?? 0}'),
            MetricTile(label: 'Workers', value: '${workers['worker_count'] ?? 0}', icon: Icons.precision_manufacturing, color: AlfaColors.violet, detail: 'Executions ${workers['total_executions'] ?? 0}'),
            MetricTile(label: 'Tasks', value: '${activeTasks.length}', icon: Icons.route, color: AlfaColors.amber, detail: 'History ${history.length}'),
            MetricTile(label: 'Models', value: activeProvider.toString().toUpperCase(), icon: Icons.hub, color: AlfaColors.neonBlue, detail: model.toString()),
            MetricTile(label: 'Plugins', value: '${tools.length}', icon: Icons.extension, color: AlfaColors.mint, detail: 'Registered tools'),
            MetricTile(label: 'Brain', value: '${executive['completed'] ?? 0}', icon: Icons.psychology_alt, color: AlfaColors.cyan, detail: 'Executive completions'),
            MetricTile(label: 'Internet', value: online ? 'LINK' : 'WAIT', icon: Icons.public, color: online ? AlfaColors.neonBlue : AlfaColors.textMuted, detail: 'API transport'),
          ]),
          const SizedBox(height: 14),
          LayoutBuilder(builder: (context, constraints) {
            final wide = constraints.maxWidth > 860;
            final widgets = [_taskPanel(activeTasks), _logsPanel(), _notificationPanel()];
            if (!wide) return Column(children: widgets.map((w) => Padding(padding: const EdgeInsets.only(bottom: 12), child: w)).toList());
            return Row(crossAxisAlignment: CrossAxisAlignment.start, children: [Expanded(child: widgets[0]), const SizedBox(width: 12), Expanded(child: widgets[1]), const SizedBox(width: 12), Expanded(child: widgets[2])]);
          }),
        ],
      ),
    );
  }

  Widget _avatar(bool online) => Row(mainAxisSize: MainAxisSize.min, children: [AvatarOrb(state: online ? 'Thinking' : 'Idle')]);

  Widget _heroCopy(Object activeProvider, Object model) => Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
    const Text('ALFA COS', style: TextStyle(fontSize: 34, fontWeight: FontWeight.w900, letterSpacing: 4)),
    const SizedBox(height: 8),
    const Text('A premium operating interface for cognition, workers, memory, models, research and tool execution.', style: TextStyle(color: AlfaColors.textMuted, height: 1.4)),
    const SizedBox(height: 14),
    Wrap(spacing: 8, runSpacing: 8, children: [StatusChip(label: 'Provider $activeProvider', icon: Icons.psychology), StatusChip(label: '$model', icon: Icons.model_training, color: AlfaColors.cyan)]),
  ]);

  Widget _quickActions() => Wrap(spacing: 8, runSpacing: 8, children: [
    _action('Chat', Icons.forum, 1), _action('Models', Icons.hub, 4), _action('Memory', Icons.account_tree, 2), _action('Workers', Icons.engineering, 6),
  ]);
  Widget _action(String label, IconData icon, int index) => OutlinedButton.icon(onPressed: () => widget.onNavigate?.call(index), icon: Icon(icon, size: 16), label: Text(label));

  Widget _taskPanel(List activeTasks) => GlassPanel(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
    const SectionHeader(title: 'Task stream', subtitle: 'Active executive work'), const SizedBox(height: 10),
    if (activeTasks.isEmpty) const Text('No active tasks running', style: TextStyle(color: AlfaColors.textMuted))
    else for (final item in activeTasks.take(5)) ListTile(contentPadding: EdgeInsets.zero, leading: const Icon(Icons.pending_actions), title: Text('${item['goal_name'] ?? item['execution_id'] ?? 'Task'}'), subtitle: Text('${item['status'] ?? 'unknown'}', style: const TextStyle(color: AlfaColors.textMuted))),
  ]));

  Widget _logsPanel() => GlassPanel(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
    const SectionHeader(title: 'Logs', subtitle: 'Recent runtime trace'), const SizedBox(height: 10),
    if (_logs.isEmpty) const Text('No logs reported', style: TextStyle(color: AlfaColors.textMuted))
    else for (final line in _logs.take(8)) Padding(padding: const EdgeInsets.only(bottom: 6), child: Text(line, maxLines: 1, overflow: TextOverflow.ellipsis, style: const TextStyle(color: AlfaColors.textMuted, fontFamily: 'monospace', fontSize: 11))),
  ]));

  Widget _notificationPanel() => GlassPanel(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
    const SectionHeader(title: 'Notifications', subtitle: 'System signals'), const SizedBox(height: 10),
    StatusChip(label: _health['status'] == 'ok' ? 'Health nominal' : 'Backend unreachable', icon: Icons.notifications_active, color: _health['status'] == 'ok' ? AlfaColors.mint : AlfaColors.danger),
    const SizedBox(height: 10),
    Text(_health['error']?.toString() ?? 'All connected widgets are API-driven. No synthetic telemetry is displayed.', style: const TextStyle(color: AlfaColors.textMuted, height: 1.35)),
  ]));
}
