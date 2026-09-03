import { API_BASE_URL } from "../constants/env";
import type {
  Participant,
  ParticipantCreate,
} from "../types/backend";

export async function createParticipant(
  sessionId: string,
  input: ParticipantCreate,
  signal?: AbortSignal,
): Promise<Participant> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/sessions/${sessionId}/participants`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(input),
      signal,
    },
  );

  if (!response.ok) {
    throw new Error(
      `Participant creation failed with HTTP status ${response.status}`,
    );
  }

  return (await response.json()) as Participant;
}

export async function listParticipants(
  sessionId: string,
  signal?: AbortSignal,
): Promise<Participant[]> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/sessions/${sessionId}/participants`,
    {
      method: "GET",
      signal,
    },
  );

  if (!response.ok) {
    throw new Error(
      `Participant list failed with HTTP status ${response.status}`,
    );
  }

  return (await response.json()) as Participant[];
}

export async function disconnectParticipant(
  sessionId: string,
  participantId: string,
  signal?: AbortSignal,
): Promise<Participant> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/sessions/${sessionId}/participants/${participantId}/disconnect`,
    {
      method: "POST",
      signal,
    },
  );

  if (!response.ok) {
    throw new Error(
      `Participant disconnect failed with HTTP status ${response.status}`,
    );
  }

  return (await response.json()) as Participant;
}