import { useState } from "react";
import { PreStartPanel } from "../analysis/PreStartPanel";
import { CompactAnalysisPanel } from "../analysis/CompactAnalysisPanel";
import { DashboardScreen } from "../dashboard/DashboardScreen";
import { ErrorBanner } from "../status/ErrorBanner";
import { useAnalysis } from "../../hooks/useAnalysis";
import { useAnalysisStore } from "../../stores/useAnalysisStore";
import { APP_CONFIG } from "../../constants/appConfig";
import { theme } from "../../constants/theme";

export function MeetingScreen() {
  const { status } = useAnalysis();
  const [dismissed, setDismissed] = useState(false);
  
  const dashboardOpen = useAnalysisStore((state) => state.dashboardOpen);
  const currentError = useAnalysisStore((state) => state.currentError);
  const setError = useAnalysisStore((state) => state.setError);
  const clearError = useAnalysisStore((state) => state.clearError);

  if (dashboardOpen) {
    return <DashboardScreen />;
  }

  return (
    <div style={{ position: "relative", width: "100vw", height: "100vh", background: theme.colors.bgPrimary, display: "flex", flexDirection: "column", overflow: "hidden", fontFamily: theme.font.heading }}>
      
      <header style={{ height: "60px", background: theme.colors.bgSurface, borderBottom: `1px solid ${theme.colors.bgSurfaceAlt}`, display: "flex", alignItems: "center", justifyContent: "space-between", padding: "0 20px", color: theme.colors.textPrimary }}>
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          {/* YENİ: Mavi nokta kaldırıldı, yerine public klasöründeki logomuz eklendi */}
          <img 
            src="/logo.png" 
            alt="FakeSent Logo" 
            style={{ height: "26px", borderRadius: "6px", background: "#fff", padding: "2px 8px" }} 
          />
          <span style={{ fontWeight: "bold", letterSpacing: "0.5px", fontSize: "1.1rem" }}>{APP_CONFIG.name} Konferans Odası</span>
        </div>
        <div style={{ fontSize: "0.85rem", color: theme.colors.textSecondary }}>Güvenli Toplantı Oturumu</div>
      </header>

      <div style={{ flex: 1, display: "grid", gridTemplateColumns: "1fr 1fr", gap: "15px", padding: "20px", position: "relative" }}>
        
        <div style={{ background: theme.colors.bgSurfaceAlt, borderRadius: "12px", display: "flex", alignItems: "center", justifyContent: "center", color: theme.colors.textSecondary, fontSize: "1.2rem", position: "relative" }}>
          <span>Karşı Tarafın Kamera Akışı (Katılımcı A)</span>
          <div style={{ position: "absolute", bottom: "12px", left: "12px", background: "rgba(0,0,0,0.6)", padding: "4px 8px", borderRadius: "4px", color: theme.colors.textPrimary, fontSize: "0.8rem" }}>Ahmet Yılmaz</div>
        </div>
        
        <div style={{ background: theme.colors.bgSurfaceAlt, borderRadius: "12px", display: "flex", alignItems: "center", justifyContent: "center", color: theme.colors.textSecondary, fontSize: "1.2rem", position: "relative" }}>
          <span>Karşı Tarafın Kamera Akışı (Katılımcı B)</span>
          <div style={{ position: "absolute", bottom: "12px", left: "12px", background: "rgba(0,0,0,0.6)", padding: "4px 8px", borderRadius: "4px", color: theme.colors.textPrimary, fontSize: "0.8rem" }}>Mehmet Demir</div>
        </div>

        <div style={{ position: "absolute", top: "20px", right: "20px", width: "360px", zIndex: 100, display: "flex", flexDirection: "column", gap: "15px" }}>
          <ErrorBanner error={currentError} onClear={clearError} />
          {status === "idle" && !dismissed && <PreStartPanel onDismiss={() => setDismissed(true)} />}
          {status === "idle" && dismissed && (
            <button onClick={() => setDismissed(false)} style={{ padding: "10px 16px", background: theme.colors.accentPrimary, color: theme.colors.textPrimary, border: "none", borderRadius: "6px", cursor: "pointer", fontWeight: "bold", width: "100%" }}>Güvenlik Panelini Aç</button>
          )}
          {status === "starting" && (
            <div style={{ padding: "1.5rem", color: theme.colors.textPrimary, background: theme.colors.bgSurface, borderRadius: "8px", border: `1px solid ${theme.colors.bgSurfaceAlt}`, textAlign: "center" }}>
              <div style={{ color: theme.colors.accentPrimary, fontWeight: "bold", marginBottom: "8px" }}>Model Hazırlanıyor...</div>
              <div style={{ fontSize: "0.85rem", color: theme.colors.textSecondary }}>Sensörler ve AI motoru kalibre ediliyor.</div>
            </div>
          )}
          {(status === "analyzing" || status === "warning" || status === "critical") && <CompactAnalysisPanel />}
        </div>

        <div style={{ position: "absolute", bottom: "20px", left: "20px", zIndex: 100, background: theme.colors.bgSurface, padding: "10px", borderRadius: "8px", border: `1px solid ${theme.colors.warning}` }}>
          <div style={{ fontSize: "0.7rem", color: theme.colors.warning, marginBottom: "8px", fontWeight: "bold", textTransform: "uppercase" }}>Test (Jüri Demosu İçin)</div>
          <div style={{ display: "flex", gap: "8px" }}>
            <button onClick={() => setError("camera_unavailable")} style={{ fontSize: "0.75rem", padding: "6px 10px", cursor: "pointer", borderRadius: "4px", border: "none" }}>Kamera Hatası</button>
            <button onClick={() => setError("connection_lost")} style={{ fontSize: "0.75rem", padding: "6px 10px", cursor: "pointer", borderRadius: "4px", border: "none" }}>Bağlantı Koptu</button>
            <button onClick={() => clearError()} style={{ fontSize: "0.75rem", padding: "6px 10px", cursor: "pointer", background: theme.colors.safe, color: "white", border: "none", borderRadius: "4px" }}>Temizle</button>
          </div>
        </div>

      </div>
    </div>
  );
}