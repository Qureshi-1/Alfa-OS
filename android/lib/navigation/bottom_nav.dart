import 'package:flutter/material.dart';
import '../core/theme.dart';
import '../services/api_service.dart';
import '../widgets/cos_components.dart';
import '../features/dashboard/screens/dashboard_screen.dart';
import '../features/chat/screens/chat_screen.dart';
import '../features/memory/screens/memory_screen.dart';
import '../features/tasks/screens/task_screen.dart';
import '../features/settings/screens/settings_screen.dart';
import '../features/providers/screens/provider_screen.dart';
import '../features/plugins/screens/plugin_screen.dart';
import '../features/developer/screens/developer_screen.dart';

class MainNavigation extends StatefulWidget {
  final ApiService apiService;
  const MainNavigation({super.key, required this.apiService});

  @override
  State<MainNavigation> createState() => _MainNavigationState();
}

class _NavItem {
  final String label;
  final String subtitle;
  final IconData icon;
  final Widget Function() builder;
  const _NavItem(this.label, this.subtitle, this.icon, this.builder);
}

class _MainNavigationState extends State<MainNavigation> {
  int _currentIndex = 0;
  String _healthStatus = 'Checking';
  bool _online = false;
  late final List<_NavItem> _items;

  @override
  void initState() {
    super.initState();
    _items = [
      _NavItem('Dashboard', 'System overview', Icons.dashboard_customize, () => DashboardScreen(apiService: widget.apiService, onNavigate: (i) => setState(() => _currentIndex = i))),
      _NavItem('Chat', 'Conversation workspace', Icons.forum, () => ChatScreen(apiService: widget.apiService)),
      _NavItem('Memory', 'Explorer and graph', Icons.account_tree, () => MemoryScreen(apiService: widget.apiService)),
      _NavItem('Tasks', 'Executive workstream', Icons.route, () => TaskScreen(apiService: widget.apiService)),
      _NavItem('Models', 'Universal model hub', Icons.hub, () => ProviderScreen(apiService: widget.apiService)),
      _NavItem('Plugins', 'Capability registry', Icons.extension, () => PluginScreen(apiService: widget.apiService)),
      _NavItem('Workers', 'Runtime telemetry', Icons.precision_manufacturing, () => DeveloperScreen(apiService: widget.apiService)),
      _NavItem('Settings', 'System configuration', Icons.tune, () => SettingsScreen(apiService: widget.apiService)),
    ];
    _checkServerHealth();
  }

  Future<void> _checkServerHealth() async {
    final health = await widget.apiService.checkHealth();
    if (!mounted) return;
    setState(() {
      _online = health['status'] == 'ok';
      _healthStatus = _online ? 'Connected ${health['provider'] ?? ''}'.trim() : 'Offline';
    });
  }

