import type { AnalysisResult, Participant } from "../types/backend";

export interface ParticipantViewModel {
  participant: Participant;
  latestAnalysis: AnalysisResult | null;
}
