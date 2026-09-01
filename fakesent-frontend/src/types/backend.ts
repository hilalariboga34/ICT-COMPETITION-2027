export type ParticipantStatus =
  | "analyzing"
  | "authentic"
  | "suspicious"
  | "disconnected";

export type SessionStatus =
  | "waiting"
  | "active"
  | "ended";

export interface AnalysisInput {
  sessionId: string;
  participantId: string;
  fakeProbability: number;
  confidence: number;
  timestamp: string;
  modelVersion: string;
}

export interface AnalysisResult {
  sessionId: string;
  participantId: string;
  realityScore: number;
  confidence: number;
  status: ParticipantStatus;
  timestamp: string;
  modelVersion: string;
}

export interface AnalysisUpdatedEvent {
  type: "analysis.updated";
  data: AnalysisResult;
}

export interface Participant {
  participantId: string;
  sessionId: string;
  displayName: string;
  status: ParticipantStatus;
  joinedAt: string;
  leftAt: string | null;
}

export interface Session {
  sessionId: string;
  title: string;
  status: SessionStatus;
  createdAt: string;
  startedAt: string | null;
  endedAt: string | null;
}

export interface ParticipantCreate {
  displayName: string;
}

export interface SessionCreate {
  title: string;
}
