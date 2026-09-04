import { beforeEach, describe, expect, it } from "vitest";
import { useAnalysisStore } from "./useAnalysisStore";
import type { ParticipantViewModel } from "../types/viewModels";
import type { Session } from "../types/backend";

const SESSION_ID = "11111111-1111-4111-8111-111111111111";
const PARTICIPANT_ID = "22222222-2222-4222-8222-222222222222";

const session: Session = {
  sessionId: SESSION_ID,
  title: "PersonaLive Test Session",
  status: "active",
  createdAt: "2026-09-04T08:00:00.000Z",
  startedAt: "2026-09-04T08:05:00.000Z",
  endedAt: null,
};

const initialParticipant: ParticipantViewModel = {
  participant: {
    participantId: PARTICIPANT_ID,
    sessionId: SESSION_ID,
    displayName: "Test Participant",
    status: "authentic",
    joinedAt: "2026-09-04T08:04:00.000Z",
    leftAt: null,
  },
  latestAnalysis: {
    sessionId: SESSION_ID,
    participantId: PARTICIPANT_ID,
    realityScore: 0.8,
    confidence: 0.9,
    status: "authentic",
    timestamp: "2026-09-04T08:10:00.000Z",
    modelVersion: "analysis-v1",
  },
};

beforeEach(() => {
  useAnalysisStore.getState().reset();
});

describe("analysis store snapshot reconciliation", () => {
  it("keeps a newer WebSocket analysis when an older reconnect snapshot arrives", () => {
    useAnalysisStore
      .getState()
      .setSnapshot(session, [initialParticipant]);

    useAnalysisStore.getState().applyAnalysisResult({
      sessionId: SESSION_ID,
      participantId: PARTICIPANT_ID,
      realityScore: 0.95,
      confidence: 0.98,
      status: "authentic",
      timestamp: "2026-09-04T08:12:00.000Z",
      modelVersion: "analysis-v1",
    });

    const staleSnapshotParticipant: ParticipantViewModel = {
      participant: {
        ...initialParticipant.participant,
        status: "suspicious",
      },
      latestAnalysis: {
        sessionId: SESSION_ID,
        participantId: PARTICIPANT_ID,
        realityScore: 0.4,
        confidence: 0.85,
        status: "suspicious",
        timestamp: "2026-09-04T08:11:00.000Z",
        modelVersion: "analysis-v1",
      },
    };

    useAnalysisStore
      .getState()
      .mergeSnapshot(session, [staleSnapshotParticipant]);

    const result = useAnalysisStore.getState().participants[0];

    expect(result.latestAnalysis?.timestamp).toBe(
      "2026-09-04T08:12:00.000Z",
    );
    expect(result.latestAnalysis?.realityScore).toBe(0.95);
    expect(result.participant.status).toBe("authentic");
  });

  it("keeps an already disconnected participant disconnected", () => {
    useAnalysisStore
      .getState()
      .setSnapshot(session, [initialParticipant]);

    useAnalysisStore
      .getState()
      .setParticipantDisconnected(
        PARTICIPANT_ID,
        "2026-09-04T08:15:00.000Z",
      );

    useAnalysisStore
      .getState()
      .mergeSnapshot(session, [initialParticipant]);

    const result = useAnalysisStore.getState().participants[0];

    expect(result.participant.status).toBe("disconnected");
    expect(result.participant.leftAt).toBe(
      "2026-09-04T08:15:00.000Z",
    );
  });

  it("preserves a disconnected participant returned by the snapshot", () => {
    useAnalysisStore
      .getState()
      .setSnapshot(session, [initialParticipant]);

    const disconnectedSnapshotParticipant: ParticipantViewModel = {
      participant: {
        ...initialParticipant.participant,
        status: "disconnected",
        leftAt: "2026-09-04T08:20:00.000Z",
      },
      latestAnalysis: initialParticipant.latestAnalysis,
    };

    useAnalysisStore
      .getState()
      .mergeSnapshot(session, [disconnectedSnapshotParticipant]);

    const result = useAnalysisStore.getState().participants[0];

    expect(result.participant.status).toBe("disconnected");
    expect(result.participant.leftAt).toBe(
      "2026-09-04T08:20:00.000Z",
    );
  });

  it("does not move an ended session back to active", () => {
    const endedSession: Session = {
      ...session,
      status: "ended",
      endedAt: "2026-09-04T08:30:00.000Z",
    };

    useAnalysisStore
      .getState()
      .setSnapshot(endedSession, [initialParticipant]);

    useAnalysisStore
      .getState()
      .mergeSnapshot(session, [initialParticipant]);

    const result = useAnalysisStore.getState().session;

    expect(result?.status).toBe("ended");
    expect(result?.endedAt).toBe("2026-09-04T08:30:00.000Z");
  });
});
