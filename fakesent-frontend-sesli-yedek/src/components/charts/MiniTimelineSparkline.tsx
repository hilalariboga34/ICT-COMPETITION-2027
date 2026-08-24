import type { AnalysisSnapshot } from "../../types/analysis";
import { theme } from "../../constants/theme";

export function MiniTimelineSparkline({ data }: { data: AnalysisSnapshot[] }) {
  if (data.length === 0) return <div style={{ height: "40px", color: theme.colors.textMuted }}>Bekleniyor...</div>;

  const width = 300;
  const height = 40;
  const recentData = data.slice(-25);
  const stepX = width / Math.max(recentData.length - 1, 1);

  const points = recentData.map((d, i) => {
    const x = i * stepX;
    const y = height - ((d.overallScore) / 100) * height;
    return `${x},${y}`;
  }).join(" ");

  return (
    <div style={{ marginTop: "20px" }}>
      <div style={{ fontSize: "0.75rem", color: theme.colors.textSecondary, marginBottom: "8px", textTransform: "uppercase", letterSpacing: "1px", fontFamily: theme.font.heading }}>
        Analiz Zaman Çizelgesi
      </div>
      <svg width="100%" height={height} viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none">
        <polyline points={points} fill="none" stroke={theme.colors.accentPrimary} strokeWidth="2" strokeLinejoin="round" />
      </svg>
    </div>
  );
}