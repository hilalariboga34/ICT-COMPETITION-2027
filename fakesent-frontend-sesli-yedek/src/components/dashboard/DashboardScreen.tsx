import { useAnalysisStore } from "../../stores/useAnalysisStore";
import { useAnalysis } from "../../hooks/useAnalysis";
import { theme } from "../../constants/theme";

export function DashboardScreen() {
  const toggleDashboard = useAnalysisStore((state) => state.toggleDashboard);
  const { currentSnapshot, status, timeline } = useAnalysis();

  const score = currentSnapshot?.overallScore || 0;
  const audioLip = currentSnapshot?.scores.audioLip || 0;
  const audioFace = currentSnapshot?.scores.audioFace || 0;
  const faceLip = currentSnapshot?.scores.faceLip || 0;

  const radius = 50;
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
          {/* YENİ EKLENEN LOGO */}
          <img 
            src="/logo.png" 
            alt="FakeSent Logo" 
            style={{ height: "28px", borderRadius: "6px", background: "#fff", padding: "2px 8px" }} 
          />
          <h1 style={{ color: theme.colors.accentPrimary, margin: 0, fontSize: "1.4rem", letterSpacing: "1px" }}>FakeSent <span style={{ color: theme.colors.textPrimary, fontWeight: "300" }}>| REAL-TIME AI ANALYSIS</span></h1>
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

      {/* ANA IZGARA (GRID) YAPISI */}
      <div style={{ display: "grid", gridTemplateColumns: "250px 1fr 350px", gap: "15px" }}>
        
        {/* SOL KOLON */}
        <div style={{ display: "flex", flexDirection: "column", gap: "15px" }}>
          <div style={{ background: theme.colors.bgSurface, padding: "20px", borderRadius: "8px", border: `1px solid ${theme.colors.bgSurfaceAlt}`, textAlign: "center" }}>
            <h3 style={{ margin: "0 0 15px 0", fontSize: "0.85rem", color: theme.colors.textSecondary, textAlign: "left" }}>GENEL DEĞERLENDİRME</h3>
            
            <div style={{ position: "relative", width: "120px", height: "120px", margin: "0 auto" }}>
              <svg width="120" height="120" viewBox="0 0 120 120">
                <circle cx="60" cy="60" r={radius} fill="none" stroke={theme.colors.bgSurfaceAlt} strokeWidth="8" />
                <circle cx="60" cy="60" r={radius} fill="none" stroke={mainColor} strokeWidth="8"
                  strokeDasharray={circumference} strokeDashoffset={strokeDashoffset}
                  strokeLinecap="round" transform="rotate(-90 60 60)"
                  style={{ transition: "stroke-dashoffset 0.5s ease, stroke 0.5s ease" }} />
              </svg>
              <div style={{ position: "absolute", top: 0, left: 0, width: "100%", height: "100%", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "2.5rem", fontWeight: "bold", color: mainColor }}>
                {Math.round(score)}%
              </div>
            </div>

            <div style={{ color: statusColor, fontWeight: "bold", marginTop: "15px", letterSpacing: "0.5px" }}>{statusText}</div>
            <div style={{ color: statusColor, fontSize: "0.75rem", border: `1px solid ${statusColor}`, display: "inline-block", padding: "2px 8px", borderRadius: "10px", marginTop: "8px" }}>
              Risk Seviyesi: {isSuspicious ? "YÜKSEK" : "DÜŞÜK"}
            </div>
          </div>

          <div style={{ background: theme.colors.bgSurface, padding: "15px", borderRadius: "8px", border: `1px solid ${theme.colors.bgSurfaceAlt}`, flex: 1 }}>
            <h3 style={{ margin: "0 0 15px 0", fontSize: "0.85rem", color: theme.colors.textSecondary }}>ANALİZ ÖZETİ</h3>
            <div style={{ display: "flex", flexDirection: "column", gap: "10px", color: theme.colors.textPrimary }}>
              <div style={{ display: "flex", justifyContent: "space-between" }}><span>İşlenen FPS</span><span>24.7</span></div>
              <div style={{ display: "flex", justifyContent: "space-between" }}><span>Model Sürümü</span><span>FakeSent v2.3.1</span></div>
              <div style={{ display: "flex", justifyContent: "space-between" }}><span>Cihaz</span><span>Edge AI (NPU)</span></div>
            </div>
          </div>
        </div>

        {/* ORTA KOLON */}
        <div style={{ display: "flex", flexDirection: "column", gap: "15px" }}>
          <div style={{ background: theme.colors.bgSurface, padding: "15px", borderRadius: "8px", border: `1px solid ${theme.colors.bgSurfaceAlt}`, display: "flex", flexDirection: "column" }}>
            <h3 style={{ margin: "0 0 15px 0", fontSize: "0.85rem", color: theme.colors.textSecondary }}>YÜZ & DUDAK ANALİZİ</h3>
            <div style={{ flex: 1, background: theme.colors.bgSurfaceAlt, borderRadius: "6px", position: "relative", display: "flex", alignItems: "center", justifyContent: "center", minHeight: "250px", overflow: "hidden" }}>
              <div style={{ position: "absolute", top: 0, left: 0, right: 0, bottom: 0, backgroundImage: `linear-gradient(${theme.colors.accentPrimary}1A 1px, transparent 1px), linear-gradient(90deg, ${theme.colors.accentPrimary}1A 1px, transparent 1px)`, backgroundSize: "20px 20px" }}></div>
              <div style={{ zIndex: 1, color: theme.colors.textMuted, textAlign: "center" }}>
                <div style={{ fontSize: "2rem", marginBottom: "10px" }}>📷</div>
                <div>Karşı Tarafın Kamera Akışı ve ROI Alanı<br/><span style={{ fontSize: "0.75rem" }}>(Gerçek API bağlandığında canlı akış buraya gelecek)</span></div>
              </div>
            </div>
          </div>

          <div style={{ background: theme.colors.bgSurface, padding: "15px", borderRadius: "8px", border: `1px solid ${theme.colors.bgSurfaceAlt}` }}>
            <h3 style={{ margin: "0 0 15px 0", fontSize: "0.85rem", color: theme.colors.textSecondary }}>KARŞILAŞTIRMALI UYUM ANALİZİ</h3>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "10px" }}>
              {[
                { label: "AUDIO ↔ LIP", val: Math.round(audioLip), color: audioLip > 65 ? theme.colors.safe : theme.colors.warning },
                { label: "AUDIO ↔ FACE", val: Math.round(audioFace), color: audioFace > 65 ? theme.colors.safe : theme.colors.warning },
                { label: "FACE ↔ LIP", val: Math.round(faceLip), color: faceLip > 65 ? theme.colors.safe : theme.colors.warning }
              ].map((item, i) => (
                <div key={i} style={{ background: theme.colors.bgPrimary, padding: "15px", borderRadius: "8px", border: `1px solid ${theme.colors.bgSurfaceAlt}` }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "10px" }}>
                    <div style={{ fontSize: "0.8rem", color: theme.colors.textPrimary, fontWeight: "bold" }}>{item.label}</div>
                    <div style={{ fontSize: "1.8rem", fontWeight: "bold", color: item.color }}>{item.val}%</div>
                  </div>
                  <div style={{ width: "100%", height: "6px", background: theme.colors.bgSurfaceAlt, borderRadius: "3px", overflow: "hidden", marginBottom: "10px" }}>
                    <div style={{ width: `${item.val}%`, height: "100%", background: item.color, transition: "width 0.5s ease" }}></div>
                  </div>
                  <div style={{ fontSize: "0.65rem", color: theme.colors.textMuted }}>Uyum Zaman Çizelgesi</div>
                  {renderMiniChart(item.color)}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* SAĞ KOLON */}
        <div style={{ display: "flex", flexDirection: "column", gap: "15px" }}>
          <div style={{ background: theme.colors.bgSurface, padding: "15px", borderRadius: "8px", border: `1px solid ${theme.colors.bgSurfaceAlt}` }}>
            <h3 style={{ margin: "0 0 15px 0", fontSize: "0.85rem", color: theme.colors.textSecondary }}>CANLI SES ANALİZİ</h3>
            <div style={{ marginBottom: "15px" }}>
              <div style={{ fontSize: "0.75rem", color: theme.colors.textSecondary, marginBottom: "5px" }}>DALGA FORMU</div>
              <div style={{ height: "50px", display: "flex", alignItems: "center", gap: "2px", overflow: "hidden", background: theme.colors.bgPrimary, padding: "5px", borderRadius: "4px" }}>
                {[...Array(60)].map((_, i) => {
                   const height = 20 + Math.random() * 80;
                   return <div key={i} style={{ flex: 1, background: theme.colors.accentPrimary, height: `${height}%`, borderRadius: "2px" }}></div>
                })}
              </div>
            </div>
            <div>
              <div style={{ fontSize: "0.75rem", color: theme.colors.textSecondary, marginBottom: "5px" }}>MEL-SPEKTROGRAM</div>
              <div style={{ height: "80px", background: `url('data:image/svg+xml;utf8,<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"100%\" height=\"100%\"><defs><linearGradient id=\"g\" x1=\"0\" y1=\"1\" x2=\"0\" y2=\"0\"><stop offset=\"0%\" stop-color=\"%23000\"/><stop offset=\"30%\" stop-color=\"%234c1d95\"/><stop offset=\"60%\" stop-color=\"%23be185d\"/><stop offset=\"100%\" stop-color=\"%23f59e0b\"/></linearGradient></defs><rect width=\"100%\" height=\"100%\" fill=\"url(%23g)\"/><filter id=\"noise\"><feTurbulence type=\"fractalNoise\" baseFrequency=\"0.1 0.5\" numOctaves=\"3\" stitchTiles=\"stitch\"/></filter><rect width=\"100%\" height=\"100%\" filter=\"url(%23noise)\" opacity=\"0.4\" mix-blend-mode=\"multiply\"/></svg>')`, borderRadius: "4px", backgroundSize: "cover" }}></div>
            </div>
          </div>

          <div style={{ background: theme.colors.bgSurface, padding: "15px", borderRadius: "8px", border: `1px solid ${theme.colors.bgSurfaceAlt}` }}>
            <h3 style={{ margin: "0 0 15px 0", fontSize: "0.85rem", color: theme.colors.textSecondary }}>SES METRİKLERİ</h3>
            <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
               {[
                 { label: "Pitch Stabilitesi", val: 91 },
                 { label: "Enerji Tutarlılığı", val: 87 },
                 { label: "Zamanlama Uyumu", val: 94 },
                 { label: "SNR Kalitesi", val: 88 }
               ].map((m, i) => (
                 <div key={i}>
                   <div style={{ display: "flex", justifyContent: "space-between", color: theme.colors.textPrimary, fontSize: "0.8rem", marginBottom: "4px" }}>
                     <span>{m.label}</span><span style={{color: theme.colors.safe, fontWeight: "bold"}}>{m.val}%</span>
                   </div>
                   <div style={{ width: "100%", height: "4px", background: theme.colors.bgSurfaceAlt, borderRadius: "2px" }}>
                     <div style={{ width: `${m.val}%`, height: "100%", background: theme.colors.safe, borderRadius: "2px" }}></div>
                   </div>
                 </div>
               ))}
            </div>
          </div>
        </div>
      </div> 

      {/* ALT ZAMAN ÇİZELGESİ VE SİSTEM DURUMU */}
      <div style={{ display: "flex", gap: "15px", marginTop: "15px" }}>
        
        <div style={{ flex: 1, background: theme.colors.bgSurface, padding: "15px", borderRadius: "8px", border: `1px solid ${theme.colors.bgSurfaceAlt}` }}>
          <h3 style={{ margin: "0 0 15px 0", fontSize: "0.85rem", color: theme.colors.textSecondary }}>ANALİZ ZAMAN ÇİZELGESİ</h3>
          <div style={{ height: "100px", background: theme.colors.bgSurfaceAlt, borderRadius: "6px", position: "relative", overflow: "hidden" }}>
             <svg width="100%" height="100%" preserveAspectRatio="none" viewBox="0 0 100 100">
               <line x1="0" y1="25" x2="100" y2="25" stroke={theme.colors.textMuted} strokeWidth="0.5" opacity="0.3" />
               <line x1="0" y1="50" x2="100" y2="50" stroke={theme.colors.textMuted} strokeWidth="0.5" opacity="0.3" />
               <line x1="0" y1="75" x2="100" y2="75" stroke={theme.colors.textMuted} strokeWidth="0.5" opacity="0.3" />
               
               <polyline points="0,60 10,55 20,65 30,50 40,70 50,45 60,80 70,55 80,60 90,40 100,65" fill="none" stroke={theme.colors.accentPrimary} strokeWidth="1.5" />
               <polyline points="0,80 10,75 20,85 30,70 40,90 50,65 60,95 70,75 80,80 90,60 100,85" fill="none" stroke={theme.colors.safe} strokeWidth="1.5" opacity="0.7"/>
               <polyline points="0,40 10,35 20,45 30,30 40,50 50,25 60,60 70,35 80,40 90,20 100,45" fill="none" stroke="#8b5cf6" strokeWidth="1.5" opacity="0.7"/>
             </svg>
             <div style={{ position: "absolute", bottom: "8px", left: "15px", display: "flex", gap: "15px", fontSize: "0.65rem", color: theme.colors.textPrimary }}>
                <span style={{ display: "flex", alignItems: "center", gap: "4px" }}><div style={{ width: "8px", height: "8px", background: theme.colors.accentPrimary, borderRadius: "50%" }}></div> AUDIO ↔ LIP</span>
                <span style={{ display: "flex", alignItems: "center", gap: "4px" }}><div style={{ width: "8px", height: "8px", background: theme.colors.safe, borderRadius: "50%" }}></div> AUDIO ↔ FACE</span>
                <span style={{ display: "flex", alignItems: "center", gap: "4px" }}><div style={{ width: "8px", height: "8px", background: "#8b5cf6", borderRadius: "50%" }}></div> FACE ↔ LIP</span>
             </div>
          </div>
        </div>

        <div style={{ width: "350px", background: theme.colors.bgSurface, padding: "15px", borderRadius: "8px", border: `1px solid ${theme.colors.bgSurfaceAlt}`, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div style={{ textAlign: "center" }}>
            <div style={{ fontSize: "1.2rem", marginBottom: "8px" }}>⚙️</div>
            <div style={{ fontSize: "0.7rem", color: theme.colors.textSecondary, marginBottom: "4px" }}>Edge AI</div>
            <div style={{ color: theme.colors.safe, fontSize: "0.8rem", fontWeight: "bold" }}>Aktif</div>
          </div>
          <div style={{ textAlign: "center" }}>
            <div style={{ fontSize: "1.2rem", marginBottom: "8px" }}>🖩</div>
            <div style={{ fontSize: "0.7rem", color: theme.colors.textSecondary, marginBottom: "4px" }}>NPU Kullanımı</div>
            <div style={{ color: theme.colors.safe, fontSize: "0.8rem", fontWeight: "bold" }}>68%</div>
          </div>
          <div style={{ textAlign: "center" }}>
            <div style={{ fontSize: "1.2rem", marginBottom: "8px" }}>⏱️</div>
            <div style={{ fontSize: "0.7rem", color: theme.colors.textSecondary, marginBottom: "4px" }}>İşlem Gecikmesi</div>
            <div style={{ color: theme.colors.safe, fontSize: "0.8rem", fontWeight: "bold" }}>32 ms</div>
          </div>
        </div>
      </div>
      
    </div>
  );
}