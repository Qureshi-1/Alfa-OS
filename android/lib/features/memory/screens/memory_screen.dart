import 'package:flutter/material.dart';
import '../../../services/api_service.dart';

class MemoryScreen extends StatefulWidget {
  final ApiService apiService;
  const MemoryScreen({super.key, required this.apiService});

  @override
  State<MemoryScreen> createState() => _MemoryScreenState();
}

class _MemoryScreenState extends State<MemoryScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  final TextEditingController _searchController = TextEditingController();

  List<dynamic> _workingMemory = [];
  List<dynamic> _persistentMemory = [];
  List<dynamic> _searchResults = [];
  Map<String, dynamic> _stats = {};
  bool _isLoading = false;
  bool _isSearching = false;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
    _loadMemory();
  }

  Future<void> _loadMemory() async {
    setState(() => _isLoading = true);
    final res = await widget.apiService.getMemory();
    setState(() {
      _isLoading = false;
      _stats = res['stats'] ?? {};
      _workingMemory = res['working_memory'] ?? [];
      _persistentMemory = res['persistent_memory'] ?? [];
    });
  }

  void _onSearch() async {
    final query = _searchController.text.trim();
    if (query.isEmpty) {
      setState(() => _isSearching = false);
      return;
    }
    setState(() {
      _isLoading = true;
      _isSearching = true;
    });

    final res = await widget.apiService.searchMemory(query);
    setState(() {
      _isLoading = false;
      _searchResults = res['results'] ?? [];
    });
  }

  void _clearMemory(String target) async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Clear $target Memory?'),
        content: Text('Are you sure you want to clear $target memory?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('CANCEL'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('CLEAR', style: TextStyle(color: Colors.red)),
          ),
        ],
      ),
    );

    if (confirm == true) {
      await widget.apiService.clearMemory(target: target);
      _loadMemory();
    }
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        // Search & Filter Header
        Padding(
          padding: const EdgeInsets.all(12.0),
          child: Row(
            children: [
              Expanded(
                child: TextField(
                  controller: _searchController,
                  style: const TextStyle(color: Colors.white),
                  decoration: InputDecoration(
                    hintText: 'Search memories...',
                    hintStyle: const TextStyle(color: Colors.white38),
                    prefixIcon: const Icon(Icons.search, color: Color(0xFF4EC9B0)),
                    suffixIcon: _searchController.text.isNotEmpty
                        ? IconButton(
                            icon: const Icon(Icons.clear, color: Colors.white54),
                            onPressed: () {
                              _searchController.clear();
                              setState(() => _isSearching = false);
                            },
                          )
                        : null,
                    filled: true,
                    fillColor: const Color(0xFF252526),
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(8.0),
                      borderSide: BorderSide.none,
                    ),
                  ),
                  onSubmitted: (_) => _onSearch(),
                ),
              ),
              const SizedBox(width: 8),
              IconButton(
                icon: const Icon(Icons.refresh, color: Color(0xFF4EC9B0)),
                onPressed: _loadMemory,
              ),
              PopupMenuButton<String>(
                icon: const Icon(Icons.delete_sweep, color: Colors.redAccent),
                onSelected: _clearMemory,
                itemBuilder: (context) => const [
                  PopupMenuItem(value: 'working', child: Text('Clear Working Memory')),
                  PopupMenuItem(value: 'persistent', child: Text('Clear Persistent Memory')),
                  PopupMenuItem(value: 'all', child: Text('Clear All Memory')),
                ],
              ),
            ],
          ),
        ),

        // Tabs
        TabBar(
          controller: _tabController,
          indicatorColor: const Color(0xFF4EC9B0),
          labelColor: const Color(0xFF4EC9B0),
          unselectedLabelColor: Colors.white54,
          tabs: [
            Tab(text: 'Working (${_workingMemory.length})'),
            Tab(text: 'Persistent (${_persistentMemory.length})'),
            const Tab(text: 'Stats'),
          ],
        ),

        if (_isLoading) const LinearProgressIndicator(),

        Expanded(
          child: _isSearching
              ? _buildSearchResultsList()
              : TabBarView(
                  controller: _tabController,
                  children: [
                    _buildMemoryList(_workingMemory, 'Working Memory'),
                    _buildMemoryList(_persistentMemory, 'Persistent SQLite Memory'),
                    _buildStatsView(),
                  ],
                ),
        ),
      ],
    );
  }

  Widget _buildSearchResultsList() {
    return ListView.builder(
      padding: const EdgeInsets.all(12.0),
      itemCount: _searchResults.length,
      itemBuilder: (context, index) {
        final item = _searchResults[index];
        final content = item is Map ? item['content'] ?? item.toString() : item.toString();
        return Card(
          color: const Color(0xFF252526),
          child: ListTile(
            leading: const Icon(Icons.search, color: Color(0xFF4EC9B0)),
            title: Text(content, style: const TextStyle(color: Colors.white)),
            subtitle: Text(item is Map ? 'Tags: ${item['tags'] ?? []}' : 'Result'),
          ),
        );
      },
    );
  }

  Widget _buildMemoryList(List<dynamic> items, String title) {
    if (items.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.memory, size: 48, color: Colors.white24),
            const SizedBox(height: 12),
            Text('No items in $title', style: const TextStyle(color: Colors.white54)),
          ],
        ),
      );
    }
    return ListView.builder(
      padding: const EdgeInsets.all(12.0),
      itemCount: items.length,
      itemBuilder: (context, index) {
        final item = items[index];
        final content = item is Map ? item['content'] ?? item.toString() : item.toString();
        final tags = item is Map ? (item['tags'] as List?)?.join(', ') ?? '' : '';

        return Card(
          color: const Color(0xFF252526),
          margin: const EdgeInsets.symmetric(vertical: 4.0),
          child: ListTile(
            leading: const Icon(Icons.storage, color: Color(0xFF0E639C)),
            title: Text(content, style: const TextStyle(color: Colors.white)),
            subtitle: tags.isNotEmpty
                ? Text('Tags: $tags', style: const TextStyle(color: Color(0xFF4EC9B0), fontSize: 12))
                : null,
          ),
        );
      },
    );
  }

  Widget _buildStatsView() {
    return ListView(
      padding: const EdgeInsets.all(16.0),
      children: [
        const Text(
          'Memory Engine Metrics',
          style: TextStyle(color: Color(0xFF4EC9B0), fontSize: 18, fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 12),
        Card(
          color: const Color(0xFF252526),
          child: ListTile(
            title: const Text('Working Memory Count', style: TextStyle(color: Colors.white)),
            trailing: Text('${_workingMemory.length}', style: const TextStyle(color: Color(0xFF4EC9B0), fontSize: 18)),
          ),
        ),
        Card(
          color: const Color(0xFF252526),
          child: ListTile(
            title: const Text('Persistent SQLite Count', style: TextStyle(color: Colors.white)),
            trailing: Text('${_persistentMemory.length}', style: const TextStyle(color: Color(0xFF4EC9B0), fontSize: 18)),
          ),
        ),
        Card(
          color: const Color(0xFF252526),
          child: ListTile(
            title: const Text('Memory Engine Status', style: TextStyle(color: Colors.white)),
            subtitle: Text(_stats.toString(), style: const TextStyle(color: Colors.white70, fontSize: 12)),
          ),
        ),
      ],
    );
  }
}
