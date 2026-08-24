// Analiz süreç durumları
export type AnalysisStatus =
  | "idle"
  | "ready"
  | "starting"
  | "analyzing"
  | "warning"
  | "critical"
  | "completed"
  | "error";

// Hata senaryoları tipleri (Yeni eklendi)
export type AnalysisError = 
  | "connection_lost" 
  | "camera_unavailable" 
  | "microphone_unavailable" 
  | "model_unavailable" 
  | "unknown"
  | null;

export type ConnectionState = "connected" | "connecting" | "disconnected" | "reconnecting";

// Modaliteler arası uyum skorları
export interface ModalityScores {
  audioLip: number;
  audioFace: number;
  faceLip: number;
}

// Anlık analiz verisi yapısı
export interface AnalysisSnapshot {
  timestamp: number;
  overallScore: number;
  scores: ModalityScores;
  status: AnalysisStatus;
}

// Katılımcı verisi (İleride çoklu katılımcı analizi için)
export interface Participant {
  id: string;
  name: string;
  role: "interviewer" | "candidate" | "participant";
  isActive: boolean;
}