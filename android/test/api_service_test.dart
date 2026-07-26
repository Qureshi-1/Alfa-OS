import 'package:flutter_test/flutter_test.dart';
import 'package:alfa_cos_mobile/services/api_service.dart';

void main() {
  group('ApiService Unit Tests', () {
    late ApiService apiService;

    setUp(() {
      apiService = ApiService(customBaseUrl: 'http://127.0.0.1:8000');
    });

    test('Base URL initializes correctly', () async {
      expect(apiService.baseUrl, 'http://127.0.0.1:8000');
    });

    test('Custom Base URL setting persists', () async {
      apiService = ApiService(customBaseUrl: 'http://192.168.1.100:8000');
      expect(apiService.baseUrl, 'http://192.168.1.100:8000');
    });
  });
}
