import type { AnalysisSnapshot } from "../types/analysis";

// Componentler bu interface'i kullanır — WebSocket/REST/IPC detayına asla dokunmaz.
export interface IAnalysisService {
  startAnalysis(): Promise<void>;
  stopAnalysis(): Promise<void>;
  getAnalysisStatus(): Promise<AnalysisSnapshot>;
  getAnalysisHistory(): Promise<AnalysisSnapshot[]>;
  subscribeToLiveAnalysis(onSnapshot: (snapshot: AnalysisSnapshot) => void): () => void; // unsubscribe döner
}