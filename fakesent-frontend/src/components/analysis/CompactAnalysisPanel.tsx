import { useAnalysis } from "../../hooks/useAnalysis";
import { useAnalysisStore } from "../../stores/useAnalysisStore";
import { OverallScoreGauge } from "../charts/OverallScoreGauge";
import { ModalityScoreBar, ModalityStatus } from "../charts/ModalityScoreBar";
import { MiniTimelineSparkline } from "../charts/MiniTimelineSparkline";
import { theme } from "../../constants/theme";

function getModalityStatus(score: number): ModalityStatus {
  if (score < 40) return "uyumsuz";
  if (score < 65) return "anomali";
  return "tutarli";
}

export function CompactAnalysisPanel() {
  const { currentSnapshot, status, timeline, stop } = useAnalysis();
  const toggleDashboard = useAnalysisStore((state) => state.toggleDashboard);

  if (!currentSnapshot) return null;

  const isSuspicious = status === "warning" || status === "critical";
  // Koyu bir kırmızı tonu (Alert Red'in daha karanlık hali arka plan için)
  const panelBg = isSuspicious ? "#2b1010" : theme.colors.bgSurface; 
  const panelBorder = isSuspicious ? theme.colors.danger : theme.colors.bgSurfaceAlt;

  return (
    <div style={{ padding: "1.5rem", color: theme.colors.textPrimary, background: panelBg, borderRadius: "8px", border: `1px solid ${panelBorder}`, transition: "all 0.3s ease", boxShadow: "0 4px 12px rgba(0,0,0,0.5)", fontFamily: "sans-serif" }}>
      
      {isSuspicious && (
        <div style={{ background: theme.colors.danger, color: theme.colors.textPrimary, padding: "6px 8px", borderRadius: "4px", fontSize: "0.75rem", fontWeight: "bold", textAlign: "center", marginBottom: "15px", letterSpacing: "1px", fontFamily: theme.font.heading }}>
          ŞÜPHELİ — POTANSİYEL MANİPÜLASYON
        </div>
      )}

      <div style={{ display: "flex", justifyContent: "center", marginBottom: "20px" }}>
        <OverallScoreGauge score={currentSnapshot.overallScore} status={status} />
      </div>
      
      <div>
        {/* Sadece görsel uyum bırakıldı, ses metrikleri silindi */}
        <ModalityScoreBar 
          label="Yüz ↔ Dudak Uyumu" 
          score={Math.round(currentSnapshot.scores?.faceLip || 0)} 
          status={getModalityStatus(currentSnapshot.scores?.faceLip || 0)} 
        />
      </div>

      <MiniTimelineSparkline data={timeline} />

      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "20px" }}>
        <div style={{ fontStyle: "italic", color: theme.colors.textSecondary, fontSize: "0.8rem", display: "flex", alignItems: "center", gap: "6px" }}>
          <span style={{ display: "inline-block", width: "8px", height: "8px", borderRadius: "50%", background: isSuspicious ? theme.colors.danger : theme.colors.accentPrimary }}></span>
          Analiz devam ediyor...
        </div>
        <div style={{ display: "flex", gap: "8px" }}>
          <button onClick={() => toggleDashboard(true)} style={{ padding: "6px 12px", background: "transparent", color: theme.colors.accentPrimary, border: `1px solid ${theme.colors.accentPrimary}`, borderRadius: "4px", cursor: "pointer", fontSize: "0.8rem", fontWeight: "bold" }}>
            Detaylı Görünüm
          </button>
          <button onClick={stop} style={{ padding: "6px 12px", background: theme.colors.bgSurfaceAlt, color: theme.colors.textSecondary, border: "none", borderRadius: "4px", cursor: "pointer", fontSize: "0.8rem" }}>
            Durdur
          </button>
        </div>
      </div>
    </div>
  );
}