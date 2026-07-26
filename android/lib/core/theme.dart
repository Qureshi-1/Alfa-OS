import 'package:flutter/material.dart';

class AlfaColors {
  static const voidBlack = Color(0xFF030712);
  static const deepSpace = Color(0xFF07111F);
  static const panel = Color(0xB30B1626);
  static const panelSolid = Color(0xFF0B1626);
  static const panelElevated = Color(0xFF102033);
  static const line = Color(0x334FC3FF);
  static const lineStrong = Color(0x664FC3FF);
  static const neonBlue = Color(0xFF4FC3FF);
  static const electricBlue = Color(0xFF0A84FF);
  static const cyan = Color(0xFF64F7FF);
  static const mint = Color(0xFF4DFFCA);
  static const violet = Color(0xFF8B7CFF);
  static const amber = Color(0xFFFFC857);
  static const danger = Color(0xFFFF5C7A);
  static const text = Color(0xFFEAF6FF);
  static const textMuted = Color(0xFF8EA4B8);
}

class AlfaTheme {
  static ThemeData get darkTheme {
    final base = ThemeData.dark(useMaterial3: true);
    return base.copyWith(
      brightness: Brightness.dark,
      scaffoldBackgroundColor: AlfaColors.voidBlack,
      colorScheme: const ColorScheme.dark(
        primary: AlfaColors.neonBlue,
        secondary: AlfaColors.cyan,
        tertiary: AlfaColors.mint,
        surface: AlfaColors.panelSolid,
        error: AlfaColors.danger,
      ),
      textTheme: base.textTheme.apply(
        bodyColor: AlfaColors.text,
        displayColor: AlfaColors.text,
        fontFamily: 'Roboto',
      ),
      appBarTheme: const AppBarTheme(
        elevation: 0,
        centerTitle: false,
        backgroundColor: Colors.transparent,
        foregroundColor: AlfaColors.text,
        titleTextStyle: TextStyle(fontSize: 16, fontWeight: FontWeight.w700, letterSpacing: 1.4),
      ),
      cardTheme: CardTheme(
        color: AlfaColors.panel,
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(22),
          side: const BorderSide(color: AlfaColors.line),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: const Color(0x66091424),
        hintStyle: const TextStyle(color: AlfaColors.textMuted),
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(18),
          borderSide: const BorderSide(color: AlfaColors.line),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(18),
          borderSide: const BorderSide(color: AlfaColors.neonBlue, width: 1.4),
        ),
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(18)),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: AlfaColors.electricBlue,
          foregroundColor: Colors.white,
          elevation: 0,
          padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 14),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        ),
      ),
      iconButtonTheme: IconButtonThemeData(
        style: IconButton.styleFrom(foregroundColor: AlfaColors.neonBlue),
      ),
      dividerTheme: const DividerThemeData(color: AlfaColors.line),
      progressIndicatorTheme: const ProgressIndicatorThemeData(
        color: AlfaColors.neonBlue,
        linearTrackColor: Color(0x220A84FF),
      ),
      bottomNavigationBarTheme: const BottomNavigationBarThemeData(
        backgroundColor: AlfaColors.panelSolid,
        selectedItemColor: AlfaColors.neonBlue,
        unselectedItemColor: AlfaColors.textMuted,
        type: BottomNavigationBarType.fixed,
      ),
    );
  }
}
