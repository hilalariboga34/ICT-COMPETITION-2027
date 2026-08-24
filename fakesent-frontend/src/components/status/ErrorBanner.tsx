import { theme } from "../../constants/theme";
import type { AnalysisError } from "../../types/analysis";

export function ErrorBanner({ error, onClear }: { error: AnalysisError; onClear: () => void }) {
  if (!error) return null;

  // Prompt'ta istenen Türkçe çeviriler
  const errorMessages: Record<string, string> = {
    camera_unavailable: "Kamera erişimi sağlanamadı.",
    microphone_unavailable: "Mikrofon erişimi sağlanamadı.",
    connection_lost: "Bağlantı koptu, yeniden bağlanılıyor...",
    model_unavailable: "Analiz motoru başlatılamadı.",
    unknown: "Bilinmeyen bir teknik hata oluştu."
  };

  const message = typeof error === 'string' && errorMessages[error] ? errorMessages[error] : errorMessages.unknown;

  return (
    <div style={{
      background: theme.colors.danger,
      color: theme.colors.textPrimary,
      padding: "12px 20px",
      borderRadius: "8px",
      display: "flex",
      justifyContent: "space-between",
      alignItems: "center",
      marginBottom: "15px",
      fontFamily: theme.font.heading, // Marka tipografisi
      boxShadow: "0 4px 12px rgba(0,0,0,0.5)",
      border: `1px solid ${theme.colors.bgSurfaceAlt}`
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: "10px", fontSize: "0.9rem", letterSpacing: "0.5px" }}>
        <span style={{ fontSize: "1.2rem" }}>⚠️</span>
        <span>{message}</span>
      </div>
      <button 
        onClick={onClear} 
        style={{ 
          background: "transparent", 
          border: "none", 
          color: theme.colors.textPrimary, 
          cursor: "pointer", 
          fontWeight: "bold",
          fontSize: "1.1rem"
        }}
      >
        ✕
      </button>
    </div>
  );
}