  @override
  Widget build(BuildContext context) {
    final width = MediaQuery.of(context).size.width;
    final rail = width >= 760;
    return Scaffold(
      extendBody: true,
      body: CosBackdrop(
        child: SafeArea(
          child: Row(
            children: [
              if (rail) _buildSideRail(width >= 1180),
              Expanded(
                child: Column(
                  children: [
                    _buildTopBar(),
                    Expanded(
                      child: AnimatedSwitcher(
                        duration: const Duration(milliseconds: 260),
                        switchInCurve: Curves.easeOutCubic,
                        switchOutCurve: Curves.easeInCubic,
                        child: KeyedSubtree(key: ValueKey(_currentIndex), child: _items[_currentIndex].builder()),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
      bottomNavigationBar: rail ? null : NavigationBar(
        selectedIndex: _currentIndex.clamp(0, 3),
        onDestinationSelected: (index) => setState(() => _currentIndex = index),
        backgroundColor: AlfaColors.panelSolid.withOpacity(.94),
        indicatorColor: AlfaColors.neonBlue.withOpacity(.18),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.dashboard_customize), label: 'Home'),
          NavigationDestination(icon: Icon(Icons.forum), label: 'Chat'),
          NavigationDestination(icon: Icon(Icons.account_tree), label: 'Memory'),
          NavigationDestination(icon: Icon(Icons.route), label: 'Tasks'),
        ],
      ),
      drawer: rail ? null : Drawer(backgroundColor: AlfaColors.panelSolid, child: SafeArea(child: _navList(expanded: true))),
    );
  }

  Widget _buildTopBar() => Padding(
    padding: const EdgeInsets.fromLTRB(16, 10, 16, 8),
    child: GlassPanel(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
      child: Row(children: [
        Builder(builder: (context) => IconButton(icon: const Icon(Icons.menu), onPressed: MediaQuery.of(context).size.width < 760 ? () => Scaffold.of(context).openDrawer() : null)),
        const SizedBox(width: 4),
        Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(_items[_currentIndex].label.toUpperCase(), style: const TextStyle(fontWeight: FontWeight.w900, letterSpacing: 2)),
          Text(_items[_currentIndex].subtitle, style: const TextStyle(color: AlfaColors.textMuted, fontSize: 12)),
        ])),
        StatusChip(label: _healthStatus, icon: _online ? Icons.sensors : Icons.sensors_off, color: _online ? AlfaColors.mint : AlfaColors.danger),
        IconButton(onPressed: _checkServerHealth, icon: const Icon(Icons.refresh)),
      ]),
    ),
  );

  Widget _buildSideRail(bool expanded) => Container(
    width: expanded ? 286 : 92,
    padding: const EdgeInsets.fromLTRB(12, 12, 0, 12),
    child: GlassPanel(
      padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 10),
      child: _navList(expanded: expanded),
    ),
  );

  Widget _navList({required bool expanded}) => Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
    Padding(
      padding: const EdgeInsets.all(10),
      child: Row(children: [
        Container(width: 38, height: 38, decoration: BoxDecoration(shape: BoxShape.circle, gradient: const LinearGradient(colors: [AlfaColors.neonBlue, AlfaColors.violet]), boxShadow: [BoxShadow(color: AlfaColors.neonBlue.withOpacity(.35), blurRadius: 24)]), child: const Icon(Icons.blur_circular, color: Colors.white)),
        if (expanded) const SizedBox(width: 12),
        if (expanded) const Expanded(child: Text('ALFA COS', style: TextStyle(fontWeight: FontWeight.w900, letterSpacing: 2))),
      ]),
    ),
    const Divider(),
    Expanded(child: ListView.builder(itemCount: _items.length, itemBuilder: (context, index) {
      final item = _items[index];
      final selected = index == _currentIndex;
      return Padding(
        padding: const EdgeInsets.symmetric(vertical: 3),
        child: InkWell(
          borderRadius: BorderRadius.circular(16),
          onTap: () { Navigator.maybePop(context); setState(() => _currentIndex = index); },
          child: AnimatedContainer(
            duration: const Duration(milliseconds: 180),
            padding: EdgeInsets.symmetric(horizontal: expanded ? 12 : 0, vertical: 11),
            decoration: BoxDecoration(color: selected ? AlfaColors.neonBlue.withOpacity(.14) : Colors.transparent, borderRadius: BorderRadius.circular(16), border: Border.all(color: selected ? AlfaColors.lineStrong : Colors.transparent)),
            child: Row(mainAxisAlignment: expanded ? MainAxisAlignment.start : MainAxisAlignment.center, children: [
              Icon(item.icon, color: selected ? AlfaColors.neonBlue : AlfaColors.textMuted),
              if (expanded) const SizedBox(width: 12),
              if (expanded) Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [Text(item.label, style: TextStyle(fontWeight: selected ? FontWeight.w800 : FontWeight.w600)), Text(item.subtitle, style: const TextStyle(color: AlfaColors.textMuted, fontSize: 11))])),
            ]),
          ),
        ),
      );
    })),
    if (expanded) Padding(padding: const EdgeInsets.all(10), child: Text(widget.apiService.baseUrl, style: const TextStyle(color: AlfaColors.textMuted, fontSize: 11))),
  ]);
}
