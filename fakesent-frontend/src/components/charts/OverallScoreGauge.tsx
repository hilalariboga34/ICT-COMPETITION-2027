import type { AnalysisStatus } from "../../types/analysis";
import { theme } from "../../constants/theme";

export function OverallScoreGauge({ score, status }: { score: number; status: AnalysisStatus }) {
  const radius = 40;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (score / 100) * circumference;

  // ÇÖZÜM BURADA: ": string" tipini belirttik
  let color: string = theme.colors.accentPrimary; 
  if (status === "warning") color = theme.colors.warning;
  if (status === "critical") color = theme.colors.danger; 

  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
      <svg width="100" height="100" viewBox="0 0 100 100">
        <circle cx="50" cy="50" r={radius} fill="none" stroke={theme.colors.bgSurfaceAlt} strokeWidth="8" />
        <circle
          cx="50" cy="50" r={radius} fill="none" stroke={color} strokeWidth="8"
          strokeDasharray={circumference} strokeDashoffset={strokeDashoffset}
          strokeLinecap="round" transform="rotate(-90 50 50)"
          style={{ transition: "stroke-dashoffset 0.5s ease, stroke 0.5s ease" }}
        />
        <text x="50" y="56" textAnchor="middle" fill={theme.colors.textPrimary} fontSize="1.5rem" fontWeight="bold" fontFamily={theme.font.heading}>
          {Math.round(score)}%
        </text>
      </svg>
      <div style={{ color, fontSize: "0.8rem", marginTop: "8px", fontWeight: "bold", letterSpacing: "1px", fontFamily: theme.font.heading }}>
        {status.toUpperCase()}
      </div>
    </div>
  );
}