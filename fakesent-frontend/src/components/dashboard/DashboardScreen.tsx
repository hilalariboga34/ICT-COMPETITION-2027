import { useAnalysisStore } from "../../stores/useAnalysisStore";
import { useAnalysis } from "../../hooks/useAnalysis";
import { theme } from "../../constants/theme";

export function DashboardScreen() {
  const toggleDashboard = useAnalysisStore((state) => state.toggleDashboard);
  const { currentSnapshot, status, timeline } = useAnalysis();

  const score = currentSnapshot?.overallScore || 0;
  // Olası tip hatalarını önlemek için scores?.faceLip yapıldı
  const faceLip = currentSnapshot?.scores?.faceLip || 0;

  // Atıl değişken hatası giderildi, yarıçap doğrudan 60'a çıkarıldı ve değişkenler kullanıma alındı
  const radius = 60; 
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (score / 100) * circumference;
  
  const isSuspicious = status === "warning" || status === "critical";
  const mainColor = isSuspicious ? theme.colors.danger : theme.colors.accentPrimary;
  const statusText = isSuspicious ? "ŞÜPHELİ" : "YÜKSEK İHTİMALLE GERÇEK";
  const statusColor = isSuspicious ? theme.colors.danger : theme.colors.safe;

  const renderMiniChart = (color: string) => {
    if (!timeline || timeline.length === 0) return null;
    const recent = timeline.slice(-20);
    const step = 100 / Math.max(recent.length - 1, 1);
    const points = recent.map((d, i) => `${i * step},${20 - (d.overallScore / 100) * 20}`).join(" ");
    return (
      <svg width="100%" height="20" viewBox="0 0 100 20" preserveAspectRatio="none" style={{ marginTop: "10px" }}>
        <polyline points={points} fill="none" stroke={color} strokeWidth="1.5" strokeLinejoin="round" />
      </svg>
    );
  };

  return (
    <div style={{ padding: "15px 25px", color: theme.colors.textPrimary, background: theme.colors.bgPrimary, minHeight: "100vh", fontSize: "0.85rem" }}>
      
      {/* ÜST BİLGİ ÇUBUĞU */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "15px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "15px" }}>
          <img src="/logo.png" alt="FakeSent Logo" style={{ height: "28px", borderRadius: "6px", background: "#fff", padding: "2px 8px" }} />
          <h1 style={{ color: theme.colors.accentPrimary, margin: 0, fontSize: "1.4rem", letterSpacing: "1px" }}>FakeSent <span style={{ color: theme.colors.textPrimary, fontWeight: "300" }}>| VISUAL AI ANALYSIS</span></h1>
          <div style={{ background: isSuspicious ? "#451a1a" : "#064e3b", color: statusColor, padding: "4px 10px", borderRadius: "12px", fontSize: "0.75rem", display: "flex", alignItems: "center", gap: "6px" }}>
            <span style={{ width: "8px", height: "8px", background: statusColor, borderRadius: "50%", display: "inline-block", animation: "pulse 2s infinite" }}></span>
            CANLI ANALİZ {isSuspicious && "- YÜKSEK RİSK"}
          </div>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "20px", color: theme.colors.textSecondary, fontSize: "0.8rem" }}>
          <span>Oturum ID: 7f3a2e9b-4d21...</span>
          <button onClick={() => toggleDashboard(false)} style={{ padding: "8px 16px", background: theme.colors.bgSurfaceAlt, color: theme.colors.textPrimary, border: "none", borderRadius: "4px", cursor: "pointer", fontWeight: "bold" }}>
            ✕ Toplantıya Dön
          </button>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "300px 1fr", gap: "20px" }}>
        
        {/* SOL KOLON */}
        <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
          <div style={{ background: theme.colors.bgSurface, padding: "25px", borderRadius: "8px", border: `1px solid ${theme.colors.bgSurfaceAlt}`, textAlign: "center" }}>
            <h3 style={{ margin: "0 0 20px 0", fontSize: "0.85rem", color: theme.colors.textSecondary, textAlign: "left" }}>GENEL GÖRSEL DEĞERLENDİRME</h3>
            
            <div style={{ position: "relative", width: "140px", height: "140px", margin: "0 auto" }}>
              <svg width="140" height="140" viewBox="0 0 140 140">
                {/* Değişkenler dinamik olarak buraya bağlandı */}
                <circle cx="70" cy="70" r={radius} fill="none" stroke={theme.colors.bgSurfaceAlt} strokeWidth="10" />
                <circle cx="70" cy="70" r={radius} fill="none" stroke={mainColor} strokeWidth="10"
                  strokeDasharray={circumference} strokeDashoffset={strokeDashoffset}
                  strokeLinecap="round" transform="rotate(-90 70 70)"
                  style={{ transition: "stroke-dashoffset 0.5s ease, stroke 0.5s ease" }} />
              </svg>
              <div style={{ position: "absolute", top: 0, left: 0, width: "100%", height: "100%", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "2.5rem", fontWeight: "bold", color: mainColor }}>
                {Math.round(score)}%
              </div>
            </div>

            <div style={{ color: statusColor, fontWeight: "bold", marginTop: "20px", fontSize: "1.1rem", letterSpacing: "0.5px" }}>{statusText}</div>
            <div style={{ color: statusColor, fontSize: "0.8rem", border: `1px solid ${statusColor}`, display: "inline-block", padding: "4px 12px", borderRadius: "12px", marginTop: "10px" }}>
              Risk Seviyesi: {isSuspicious ? "YÜKSEK" : "DÜŞÜK"}
            </div>
          </div>

          <div style={{ background: theme.colors.bgSurface, padding: "20px", borderRadius: "8px", border: `1px solid ${theme.colors.bgSurfaceAlt}`, flex: 1 }}>
            <h3 style={{ margin: "0 0 15px 0", fontSize: "0.85rem", color: theme.colors.textSecondary }}>SİSTEM ÖZETİ</h3>
            <div style={{ display: "flex", flexDirection: "column", gap: "12px", color: theme.colors.textPrimary }}>
              <div style={{ display: "flex", justifyContent: "space-between" }}><span>İşlenen FPS</span><span style={{ fontWeight: "bold" }}>24.7</span></div>
              <div style={{ display: "flex", justifyContent: "space-between" }}><span>Model Sürümü</span><span style={{ fontWeight: "bold" }}>FakeSent Vision v1.0</span></div>
              <div style={{ display: "flex", justifyContent: "space-between" }}><span>Cihaz Hızlandırması</span><span style={{ color: theme.colors.safe, fontWeight: "bold" }}>Edge AI (NPU) Aktif</span></div>
              <div style={{ display: "flex", justifyContent: "space-between" }}><span>İşlem Gecikmesi</span><span style={{ fontWeight: "bold" }}>32 ms</span></div>
            </div>
          </div>
        </div>

        {/* SAĞ KOLON (Görsel Analiz) */}
        <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
          <div style={{ background: theme.colors.bgSurface, padding: "20px", borderRadius: "8px", border: `1px solid ${theme.colors.bgSurfaceAlt}`, display: "flex", flexDirection: "column", flex: 1 }}>
            <h3 style={{ margin: "0 0 15px 0", fontSize: "0.85rem", color: theme.colors.textSecondary }}>CANLI YÜZ VE MİMİK TAKİBİ</h3>
            <div style={{ flex: 1, background: theme.colors.bgSurfaceAlt, borderRadius: "6px", position: "relative", display: "flex", alignItems: "center", justifyContent: "center", minHeight: "300px", overflow: "hidden" }}>
              <div style={{ position: "absolute", top: 0, left: 0, right: 0, bottom: 0, backgroundImage: `linear-gradient(${theme.colors.accentPrimary}1A 1px, transparent 1px), linear-gradient(90deg, ${theme.colors.accentPrimary}1A 1px, transparent 1px)`, backgroundSize: "20px 20px" }}></div>
              <div style={{ zIndex: 1, color: theme.colors.textMuted, textAlign: "center" }}>
                <div style={{ fontSize: "2.5rem", marginBottom: "15px" }}>👁️</div>
                <div style={{ fontSize: "1.1rem", marginBottom: "8px" }}>Görsel ROI (Region of Interest) Alanı</div>
                <div style={{ fontSize: "0.8rem" }}>Sadece Yüz, Göz ve Dudak hareketleri işleniyor.</div>
              </div>
            </div>
          </div>

          <div style={{ background: theme.colors.bgSurface, padding: "20px", borderRadius: "8px", border: `1px solid ${theme.colors.bgSurfaceAlt}` }}>
            <h3 style={{ margin: "0 0 15px 0", fontSize: "0.85rem", color: theme.colors.textSecondary }}>GÖRSEL UYUM METRİĞİ</h3>
            <div style={{ background: theme.colors.bgPrimary, padding: "20px", borderRadius: "8px", border: `1px solid ${theme.colors.bgSurfaceAlt}` }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "10px" }}>
                <div style={{ fontSize: "1rem", color: theme.colors.textPrimary, fontWeight: "bold" }}>YÜZ ↔ DUDAK SENKRONİZASYONU</div>
                <div style={{ fontSize: "2.2rem", fontWeight: "bold", color: faceLip > 65 ? theme.colors.safe : theme.colors.warning }}>{Math.round(faceLip)}%</div>
              </div>
              <div style={{ width: "100%", height: "8px", background: theme.colors.bgSurfaceAlt, borderRadius: "4px", overflow: "hidden", marginBottom: "15px" }}>
                <div style={{ width: `${faceLip}%`, height: "100%", background: faceLip > 65 ? theme.colors.safe : theme.colors.warning, transition: "width 0.5s ease" }}></div>
              </div>
              <div style={{ fontSize: "0.75rem", color: theme.colors.textMuted }}>Görsel Uyum Zaman Çizelgesi</div>
              {renderMiniChart(faceLip > 65 ? theme.colors.safe : theme.colors.warning)}
            </div>
          </div>
        </div>

      </div> 

      {/* ALT ZAMAN ÇİZELGESİ */}
      <div style={{ marginTop: "20px", background: theme.colors.bgSurface, padding: "20px", borderRadius: "8px", border: `1px solid ${theme.colors.bgSurfaceAlt}` }}>
        <h3 style={{ margin: "0 0 15px 0", fontSize: "0.85rem", color: theme.colors.textSecondary }}>GENEL ANALİZ ZAMAN ÇİZELGESİ</h3>
        <div style={{ height: "120px", background: theme.colors.bgSurfaceAlt, borderRadius: "6px", position: "relative", overflow: "hidden" }}>
            <svg width="100%" height="100%" preserveAspectRatio="none" viewBox="0 0 100 100">
              <line x1="0" y1="25" x2="100" y2="25" stroke={theme.colors.textMuted} strokeWidth="0.5" opacity="0.3" />
              <line x1="0" y1="50" x2="100" y2="50" stroke={theme.colors.textMuted} strokeWidth="0.5" opacity="0.3" />
              <line x1="0" y1="75" x2="100" y2="75" stroke={theme.colors.textMuted} strokeWidth="0.5" opacity="0.3" />
              <polyline points="0,60 10,55 20,65 30,50 40,70 50,45 60,80 70,55 80,60 90,40 100,65" fill="none" stroke={theme.colors.accentPrimary} strokeWidth="2" />
            </svg>
            <div style={{ position: "absolute", bottom: "10px", left: "20px", display: "flex", gap: "15px", fontSize: "0.75rem", color: theme.colors.textPrimary }}>
              <span style={{ display: "flex", alignItems: "center", gap: "6px" }}><div style={{ width: "10px", height: "10px", background: theme.colors.accentPrimary, borderRadius: "50%" }}></div> Görsel Risk Skoru</span>
            </div>
        </div>
      </div>
      
    </div>
  );
}