import { afterEach, describe, expect, it, vi } from "vitest";
import { getSessionSnapshot } from "./snapshotApi";
import type { SessionSnapshotResponse } from "../types/backend";

const SESSION_ID = "11111111-1111-4111-8111-111111111111";

const snapshot: SessionSnapshotResponse = {
  session: {
    sessionId: SESSION_ID,
    title: "PersonaLive Test Session",
    status: "active",
    createdAt: "2026-09-04T08:00:00.000Z",
    startedAt: "2026-09-04T08:05:00.000Z",
    endedAt: null,
  },
  participants: [
    {
      participant: {
        participantId: "22222222-2222-4222-8222-222222222222",
        sessionId: SESSION_ID,
        displayName: "Test Participant",
        status: "authentic",
        joinedAt: "2026-09-04T08:04:00.000Z",
        leftAt: null,
      },
      latestAnalysis: {
        sessionId: SESSION_ID,
        participantId: "22222222-2222-4222-8222-222222222222",
        realityScore: 0.92,
        confidence: 0.95,
        status: "authentic",
        timestamp: "2026-09-04T08:10:00.000Z",
        modelVersion: "analysis-v1",
      },
    },
    {
      participant: {
        participantId: "33333333-3333-4333-8333-333333333333",
        sessionId: SESSION_ID,
        displayName: "No Analysis Participant",
        status: "analyzing",
        joinedAt: "2026-09-04T08:04:30.000Z",
        leftAt: null,
      },
      latestAnalysis: null,
    },
  ],
};

afterEach(() => {
  vi.restoreAllMocks();
});

describe("session snapshot API", () => {
  it("fetches and returns the snapshot response unchanged", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify(snapshot), {
        status: 200,
        headers: {
          "Content-Type": "application/json",
        },
      }),
    );

    const abortController = new AbortController();

    const result = await getSessionSnapshot(
      SESSION_ID,
      abortController.signal,
    );

    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining(
        `/api/v1/sessions/${SESSION_ID}/snapshot`,
      ),
      expect.objectContaining({
        method: "GET",
        signal: abortController.signal,
      }),
    );

    expect(result).toEqual(snapshot);
    expect(result.participants[1].latestAnalysis).toBeNull();
  });

  it("shows a user-friendly error when the session does not exist", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(null, { status: 404 }),
    );

    await expect(getSessionSnapshot(SESSION_ID)).rejects.toThrow(
      "Oturum bulunamadı.",
    );
  });

  it("includes the HTTP status for other snapshot errors", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(null, { status: 500 }),
    );

    await expect(getSessionSnapshot(SESSION_ID)).rejects.toThrow(
      "Session snapshot failed with HTTP status 500",
    );
  });
});
