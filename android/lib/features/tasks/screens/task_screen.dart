import 'package:flutter/material.dart';
import '../../../services/api_service.dart';

class TaskScreen extends StatefulWidget {
  final ApiService apiService;
  const TaskScreen({super.key, required this.apiService});

  @override
  State<TaskScreen> createState() => _TaskScreenState();
}

class _TaskScreenState extends State<TaskScreen> {
  Map<String, dynamic> _taskListData = {};
  bool _isLoading = false;
  String? _error;
  final TextEditingController _taskController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _loadTasks();
  }

  Future<void> _loadTasks() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });
    final res = await widget.apiService.getTaskList();
    setState(() {
      _isLoading = false;
      if (res['active'] != null || res['history'] != null) {
        _taskListData = res;
      } else {
        _error = res['error'] ?? 'Failed to load task list';
      }
    });
  }

  void _submitTask() async {
    final name = _taskController.text.trim();
    if (name.isEmpty) return;

    _taskController.clear();
    setState(() => _isLoading = true);

    await widget.apiService.createTask(name);
    _loadTasks();
  }

  void _cancelTask(String executionId) async {
    setState(() => _isLoading = true);
    await widget.apiService.createTask(executionId, action: 'cancel');
    _loadTasks();
  }

  @override
  Widget build(BuildContext context) {
    final activeGoals = _taskListData['active'] as List? ?? [];
    final history = _taskListData['history'] as List? ?? [];

    return Column(
      children: [
        // New Task Input Bar
        Container(
          padding: const EdgeInsets.all(12.0),
          color: const Color(0xFF1E1E1E),
          child: Row(
            children: [
              Expanded(
                child: TextField(
                  controller: _taskController,
                  style: const TextStyle(color: Colors.white),
                  decoration: const InputDecoration(
                    hintText: 'Schedule new executive goal...',
                    hintStyle: TextStyle(color: Colors.white38),
                    border: InputBorder.none,
                  ),
                  onSubmitted: (_) => _submitTask(),
                ),
              ),
              ElevatedButton.icon(
                onPressed: _submitTask,
                icon: const Icon(Icons.add_task),
                label: const Text('Schedule'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF0E639C),
                  foregroundColor: Colors.white,
                ),
              ),
            ],
          ),
        ),

        if (_isLoading) const LinearProgressIndicator(),

        if (_error != null)
          Container(
            color: const Color(0xFFA83232),
            padding: const EdgeInsets.all(8.0),
            child: Row(
              children: [
                const Icon(Icons.error_outline, color: Colors.white, size: 18),
                const SizedBox(width: 8),
                Expanded(child: Text(_error!, style: const TextStyle(color: Colors.white, fontSize: 12))),
                TextButton(onPressed: _loadTasks, child: const Text('RETRY', style: TextStyle(color: Colors.white))),
              ],
            ),
          ),

        Expanded(
          child: RefreshIndicator(
            onRefresh: _loadTasks,
            child: ListView(
              padding: const EdgeInsets.all(12.0),
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    const Text(
                      'Executive Controller Tasks',
                      style: TextStyle(color: Color(0xFF4EC9B0), fontSize: 18, fontWeight: FontWeight.bold),
                    ),
                    IconButton(
                      icon: const Icon(Icons.refresh, color: Color(0xFF4EC9B0)),
                      onPressed: _loadTasks,
                    ),
                  ],
                ),
                const SizedBox(height: 12),

                // Active Goals
                const Text(
                  'Active Executions',
                  style: TextStyle(color: Colors.white70, fontSize: 16, fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 8),

                if (activeGoals.isEmpty)
                  const Card(
                    color: Color(0xFF252526),
                    child: Padding(
                      padding: EdgeInsets.all(16.0),
                      child: Text('No active tasks running', style: TextStyle(color: Colors.white38)),
                    ),
                  )
                else
                  for (var item in activeGoals)
                    Card(
                      color: const Color(0x4D0E639C),
                      margin: const EdgeInsets.symmetric(vertical: 4.0),
                      child: ListTile(
                        leading: const Icon(Icons.pending_actions, color: Color(0xFF4EC9B0)),
                        title: Text(item['goal_name'] ?? item['execution_id'] ?? 'Goal', style: const TextStyle(color: Colors.white)),
                        subtitle: Text('Status: ${item['status']} | Priority: ${item['priority']}', style: const TextStyle(color: Colors.white70, fontSize: 12)),
                        trailing: IconButton(
                          icon: const Icon(Icons.cancel, color: Colors.redAccent),
                          onPressed: () => _cancelTask(item['execution_id'] ?? ''),
                        ),
                      ),
                    ),

                const SizedBox(height: 16),
                const Text(
                  'Execution History',
                  style: TextStyle(color: Colors.white70, fontSize: 16, fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 8),

                if (history.isEmpty)
                  const Card(
                    color: Color(0xFF252526),
                    child: Padding(
                      padding: EdgeInsets.all(16.0),
                      child: Text('No execution history recorded', style: TextStyle(color: Colors.white38)),
                    ),
                  )
                else
                  for (var item in history)
                    Card(
                      color: const Color(0xFF252526),
                      margin: const EdgeInsets.symmetric(vertical: 4.0),
                      child: ListTile(
                        leading: Icon(
                          (item['status'] == 'completed' || item['status'] == 'success')
                              ? Icons.check_circle
                              : Icons.error,
                          color: (item['status'] == 'completed' || item['status'] == 'success')
                              ? Colors.green
                              : Colors.red,
                        ),
                        title: Text(item['goal_name'] ?? item['execution_id'] ?? 'Goal', style: const TextStyle(color: Colors.white)),
                        subtitle: Text('Status: ${item['status'] ?? 'unknown'}${item['error'] != null ? ' - ${item['error']}' : ''}',
                            style: const TextStyle(color: Colors.white54, fontSize: 12)),
                      ),
                    ),
              ],
            ),
          ),
        ),
      ],
    );
  }
}
