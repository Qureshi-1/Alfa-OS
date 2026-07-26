import 'dart:math' as math;
import 'package:flutter/material.dart';
import '../core/theme.dart';

class CosBackdrop extends StatelessWidget {
  final Widget child;
  const CosBackdrop({super.key, required this.child});

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: const BoxDecoration(
        gradient: RadialGradient(
          center: Alignment(-0.65, -0.85),
          radius: 1.35,
          colors: [Color(0x3325B7FF), AlfaColors.voidBlack],
        ),
      ),
      child: Stack(
        children: [
          Positioned.fill(child: CustomPaint(painter: _GridPainter())),
          Positioned.fill(
            child: DecoratedBox(
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.topRight,
                  end: Alignment.bottomLeft,
                  colors: [AlfaColors.deepSpace.withOpacity(.58), Colors.transparent, const Color(0x220A84FF)],
                ),
              ),
            ),
          ),
          child,
        ],
      ),
    );
  }
}

class _GridPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()..color = AlfaColors.line.withOpacity(.28)..strokeWidth = .6;
    const step = 36.0;
    for (double x = 0; x < size.width; x += step) {
      canvas.drawLine(Offset(x, 0), Offset(x, size.height), paint);
    }
    for (double y = 0; y < size.height; y += step) {
      canvas.drawLine(Offset(0, y), Offset(size.width, y), paint);
    }
  }
  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

class GlassPanel extends StatelessWidget {
  final Widget child;
  final EdgeInsetsGeometry padding;
  final Color accent;
  final VoidCallback? onTap;
  const GlassPanel({super.key, required this.child, this.padding = const EdgeInsets.all(16), this.accent = AlfaColors.neonBlue, this.onTap});

  @override
  Widget build(BuildContext context) {
    final panel = AnimatedContainer(
      duration: const Duration(milliseconds: 220),
      curve: Curves.easeOutCubic,
      padding: padding,
      decoration: BoxDecoration(
        color: AlfaColors.panel,
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: accent.withOpacity(.28)),
        boxShadow: [BoxShadow(color: accent.withOpacity(.08), blurRadius: 30, spreadRadius: -8)],
      ),
      child: child,
    );
    if (onTap == null) return panel;
    return InkWell(borderRadius: BorderRadius.circular(24), onTap: onTap, child: panel);
  }
}

class StatusChip extends StatelessWidget {
  final String label;
  final IconData icon;
  final Color color;
  const StatusChip({super.key, required this.label, this.icon = Icons.circle, this.color = AlfaColors.mint});
  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 7),
    decoration: BoxDecoration(color: color.withOpacity(.12), borderRadius: BorderRadius.circular(999), border: Border.all(color: color.withOpacity(.35))),
    child: Row(mainAxisSize: MainAxisSize.min, children: [Icon(icon, size: 14, color: color), const SizedBox(width: 6), Text(label, style: TextStyle(color: color, fontSize: 11, fontWeight: FontWeight.w700, letterSpacing: .5))]),
  );
}

class SectionHeader extends StatelessWidget {
  final String title;
  final String? subtitle;
  final Widget? trailing;
  const SectionHeader({super.key, required this.title, this.subtitle, this.trailing});
  @override
  Widget build(BuildContext context) => Row(children: [
    Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Text(title.toUpperCase(), style: const TextStyle(color: AlfaColors.text, fontSize: 15, fontWeight: FontWeight.w800, letterSpacing: 1.6)),
      if (subtitle != null) Padding(padding: const EdgeInsets.only(top: 4), child: Text(subtitle!, style: const TextStyle(color: AlfaColors.textMuted, fontSize: 12))),
    ])),
    if (trailing != null) trailing!,
  ]);
}

class MetricTile extends StatelessWidget {
  final String label;
  final String value;
  final IconData icon;
  final Color color;
  final String? detail;
  const MetricTile({super.key, required this.label, required this.value, required this.icon, this.color = AlfaColors.neonBlue, this.detail});
  @override
  Widget build(BuildContext context) => GlassPanel(
    accent: color,
    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Row(children: [Icon(icon, color: color, size: 19), const Spacer(), Container(width: 8, height: 8, decoration: BoxDecoration(color: color, shape: BoxShape.circle, boxShadow: [BoxShadow(color: color, blurRadius: 12)]))]),
      const SizedBox(height: 14),
      Text(value, style: const TextStyle(fontSize: 24, fontWeight: FontWeight.w800, letterSpacing: -.4)),
      const SizedBox(height: 4),
      Text(label.toUpperCase(), style: const TextStyle(color: AlfaColors.textMuted, fontSize: 11, letterSpacing: 1.2)),
      if (detail != null) Padding(padding: const EdgeInsets.only(top: 8), child: Text(detail!, maxLines: 2, overflow: TextOverflow.ellipsis, style: const TextStyle(color: AlfaColors.textMuted, fontSize: 12))),
    ]),
  );
}

class ResponsiveGrid extends StatelessWidget {
  final List<Widget> children;
  final double minTileWidth;
  const ResponsiveGrid({super.key, required this.children, this.minTileWidth = 210});
  @override
  Widget build(BuildContext context) => LayoutBuilder(builder: (context, constraints) {
    final columns = math.max(1, constraints.maxWidth ~/ minTileWidth);
    return GridView.count(crossAxisCount: columns, shrinkWrap: true, physics: const NeverScrollableScrollPhysics(), childAspectRatio: 1.55, crossAxisSpacing: 12, mainAxisSpacing: 12, children: children);
  });
}

class EmptyState extends StatelessWidget {
  final IconData icon;
  final String title;
  final String subtitle;
  const EmptyState({super.key, required this.icon, required this.title, required this.subtitle});
  @override
  Widget build(BuildContext context) => Center(child: GlassPanel(child: Column(mainAxisSize: MainAxisSize.min, children: [Icon(icon, size: 48, color: AlfaColors.lineStrong), const SizedBox(height: 12), Text(title, style: const TextStyle(fontWeight: FontWeight.w800)), const SizedBox(height: 6), Text(subtitle, textAlign: TextAlign.center, style: const TextStyle(color: AlfaColors.textMuted))])));
}

class AvatarOrb extends StatefulWidget {
  final String state;
  const AvatarOrb({super.key, required this.state});
  @override
  State<AvatarOrb> createState() => _AvatarOrbState();
}

class _AvatarOrbState extends State<AvatarOrb> with SingleTickerProviderStateMixin {
  late final AnimationController _controller = AnimationController(vsync: this, duration: const Duration(seconds: 4))..repeat();
  @override void dispose() { _controller.dispose(); super.dispose(); }
  @override
  Widget build(BuildContext context) => AnimatedBuilder(animation: _controller, builder: (_, __) {
    final pulse = .55 + math.sin(_controller.value * math.pi * 2) * .12;
    return Container(
      width: 170, height: 170,
      decoration: BoxDecoration(shape: BoxShape.circle, gradient: RadialGradient(colors: [AlfaColors.cyan.withOpacity(.95), AlfaColors.electricBlue.withOpacity(pulse), Colors.transparent]), boxShadow: [BoxShadow(color: AlfaColors.neonBlue.withOpacity(.35), blurRadius: 48)]),
      child: Center(child: Container(width: 92, height: 92, decoration: BoxDecoration(shape: BoxShape.circle, color: AlfaColors.voidBlack.withOpacity(.72), border: Border.all(color: AlfaColors.cyan.withOpacity(.75))), child: Center(child: Text(widget.state.toUpperCase(), style: const TextStyle(fontSize: 10, fontWeight: FontWeight.w900, letterSpacing: 1.4))))),
    );
  });
}
