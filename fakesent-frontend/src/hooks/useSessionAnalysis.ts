import { useEffect } from "react";
import {
  DEMO_SESSION_ID,
  USE_MOCK_PARTICIPANTS,
} from "../constants/env";
import {
  MOCK_PARTICIPANTS,
  MOCK_SESSION,
} from "../mocks/sessionSnapshot";
import { getSessionSnapshot } from "../services/snapshotApi";
import {
  createSessionWebSocketClient,
  type SessionWebSocketClient,
  type WebSocketConnectionState,
} from "../services/sessionWebSocket";
import {
  useAnalysisStore,
  type AnalysisConnectionState,
} from "../stores/useAnalysisStore";

function mapConnectionState(
  state: WebSocketConnectionState,
): AnalysisConnectionState {
  return state === "closed" ? "disconnected" : state;
}

export function useSessionAnalysis(): void {
  useEffect(() => {
    let isActive = true;
    let client: SessionWebSocketClient | null = null;
    let reconnectAbortController: AbortController | null = null;

    const initialAbortController = new AbortController();
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

    const loadInitialSnapshot = async () => {
      if (USE_MOCK_PARTICIPANTS) {
        store.setSnapshot(MOCK_SESSION, MOCK_PARTICIPANTS);
        return;
      }

      const snapshot = await getSessionSnapshot(
        DEMO_SESSION_ID,
        initialAbortController.signal,
      );

      if (!isActive) return;

      store.setSnapshot(
        snapshot.session,
        snapshot.participants,
      );
    };

    const refreshSnapshotAfterReconnect = async () => {
      if (USE_MOCK_PARTICIPANTS || !isActive) {
        return;
      }

      reconnectAbortController?.abort();
      reconnectAbortController = new AbortController();

      const controller = reconnectAbortController;

      try {
        const snapshot = await getSessionSnapshot(
          DEMO_SESSION_ID,
          controller.signal,
        );

        if (!isActive || controller.signal.aborted) {
          return;
        }

        useAnalysisStore
          .getState()
          .mergeSnapshot(
            snapshot.session,
            snapshot.participants,
          );
      } catch (error) {
        if (
          !isActive ||
          controller.signal.aborted ||
          (error instanceof DOMException &&
            error.name === "AbortError")
        ) {
          return;
        }

        useAnalysisStore
          .getState()
          .setError(
            error instanceof Error
              ? error.message
              : "Session snapshot could not be refreshed after reconnect.",
          );
      } finally {
        if (reconnectAbortController === controller) {
          reconnectAbortController = null;
        }
      }
    };

    const initialize = async () => {
      try {
        await loadInitialSnapshot();

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

            void refreshSnapshotAfterReconnect();
          },
        });
      } catch (error) {
        if (
          !isActive ||
          initialAbortController.signal.aborted ||
          (error instanceof DOMException &&
            error.name === "AbortError")
        ) {
          return;
        }

        store.setLoading(false);
        store.setConnectionState("disconnected");
        store.setError(
          error instanceof Error
            ? error.message
            : "Session snapshot could not be loaded.",
        );
      }
    };

    void initialize();

    return () => {
      isActive = false;
      initialAbortController.abort();
      reconnectAbortController?.abort();
      client?.close();
    };
  }, []);
}
