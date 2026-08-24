import { theme } from "../../constants/theme";

export type ModalityStatus = "tutarli" | "anomali" | "uyumsuz";

export function ModalityScoreBar({ label, score, status }: { label: string; score: number; status: ModalityStatus }) {
  // ÇÖZÜM BURADA: ": string" tipini belirttik
  let color: string = theme.colors.safe; 
  if (status === "anomali") color = theme.colors.warning; 
  if (status === "uyumsuz") color = theme.colors.danger; 

  return (
    <div style={{ marginBottom: "12px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "6px", fontSize: "0.85rem", color: theme.colors.textSecondary }}>
        <span>{label}</span>
        <span style={{ fontWeight: "bold", color: theme.colors.textPrimary }}>{score}%</span>
      </div>
      <div style={{ height: "6px", background: theme.colors.bgSurfaceAlt, borderRadius: "3px", overflow: "hidden" }}>
        <div style={{ width: `${score}%`, height: "100%", background: color, transition: "width 0.5s ease, background-color 0.5s ease" }}></div>
      </div>
    </div>
  );
}