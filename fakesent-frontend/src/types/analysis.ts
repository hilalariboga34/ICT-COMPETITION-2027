// Katılımcı durumları ("kicking" geçiş durumu eklendi)
export type ParticipantStatus = "idle" | "safe" | "suspicious" | "kicking" | "kicked";

// Katılımcı veri yapısı (9 kişi için)
export interface Participant {
  id: string;
  name: string;
  realityScore: number;
  status: ParticipantStatus;
  isDemoTarget?: boolean;
}

// Analiz süreç durumları
export type AnalysisStatus =
  | "idle"
  | "starting"
  | "analyzing"
  | "completed";

// Hata senaryoları tipleri
export type AnalysisError = 
  | "connection_lost" 
  | "camera_unavailable" 
  | "model_unavailable" 
  | "unknown"
  | null;