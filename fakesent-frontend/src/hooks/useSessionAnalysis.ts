import { useEffect } from "react";
import {
  DEMO_SESSION_ID,
  USE_MOCK_PARTICIPANTS,
} from "../constants/env";
import {
  MOCK_PARTICIPANTS,
  MOCK_SESSION,
} from "../mocks/sessionSnapshot";
import { listParticipants } from "../services/participantApi";
import { getSession } from "../services/sessionApi";
import {
  createSessionWebSocketClient,
  type SessionWebSocketClient,
  type WebSocketConnectionState,
} from "../services/sessionWebSocket";
import {
  useAnalysisStore,
  type AnalysisConnectionState,
} from "../stores/useAnalysisStore";
import type { ParticipantViewModel } from "../types/viewModels";

function mapConnectionState(
  state: WebSocketConnectionState,
): AnalysisConnectionState {
  return state === "closed" ? "disconnected" : state;
}

function mapParticipantsToViewModels(
  participants: Awaited<ReturnType<typeof listParticipants>>,
): ParticipantViewModel[] {
  return participants.map((participant) => ({
    participant,
    latestAnalysis: null,
  }));
}

export function useSessionAnalysis(): void {
  useEffect(() => {
    let isActive = true;
    let client: SessionWebSocketClient | null = null;

    const abortController = new AbortController();
    const store = useAnalysisStore.getState();

    store.reset();
    store.setLoading(true);
    store.setError(null);

    if (!DEMO_SESSION_ID.trim()) {
      store.setLoading(false);
      store.setConnectionState("disconnected");
      store.setError(
        "VITE_DEMO_SESSION_ID is required before connecting to a session.",
      );
      return;
    }

    const loadSessionAndParticipants = async () => {
      if (USE_MOCK_PARTICIPANTS) {
        store.setSnapshot(MOCK_SESSION, MOCK_PARTICIPANTS);
        return;
      }

      const [session, participants] = await Promise.all([
        getSession(DEMO_SESSION_ID, abortController.signal),
        listParticipants(DEMO_SESSION_ID, abortController.signal),
      ]);

      if (!isActive) return;

      store.setSnapshot(
        session,
        mapParticipantsToViewModels(participants),
      );
    };

    const initialize = async () => {
      try {
        await loadSessionAndParticipants();

        if (!isActive) return;

        client = createSessionWebSocketClient({
          sessionId: DEMO_SESSION_ID,

          onAnalysisUpdated: (result) => {
            if (!isActive) return;

            useAnalysisStore
              .getState()
              .applyAnalysisResult(result);
          },

          onConnectionStateChange: (connectionState) => {
            if (!isActive) return;

            useAnalysisStore
              .getState()
              .setConnectionState(
                mapConnectionState(connectionState),
              );
          },

          onError: (error) => {
            if (!isActive) return;

            useAnalysisStore
              .getState()
              .setError(error.message);
          },

          onReconnected: () => {
            if (!isActive) return;

            // Reconnect sonrası session ve participant verilerinin yeniden
            // senkronizasyonu ayrı entegrasyon görevinde eklenecek.
          },
        });
      } catch (error) {
        if (!isActive || abortController.signal.aborted) return;

        store.setLoading(false);
        store.setConnectionState("disconnected");
        store.setError(
          error instanceof Error
            ? error.message
            : "Session and participant data could not be loaded.",
        );
      }
    };

    void initialize();

    return () => {
      isActive = false;
      abortController.abort();
      client?.close();
    };
  }, []);
}
