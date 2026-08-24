import { useState } from "react";
import { useAnalysisStore } from "../../stores/useAnalysisStore";
import { ErrorBanner } from "../status/ErrorBanner";
import { APP_CONFIG } from "../../constants/appConfig";
import { theme } from "../../constants/theme";

export function MeetingScreen() {
  const { 
    status, 
    participants, 
    currentError,
    startAnalysis, 
    stopAnalysis, 
    kickParticipant,
    reset,
    clearError
  } = useAnalysisStore();

  const [showKicked, setShowKicked] = useState(false);

  const activeParticipants = participants.filter(p => p.status !== "kicked" && p.status !== "kicking");
  const safeParticipants = activeParticipants.filter(p => p.status === "safe" || p.status === "idle");
  const suspiciousParticipants = activeParticipants.filter(p => p.status === "suspicious");
  const kickedParticipants = participants.filter(p => p.status === "kicked");

  // Soldaki ızgara (Grid) listesi: Sadece Kicked (tamamen atılmış) olanları filtreliyoruz
  const gridParticipants = participants.filter(p => p.status !== "kicked");

  return (
    <div style={{ width: "100vw", height: "100vh", background: theme.colors.bgPrimary, display: "flex", flexDirection: "column", fontFamily: theme.font.heading }}>
      
      {/* HEADER */}
      <header style={{ height: "60px", background: theme.colors.bgSurface, borderBottom: `1px solid ${theme.colors.bgSurfaceAlt}`, display: "flex", alignItems: "center", padding: "0 20px", color: theme.colors.textPrimary }}>
        <img src="/logo.png" alt="Logo" style={{ height: "26px", borderRadius: "6px", background: "#fff", padding: "2px 8px", marginRight: "12px" }} />
        <span style={{ fontWeight: "bold", fontSize: "1.1rem" }}>{APP_CONFIG.name} — Çoklu Konferans Güvenliği</span>
      </header>

      {/* ANA İÇERİK */}
      <div style={{ flex: 1, display: "flex", overflow: "hidden" }}>
        
        {/* SOL: 3x3 KAMERA IZGARASI */}
        <div style={{ flex: 1, padding: "20px", display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gridTemplateRows: "repeat(3, 1fr)", gap: "15px", position: "relative" }}>
          
          <div style={{ position: "absolute", top: "20px", left: "20px", right: "20px", zIndex: 100 }}>
            <ErrorBanner error={currentError} onClear={clearError} />
          </div>

          {/* SADECE AKTİF VE ÇIKARILMAKTA OLAN KAMERALARI RENDER ET */}
          {gridParticipants.map((p) => {
            const isKicking = p.status === "kicking";
            const isSuspicious = p.status === "suspicious";

            return (
              <div key={p.id} style={{ 
                background: isKicking ? "#2b1010" : theme.colors.bgSurfaceAlt, 
                borderRadius: "12px", 
                border: (isSuspicious && !isKicking) ? `2px solid ${theme.colors.danger}` : `2px solid transparent`,
                position: "relative",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                overflow: "hidden",
                transition: "all 0.3s ease"
              }}>
                {isKicking ? (
                  <span style={{ color: theme.colors.danger, fontWeight: "bold", fontSize: "0.9rem", animation: "pulse 1s infinite" }}>
                    TOPLANTIDAN ÇIKARILIYOR...
                  </span>
                ) : (
                  <>
                    <span style={{ color: theme.colors.textSecondary }}>Kamera Akışı ({p.name})</span>
                    <div style={{ position: "absolute", bottom: "10px", left: "10px", background: "rgba(0,0,0,0.7)", padding: "4px 8px", borderRadius: "4px", color: "#fff", fontSize: "0.8rem", display: "flex", alignItems: "center", gap: "6px" }}>
                      <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: isSuspicious ? theme.colors.danger : theme.colors.safe }}></span>
                      {p.name}
                    </div>
                  </>
                )}
              </div>
            );
          })}
        </div>

        {/* SAĞ: YÖNETİM PANELİ */}
        <div style={{ width: "360px", background: theme.colors.bgSurface, borderLeft: `1px solid ${theme.colors.bgSurfaceAlt}`, display: "flex", flexDirection: "column" }}>
          
          {status === "idle" ? (
            <div style={{ padding: "30px 20px", textAlign: "center", margin: "auto 0" }}>
              <div style={{ fontSize: "3rem", marginBottom: "15px" }}>🛡️</div>
              <h2 style={{ color: theme.colors.textPrimary, fontSize: "1.2rem", marginBottom: "10px" }}>Sistem Hazır</h2>
              <p style={{ color: theme.colors.textSecondary, fontSize: "0.9rem", marginBottom: "25px", lineHeight: "1.5" }}>
                Toplantıdaki 9 katılımcının gerçek yüz verisi doğrulaması eşzamanlı olarak yapılacaktır.
              </p>
              <button 
                onClick={startAnalysis}
                style={{ width: "100%", padding: "12px", background: theme.colors.accentPrimary, color: "#fff", border: "none", borderRadius: "6px", fontWeight: "bold", fontSize: "1rem", cursor: "pointer" }}>
                Analizi Başlat
              </button>
            </div>
          ) : (
            <>
              {/* ÜST KISIM */}
              <div style={{ padding: "20px", flex: 1, overflowY: "auto", display: "flex", flexDirection: "column", gap: "25px" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <h3 style={{ margin: 0, color: theme.colors.textPrimary, fontSize: "1rem" }}>Katılımcı Durumları</h3>
                  <span style={{ fontSize: "0.75rem", background: theme.colors.bgSurfaceAlt, padding: "4px 8px", borderRadius: "12px", color: theme.colors.textSecondary }}>Aktif: {activeParticipants.length}/9</span>
                </div>

                {suspiciousParticipants.length > 0 && (
                  <div>
                    <div style={{ fontSize: "0.8rem", color: theme.colors.danger, fontWeight: "bold", marginBottom: "10px", borderBottom: `1px solid ${theme.colors.danger}`, paddingBottom: "4px" }}>
                      RİSKLİ KATILIMCILAR ({suspiciousParticipants.length})
                    </div>
                    <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                      {suspiciousParticipants.map(p => (
                        <div key={p.id} style={{ background: "rgba(239, 68, 68, 0.1)", padding: "12px", borderRadius: "6px", border: `1px solid ${theme.colors.danger}`, display: "flex", flexDirection: "column", gap: "8px" }}>
                          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                            <span style={{ color: theme.colors.textPrimary, fontWeight: "bold", fontSize: "0.9rem" }}>{p.name}</span>
                            <span style={{ color: theme.colors.danger, fontWeight: "bold" }}>%{p.realityScore}</span>
                          </div>
                          <div style={{ width: "100%", height: "6px", background: "rgba(239, 68, 68, 0.2)", borderRadius: "3px", overflow: "hidden" }}>
                            <div style={{ width: `${p.realityScore}%`, height: "100%", background: theme.colors.danger, transition: "width 0.5s ease" }} />
                          </div>
                          {status === "analyzing" && (
                            <button 
                              onClick={() => kickParticipant(p.id)}
                              style={{ padding: "8px", background: theme.colors.danger, color: "#fff", border: "none", borderRadius: "4px", fontSize: "0.75rem", fontWeight: "bold", cursor: "pointer", marginTop: "4px" }}>
                              Toplantıdan Çıkart
                            </button>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {safeParticipants.length > 0 && (
                  <div>
                    <div style={{ fontSize: "0.8rem", color: theme.colors.safe, fontWeight: "bold", marginBottom: "10px", borderBottom: `1px solid ${theme.colors.bgSurfaceAlt}`, paddingBottom: "4px" }}>
                      GÜVENLİ KATILIMCILAR ({safeParticipants.length})
                    </div>
                    <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                      {safeParticipants.map(p => (
                        <div key={p.id} style={{ padding: "12px", borderRadius: "6px", background: theme.colors.bgPrimary, display: "flex", flexDirection: "column", gap: "8px" }}>
                          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                            <span style={{ color: theme.colors.textPrimary, fontSize: "0.9rem" }}>{p.name}</span>
                            {status === "analyzing" ? (
                              <span style={{ color: theme.colors.safe, fontWeight: "bold" }}>%{(p.realityScore || 95)}</span>
                            ) : (
                              <span style={{ color: theme.colors.textMuted, fontSize: "0.8rem" }}>Tamamlandı</span>
                            )}
                          </div>
                          <div style={{ width: "100%", height: "6px", background: theme.colors.bgSurfaceAlt, borderRadius: "3px", overflow: "hidden" }}>
                            <div style={{ width: `${p.realityScore}%`, height: "100%", background: theme.colors.safe, transition: "width 0.5s ease" }} />
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* ALT KISIM: AÇILIR KAPANIR MENÜ VE BUTONLAR */}
              <div style={{ padding: "20px", background: theme.colors.bgPrimary, borderTop: `1px solid ${theme.colors.bgSurfaceAlt}` }}>
                
                {kickedParticipants.length > 0 && (
                  <div style={{ marginBottom: "15px", background: theme.colors.bgSurface, borderRadius: "6px", border: `1px solid ${theme.colors.bgSurfaceAlt}`, overflow: "hidden" }}>
                    
                    <button 
                      onClick={() => setShowKicked(!showKicked)}
                      style={{ width: "100%", padding: "10px 15px", display: "flex", justifyContent: "space-between", alignItems: "center", background: "transparent", border: "none", cursor: "pointer", color: theme.colors.textSecondary }}>
                      <span style={{ fontSize: "0.75rem", fontWeight: "bold", color: theme.colors.textMuted }}>
                        TOPLANTIDAN ÇIKARILANLAR ({kickedParticipants.length})
                      </span>
                      <span style={{ fontSize: "0.8rem", transform: showKicked ? "rotate(180deg)" : "rotate(0deg)", transition: "transform 0.3s ease" }}>
                        ▼
                      </span>
                    </button>
                    
                    {showKicked && (
                      <div style={{ padding: "0 15px 15px 15px", display: "flex", flexDirection: "column", gap: "8px", maxHeight: "120px", overflowY: "auto", borderTop: `1px solid ${theme.colors.bgSurfaceAlt}`, marginTop: "5px", paddingTop: "10px" }}>
                        {kickedParticipants.map(p => (
                          <div key={p.id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", opacity: 0.7 }}>
                            <span style={{ color: theme.colors.textSecondary, fontSize: "0.85rem", textDecoration: "line-through" }}>{p.name}</span>
                            <span style={{ color: theme.colors.danger, fontSize: "0.7rem", fontWeight: "bold" }}>ATILDI</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {status === "analyzing" ? (
                  <button onClick={stopAnalysis} style={{ width: "100%", padding: "12px", background: theme.colors.bgSurfaceAlt, color: theme.colors.textSecondary, border: "none", borderRadius: "6px", cursor: "pointer", fontWeight: "bold" }}>
                    Taramayı Durdur
                  </button>
                ) : (
                  <button onClick={reset} style={{ width: "100%", padding: "12px", background: theme.colors.accentPrimary, color: "#fff", border: "none", borderRadius: "6px", cursor: "pointer", fontWeight: "bold" }}>
                    Sistemi Sıfırla (Yeni Oturum)
                  </button>
                )}
              </div>
            </>
          )}
        </div>

      </div>
    </div>
  );
}