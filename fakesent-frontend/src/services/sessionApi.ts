import { API_BASE_URL } from "../constants/env";
import type { Session } from "../types/backend";

async function parseSessionResponse(
  response: Response,
  action: "fetch" | "start" | "end",
): Promise<Session> {
  if (response.ok) {
    return (await response.json()) as Session;
  }

  if (response.status === 404) {
    throw new Error("Oturum bulunamadı.");
  }

  if (response.status === 409) {
    if (action === "start") {
      throw new Error("Oturum mevcut durumundan başlatılamıyor.");
    }

    if (action === "end") {
      throw new Error("Oturum mevcut durumundan bitirilemiyor.");
    }
  }

  throw new Error(
    `Session ${action} failed with HTTP status ${response.status}`,
  );
}

export async function getSession(
  sessionId: string,
  signal?: AbortSignal,
): Promise<Session> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/sessions/${sessionId}`,
    {
      method: "GET",
      signal,
    },
  );

  return parseSessionResponse(response, "fetch");
}

export async function startSession(
  sessionId: string,
  signal?: AbortSignal,
): Promise<Session> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/sessions/${sessionId}/start`,
    {
      method: "POST",
      signal,
    },
  );

  return parseSessionResponse(response, "start");
}

export async function endSession(
  sessionId: string,
  signal?: AbortSignal,
): Promise<Session> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/sessions/${sessionId}/end`,
    {
      method: "POST",
      signal,
    },
  );

  return parseSessionResponse(response, "end");
}
