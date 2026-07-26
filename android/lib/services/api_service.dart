import 'dart:convert';
import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

class ApiService {
  static const String _defaultEmulatorUrl = 'http://10.0.2.2:8000';
  static const String _defaultDesktopUrl = 'http://127.0.0.1:8000';
  static const String _customUrlKey = 'alfa_backend_base_url';

  String _baseUrl = '';
  bool _isOnline = false;

  ApiService({String? customBaseUrl}) {
    if (customBaseUrl != null && customBaseUrl.isNotEmpty) {
      _baseUrl = customBaseUrl;
    }
  }

  bool get isOnline => _isOnline;

  /// Initialize and detect appropriate backend URL automatically.
  Future<String> initBaseUrl() async {
    final prefs = await SharedPreferences.getInstance();
    final savedUrl = prefs.getString(_customUrlKey);
    if (savedUrl != null && savedUrl.isNotEmpty) {
      _baseUrl = savedUrl;
    } else if (kIsWeb) {
      _baseUrl = 'http://localhost:8000';
    } else if (Platform.isAndroid) {
      _baseUrl = _defaultEmulatorUrl;
    } else {
      _baseUrl = _defaultDesktopUrl;
    }
    await checkHealth();
    return _baseUrl;
  }

  String get baseUrl => _baseUrl.isNotEmpty ? _baseUrl : _defaultDesktopUrl;

  Future<void> setCustomBaseUrl(String url) async {
    _baseUrl = url.trim();
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_customUrlKey, _baseUrl);
    await checkHealth();
  }

  // ── Helper HTTP Execution with Retry Logic & Error Handling ─────────────────

  Future<Map<String, dynamic>> _get(String path, {int maxRetries = 2}) async {
    int attempts = 0;
    while (attempts <= maxRetries) {
      try {
        final response = await http
            .get(Uri.parse('$baseUrl$path'))
            .timeout(const Duration(seconds: 10));
        if (response.statusCode == 200) {
          _isOnline = true;
          return json.decode(response.body);
        }
        _isOnline = false;
        return {'success': false, 'error': 'HTTP ${response.statusCode}: ${response.body}'};
      } catch (e) {
        attempts++;
        if (attempts > maxRetries) {
          _isOnline = false;
          return {'success': false, 'error': 'Connection failed to $baseUrl: $e'};
        }
        await Future.delayed(Duration(milliseconds: 500 * attempts));
      }
    }
    _isOnline = false;
    return {'success': false, 'error': 'Connection failed after retries'};
  }

  Future<Map<String, dynamic>> _post(String path, Map<String, dynamic> body, {int maxRetries = 2}) async {
    int attempts = 0;
    while (attempts <= maxRetries) {
      try {
        final response = await http
            .post(
              Uri.parse('$baseUrl$path'),
              headers: {'Content-Type': 'application/json'},
              body: json.encode(body),
            )
            .timeout(const Duration(seconds: 25));
        if (response.statusCode == 200) {
          _isOnline = true;
          return json.decode(response.body);
        }
        _isOnline = false;
        return {'success': false, 'error': 'HTTP ${response.statusCode}: ${response.body}'};
      } catch (e) {
        attempts++;
        if (attempts > maxRetries) {
          _isOnline = false;
          return {'success': false, 'error': 'Connection failed to $baseUrl: $e'};
        }
        await Future.delayed(Duration(milliseconds: 500 * attempts));
      }
    }
    _isOnline = false;
    return {'success': false, 'error': 'Connection failed after retries'};
  }

  // ── Core API Endpoints ───────────────────────────────────────────────────

  Future<Map<String, dynamic>> checkHealth() async {
    final result = await _get('/health', maxRetries: 0);
    _isOnline = (result['status'] == 'ok');
    return result;
  }

  Future<Map<String, dynamic>> sendMessage(String message) async {
    return _post('/chat', {'message': message});
  }

  Future<Map<String, dynamic>> getStatus() async {
    return _get('/status');
  }

  Future<Map<String, dynamic>> getLogs({int lines = 100}) async {
    return _get('/logs?lines=$lines');
  }

  // ── Memory API ────────────────────────────────────────────────────────────

  Future<Map<String, dynamic>> getMemory() async {
    return _get('/memory');
  }

  Future<Map<String, dynamic>> getMemoryHistory() async {
    return _get('/memory/history');
  }

  Future<Map<String, dynamic>> searchMemory(String query) async {
    return _get('/memory/search?query=${Uri.encodeComponent(query)}');
  }

  Future<Map<String, dynamic>> clearMemory({String target = 'all'}) async {
    return _post('/memory/clear', {'target': target});
  }

  // ── Provider API ──────────────────────────────────────────────────────────

  Future<Map<String, dynamic>> getProviders() async {
    return _get('/providers');
  }

  Future<Map<String, dynamic>> switchProvider(String providerName) async {
    return _post('/providers/switch', {'provider': providerName});
  }

  // ── Plugin & Tool API ─────────────────────────────────────────────────────

  Future<Map<String, dynamic>> getPlugins() async {
    return _get('/plugins');
  }

  Future<Map<String, dynamic>> enablePlugin(String pluginName) async {
    return _post('/plugins/enable', {'plugin_name': pluginName});
  }

  Future<Map<String, dynamic>> disablePlugin(String pluginName) async {
    return _post('/plugins/disable', {'plugin_name': pluginName});
  }

  Future<Map<String, dynamic>> reloadPlugins() async {
    return _post('/plugins/reload', {});
  }

  // ── Settings API ──────────────────────────────────────────────────────────

  Future<Map<String, dynamic>> getSettings() async {
    return _get('/settings');
  }

  Future<Map<String, dynamic>> updateSettings(Map<String, dynamic> settings) async {
    return _post('/settings', settings);
  }

  // ── Goals & Tasks API ─────────────────────────────────────────────────────

  Future<Map<String, dynamic>> createGoal(String name, Map<String, dynamic> params) async {
    return _post('/goal', {'name': name, 'parameters': params});
  }

  Future<Map<String, dynamic>> createTask(String name, {String action = 'create'}) async {
    return _post('/task', {'name': name, 'action': action});
  }

  Future<Map<String, dynamic>> getTaskList() async {
    return _get('/tasks/list');
  }

  // ── Worker Framework API ──────────────────────────────────────────────────

  Future<Map<String, dynamic>> getWorkers() async {
    return _get('/workers');
  }

  Future<Map<String, dynamic>> executeWorker(String workerName, [Map<String, dynamic>? params]) async {
    return _post('/workers/execute', {'worker_name': workerName, 'parameters': params ?? {}});
  }

  Future<Map<String, dynamic>> postLearn(String insight, String source, double confidence) async {
    return _post('/learn', {'insight': insight, 'source': source, 'confidence': confidence});
  }

  Future<Map<String, dynamic>> postReflection(String executionId, double qualityScore) async {
    return _post('/reflection', {'execution_id': executionId, 'quality_score': qualityScore});
  }
}
