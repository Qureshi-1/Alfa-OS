import 'package:flutter/material.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import '../../../services/api_service.dart';

class ChatScreen extends StatefulWidget {
  final ApiService apiService;
  const ChatScreen({super.key, required this.apiService});

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final List<Map<String, dynamic>> _messages = [];
  final TextEditingController _controller = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  bool _isLoading = false;
  String? _lastError;
  String _activeProvider = 'mock';

  @override
  void initState() {
    super.initState();
    _fetchProviderInfo();
  }

  Future<void> _fetchProviderInfo() async {
    final res = await widget.apiService.getProviders();
    if (res['active_provider'] != null) {
      setState(() {
        _activeProvider = res['active_provider'];
      });
    }
  }

  void _sendMessage() async {
    final text = _controller.text.trim();
    if (text.isEmpty || _isLoading) return;

    _controller.clear();
    setState(() {
      _messages.add({
        'sender': 'user',
        'text': text,
        'timestamp': DateTime.now().toIso8601String().substring(11, 19),
      });
      _isLoading = true;
      _lastError = null;
    });

    _scrollToBottom();

    final res = await widget.apiService.sendMessage(text);

    setState(() {
      _isLoading = false;
      if (res['success'] == true) {
        _messages.add({
          'sender': 'alfa',
          'text': res['reply'] ?? '',
          'provider': res['provider_used'] ?? _activeProvider,
          'latency': res['latency_ms'] ?? 0.0,
          'execution_id': res['execution_id'],
          'timestamp': DateTime.now().toIso8601String().substring(11, 19),
        });
      } else {
        _lastError = res['error'] ?? 'Unknown network failure';
        _messages.add({
          'sender': 'system',
          'text': 'Error: $_lastError',
          'timestamp': DateTime.now().toIso8601String().substring(11, 19),
        });
      }
    });

    _scrollToBottom();
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        // Provider & Status Header Bar
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 8.0),
          color: const Color(0xFF1E1E1E),
          child: Row(
            children: [
              const Icon(Icons.psychology, color: Color(0xFF4EC9B0), size: 20),
              const SizedBox(width: 8),
              Text(
                'Active Provider: $_activeProvider',
                style: const TextStyle(color: Colors.white70, fontSize: 13),
              ),
              const Spacer(),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                decoration: BoxDecoration(
                  color: const Color(0x4D0E639C),
                  borderRadius: BorderRadius.circular(4),
                ),
                child: const Text(
                  'Runtime Online',
                  style: TextStyle(color: Color(0xFF4EC9B0), fontSize: 11),
                ),
              ),
            ],
          ),
        ),

        if (_lastError != null)
          Container(
            color: const Color(0xFFA83232),
            padding: const EdgeInsets.all(8.0),
            child: Row(
              children: [
                const Icon(Icons.warning, color: Colors.white, size: 18),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    _lastError!,
                    style: const TextStyle(color: Colors.white, fontSize: 12),
                  ),
                ),
                TextButton(
                  onPressed: () => setState(() => _lastError = null),
                  child: const Text('DISMISS', style: TextStyle(color: Colors.white)),
                ),
              ],
            ),
          ),

        // Message List
        Expanded(
          child: _messages.isEmpty
              ? const Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.chat_bubble_outline, size: 64, color: Colors.white24),
                      SizedBox(height: 16),
                      Text(
                        'Start a conversation with Alfa COS Cognitive Core',
                        style: TextStyle(color: Colors.white54),
                      ),
                    ],
                  ),
                )
              : ListView.builder(
                  controller: _scrollController,
                  padding: const EdgeInsets.all(12.0),
                  itemCount: _messages.length,
                  itemBuilder: (context, index) {
                    final msg = _messages[index];
                    final isUser = msg['sender'] == 'user';
                    final isSystem = msg['sender'] == 'system';

                    return Align(
                      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
                      child: Container(
                        constraints: BoxConstraints(
                          maxWidth: MediaQuery.of(context).size.width * 0.85,
                        ),
                        margin: const EdgeInsets.symmetric(vertical: 6.0),
                        padding: const EdgeInsets.all(12.0),
                        decoration: BoxDecoration(
                          color: isUser
                              ? const Color(0xFF0E639C)
                              : (isSystem ? const Color(0xFFA83232) : const Color(0xFF252526)),
                          borderRadius: BorderRadius.circular(10.0),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                Text(
                                  isUser ? 'You' : (isSystem ? 'System' : 'Alfa COS'),
                                  style: const TextStyle(
                                    color: Colors.white70,
                                    fontWeight: FontWeight.bold,
                                    fontSize: 12,
                                  ),
                                ),
                                const Spacer(),
                                Text(
                                  msg['timestamp'] ?? '',
                                  style: const TextStyle(color: Colors.white38, fontSize: 10),
                                ),
                              ],
                            ),
                            const Divider(color: Colors.white12, height: 12),
                            if (isUser || isSystem)
                              SelectableText(
                                msg['text'] ?? '',
                                style: const TextStyle(color: Colors.white, fontSize: 14),
                              )
                            else
                              MarkdownBody(
                                data: msg['text'] ?? '',
                                styleSheet: MarkdownStyleSheet.fromTheme(Theme.of(context)).copyWith(
                                  p: const TextStyle(color: Colors.white, fontSize: 14),
                                ),
                              ),
                            if (msg['latency'] != null) ...[
                              const SizedBox(height: 8),
                              Row(
                                mainAxisAlignment: MainAxisAlignment.end,
                                children: [
                                  const Icon(Icons.speed, size: 12, color: Colors.white38),
                                  const SizedBox(width: 4),
                                  Text(
                                    '${msg['latency']}ms (${msg['provider']})',
                                    style: const TextStyle(color: Colors.white38, fontSize: 10),
                                  ),
                                ],
                              ),
                            ],
                          ],
                        ),
                      ),
                    );
                  },
                ),
        ),

        if (_isLoading) const LinearProgressIndicator(backgroundColor: Color(0xFF252526)),

        // Text Input Bar
        Container(
          padding: const EdgeInsets.all(8.0),
          color: const Color(0xFF1E1E1E),
          child: Row(
            children: [
              Expanded(
                child: TextField(
                  controller: _controller,
                  style: const TextStyle(color: Colors.white),
                  decoration: const InputDecoration(
                    hintText: 'Ask Alfa COS anything...',
                    hintStyle: TextStyle(color: Colors.white38),
                    border: InputBorder.none,
                    contentPadding: EdgeInsets.symmetric(horizontal: 12),
                  ),
                  onSubmitted: (_) => _sendMessage(),
                ),
              ),
              IconButton(
                icon: const Icon(Icons.send, color: Color(0xFF4EC9B0)),
                onPressed: _sendMessage,
              ),
            ],
          ),
        ),
      ],
    );
  }
}
