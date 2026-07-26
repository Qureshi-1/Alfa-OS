import 'package:flutter/material.dart';
import 'core/theme.dart';
import 'navigation/bottom_nav.dart';
import 'services/api_service.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final apiService = ApiService();
  await apiService.initBaseUrl();
  runApp(AlfaApp(apiService: apiService));
}

class AlfaApp extends StatelessWidget {
  final ApiService apiService;
  const AlfaApp({super.key, required this.apiService});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Alfa COS Mobile',
      debugShowCheckedModeBanner: false,
      theme: AlfaTheme.darkTheme,
      home: MainNavigation(apiService: apiService),
    );
  }
}
