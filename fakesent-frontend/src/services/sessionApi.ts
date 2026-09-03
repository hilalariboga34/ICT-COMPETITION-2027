import { API_BASE_URL } from "../constants/env";
import type { Session } from "../types/backend";

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

  if (!response.ok) {
    throw new Error(
      `Session fetch failed with HTTP status ${response.status}`,
    );
  }

  return (await response.json()) as Session;
}