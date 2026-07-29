import 'package:flutter_test/flutter_test.dart';
import 'package:alfa_cos_mobile/main.dart';
import 'package:alfa_cos_mobile/services/api_service.dart';

void main() {
  testWidgets('Alfa COS Mobile App smoke test', (WidgetTester tester) async {
    final apiService = ApiService(customBaseUrl: 'http://127.0.0.1:8000');
    await tester.pumpWidget(AlfaApp(apiService: apiService));
    expect(find.text('ALFA COS'), findsWidgets);
  });
}
