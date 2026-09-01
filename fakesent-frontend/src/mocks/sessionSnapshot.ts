import { DEMO_SESSION_ID } from "../constants/env";
import type { Session } from "../types/backend";
import type { ParticipantViewModel } from "../types/viewModels";

export const MOCK_SESSION: Session = {
  sessionId: DEMO_SESSION_ID,
  title: "PersonaLive Demo Session",
  status: "active",
  createdAt: "2026-01-15T09:00:00.000Z",
  startedAt: "2026-01-15T09:05:00.000Z",
  endedAt: null,
};

export const MOCK_PARTICIPANTS: ParticipantViewModel[] = [
  {
    participant: {
      participantId: "8ffb09d5-f383-5529-822b-b2fdb92bd2bd",
      sessionId: DEMO_SESSION_ID,
      displayName: "Ahmet Yılmaz",
      status: "authentic",
      joinedAt: "2026-01-15T09:04:30.000Z",
      leftAt: null,
    },
    latestAnalysis: {
      sessionId: DEMO_SESSION_ID,
      participantId: "8ffb09d5-f383-5529-822b-b2fdb92bd2bd",
      realityScore: 0.94,
      confidence: 0.97,
      status: "authentic",
      timestamp: "2026-01-15T09:10:00.000Z",
      modelVersion: "demo-model-1.0.0",
    },
  },
  {
    participant: {
      participantId: "c445781a-db1d-52b5-830b-d0fc0b27766b",
      sessionId: DEMO_SESSION_ID,
      displayName: "Ayşe Kaya",
      status: "suspicious",
      joinedAt: "2026-01-15T09:04:45.000Z",
      leftAt: null,
    },
    latestAnalysis: {
      sessionId: DEMO_SESSION_ID,
      participantId: "c445781a-db1d-52b5-830b-d0fc0b27766b",
      realityScore: 0.38,
      confidence: 0.91,
      status: "suspicious",
      timestamp: "2026-01-15T09:10:05.000Z",
      modelVersion: "demo-model-1.0.0",
    },
  },
  {
    participant: {
      participantId: "adc64f52-dd2b-5ac4-ba68-96acdf360284",
      sessionId: DEMO_SESSION_ID,
      displayName: "Mehmet Demir",
      status: "analyzing",
      joinedAt: "2026-01-15T09:04:50.000Z",
      leftAt: null,
    },
    latestAnalysis: null,
  },
  {
    participant: {
      participantId: "participant-004",
      sessionId: DEMO_SESSION_ID,
      displayName: "Elif Öztürk",
      status: "disconnected",
      joinedAt: "2026-01-15T09:04:55.000Z",
      leftAt: "2026-01-15T09:12:00.000Z",
    },
    latestAnalysis: {
      sessionId: DEMO_SESSION_ID,
      participantId: "participant-004",
      realityScore: 0.82,
      confidence: 0.89,
      status: "authentic",
      timestamp: "2026-01-15T09:11:45.000Z",
      modelVersion: "demo-model-1.0.0",
    },
  },
];
