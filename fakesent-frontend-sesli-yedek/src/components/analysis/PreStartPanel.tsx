// src/components/analysis/PreStartPanel.tsx
import { useAnalysis } from "../../hooks/useAnalysis";
import { APP_CONFIG } from "../../constants/appConfig";
import { theme } from "../../constants/theme";

export function PreStartPanel({ onDismiss }: { onDismiss: () => void }) {
  const { start } = useAnalysis();

  return (
    <div style={{ 
      padding: "1.5rem", 
      color: theme.colors.textPrimary, 
      background: theme.colors.bgSurface, 
      borderRadius: "8px", 
      border: `1px solid ${theme.colors.bgSurfaceAlt}`, 
      boxShadow: "0 4px 12px rgba(0,0,0,0.5)" 
    }}>
      <h3 style={{ margin: "0 0 10px 0", color: theme.colors.accentPrimary }}>
        {APP_CONFIG.name} — Gerçek Zamanlı Güvenlik
      </h3>
      <ul style={{ lineHeight: "1.6", paddingLeft: "20px", color: theme.colors.textSecondary }}>
        <li>Ses, yüz ve dudak senkronizasyonunu canlı olarak analiz eder</li>
        <li>Deepfake ve manipülasyon risklerini tespit eder</li>
        <li>Tüm işlemler cihazınızda yapılır, veri çıkmaz</li>
      </ul>
      <div style={{ display: "flex", gap: "10px", marginTop: "1.2rem" }}>
        <button 
          onClick={start} 
          style={{ 
            padding: "8px 16px", 
            cursor: "pointer", 
            background: theme.colors.accentPrimary, 
            color: theme.colors.textPrimary, 
            border: "none", 
            borderRadius: "4px", 
            fontWeight: "bold" 
          }}>
          Analizi Başlat
        </button>
        <button 
          onClick={onDismiss} 
          style={{ 
            padding: "8px 16px", 
            cursor: "pointer", 
            background: theme.colors.bgSurfaceAlt, 
            color: theme.colors.textSecondary, 
            border: "none", 
            borderRadius: "4px" 
          }}>
          Daha Sonra
        </button>
      </div>
    </div>
  );
}