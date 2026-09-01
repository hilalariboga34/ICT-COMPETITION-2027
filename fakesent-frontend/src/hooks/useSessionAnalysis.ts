import { useEffect } from "react";
import {
  DEMO_SESSION_ID,
  USE_MOCK_PARTICIPANTS,
} from "../constants/env";
import {
  MOCK_PARTICIPANTS,
  MOCK_SESSION,
} from "../mocks/sessionSnapshot";
import {
  createSessionWebSocketClient,
  type WebSocketConnectionState,
} from "../services/sessionWebSocket";
import {
  useAnalysisStore,
  type AnalysisConnectionState,
} from "../stores/useAnalysisStore";

const SNAPSHOT_UNAVAILABLE_MESSAGE =
  "Participant and session snapshots are unavailable until the backend endpoints are implemented.";

function mapConnectionState(
  state: WebSocketConnectionState,
): AnalysisConnectionState {
  return state === "closed" ? "disconnected" : state;
}

export function useSessionAnalysis(): void {
  useEffect(() => {
    let isActive = true;
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

    if (USE_MOCK_PARTICIPANTS) {
      store.setSnapshot(MOCK_SESSION, MOCK_PARTICIPANTS);
    } else {
      store.setSession(null);
      store.setParticipants([]);
      store.setLoading(false);
      store.setError(SNAPSHOT_UNAVAILABLE_MESSAGE);
    }

    const client = createSessionWebSocketClient({
      sessionId: DEMO_SESSION_ID,
      onAnalysisUpdated: (result) => {
        if (!isActive) return;
        useAnalysisStore.getState().applyAnalysisResult(result);
      },
      onConnectionStateChange: (connectionState) => {
        if (!isActive) return;

        const currentStore = useAnalysisStore.getState();
        currentStore.setConnectionState(mapConnectionState(connectionState));

        if (connectionState === "connecting") {
          currentStore.setError(
            USE_MOCK_PARTICIPANTS ? null : SNAPSHOT_UNAVAILABLE_MESSAGE,
          );
        }

        if (connectionState === "connected") {
          currentStore.setError(
            USE_MOCK_PARTICIPANTS ? null : SNAPSHOT_UNAVAILABLE_MESSAGE,
          );
        }
      },
      onError: (error) => {
        if (!isActive) return;
        useAnalysisStore.getState().setError(error.message);
      },
      onReconnected: () => {
        if (!isActive) return;

        // Future integration boundary: refresh the authoritative session and
        // participant snapshot here once those backend endpoints are available.
        // Existing state is intentionally preserved so newer live analysis is
        // not overwritten by the deterministic initial mock snapshot.
      },
    });

    return () => {
      isActive = false;
      client.close();
    };
  }, []);
}
