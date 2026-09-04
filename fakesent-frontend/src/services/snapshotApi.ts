import { API_BASE_URL } from "../constants/env";
import type { SessionSnapshotResponse } from "../types/backend";

export async function getSessionSnapshot(
  sessionId: string,
  signal?: AbortSignal,
): Promise<SessionSnapshotResponse> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/sessions/${sessionId}/snapshot`,
    {
      method: "GET",
      signal,
    },
  );

  if (response.status === 404) {
    throw new Error("Oturum bulunamadı.");
  }

  if (!response.ok) {
    throw new Error(
      `Session snapshot failed with HTTP status ${response.status}`,
    );
  }

  return (await response.json()) as SessionSnapshotResponse;
}
