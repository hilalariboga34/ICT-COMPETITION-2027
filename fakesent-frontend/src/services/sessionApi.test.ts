import { afterEach, describe, expect, it, vi } from "vitest";
import { endSession, startSession } from "./sessionApi";
import type { Session } from "../types/backend";

const SESSION_ID = "11111111-1111-4111-8111-111111111111";

const waitingSession: Session = {
  sessionId: SESSION_ID,
  title: "PersonaLive Test Session",
  status: "waiting",
  createdAt: "2026-09-03T10:00:00.000Z",
  startedAt: null,
  endedAt: null,
};

const activeSession: Session = {
  ...waitingSession,
  status: "active",
  startedAt: "2026-09-03T10:05:00.000Z",
};

const endedSession: Session = {
  ...activeSession,
  status: "ended",
  endedAt: "2026-09-03T11:00:00.000Z",
};

afterEach(() => {
  vi.restoreAllMocks();
});

describe("session lifecycle API", () => {
  it("starts a session with POST and returns the backend response unchanged", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify(activeSession), {
        status: 200,
        headers: {
          "Content-Type": "application/json",
        },
      }),
    );

    const result = await startSession(SESSION_ID);

    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining(`/api/v1/sessions/${SESSION_ID}/start`),
      expect.objectContaining({
        method: "POST",
      }),
    );

    expect(result).toEqual(activeSession);
  });

  it("ends a session with POST and returns the backend response unchanged", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify(endedSession), {
        status: 200,
        headers: {
          "Content-Type": "application/json",
        },
      }),
    );

    const result = await endSession(SESSION_ID);

    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining(`/api/v1/sessions/${SESSION_ID}/end`),
      expect.objectContaining({
        method: "POST",
      }),
    );

    expect(result).toEqual(endedSession);
  });

  it("shows a user-friendly error when the session does not exist", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(null, { status: 404 }),
    );

    await expect(startSession(SESSION_ID)).rejects.toThrow(
      "Oturum bulunamadı.",
    );
  });

  it("shows a user-friendly error when start returns 409", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(null, { status: 409 }),
    );

    await expect(startSession(SESSION_ID)).rejects.toThrow(
      "Oturum mevcut durumundan başlatılamıyor.",
    );
  });

  it("shows a user-friendly error when end returns 409", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(null, { status: 409 }),
    );

    await expect(endSession(SESSION_ID)).rejects.toThrow(
      "Oturum mevcut durumundan bitirilemiyor.",
    );
  });
});