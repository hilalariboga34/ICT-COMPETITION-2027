import { WS_BASE_URL } from "../constants/env";
import type {
  AnalysisResult,
  AnalysisUpdatedEvent,
  ParticipantStatus,
} from "../types/backend";

export type WebSocketConnectionState =
  | "connecting"
  | "connected"
  | "reconnecting"
  | "closed";

export interface SessionWebSocketOptions {
  sessionId: string;
  onAnalysisUpdated: (result: AnalysisResult) => void;
  onConnectionStateChange?: (state: WebSocketConnectionState) => void;
  onError?: (error: Error) => void;
  onConnected?: () => void;
  onReconnected?: () => void;
}

export interface SessionWebSocketClient {
  close: () => void;
}

const INITIAL_RECONNECT_DELAY_MS = 1_000;
const MAX_RECONNECT_DELAY_MS = 30_000;

const PARTICIPANT_STATUSES: ReadonlySet<ParticipantStatus> = new Set([
  "analyzing",
  "authentic",
  "suspicious",
  "disconnected",
]);

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function isAnalysisResult(value: unknown): value is AnalysisResult {
  if (!isRecord(value)) return false;

  return (
    typeof value.sessionId === "string" &&
    typeof value.participantId === "string" &&
    typeof value.realityScore === "number" &&
    Number.isFinite(value.realityScore) &&
    value.realityScore >= 0 &&
    value.realityScore <= 1 &&
    typeof value.confidence === "number" &&
    Number.isFinite(value.confidence) &&
    typeof value.status === "string" &&
    PARTICIPANT_STATUSES.has(value.status as ParticipantStatus) &&
    typeof value.timestamp === "string" &&
    typeof value.modelVersion === "string"
  );
}

function parseAnalysisUpdatedEvent(data: unknown): AnalysisUpdatedEvent | null {
  if (typeof data !== "string") return null;

  try {
    const parsed: unknown = JSON.parse(data);

    if (
      !isRecord(parsed) ||
      parsed.type !== "analysis.updated" ||
      !isAnalysisResult(parsed.data)
    ) {
      return null;
    }

    return {
      type: "analysis.updated",
      data: parsed.data,
    };
  } catch {
    return null;
  }
}

class BrowserSessionWebSocketClient implements SessionWebSocketClient {
  private socket: WebSocket | null = null;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private reconnectAttempt = 0;
  private intentionallyClosed = false;

  constructor(private readonly options: SessionWebSocketOptions) {
    this.connect();
  }

  close(): void {
    this.intentionallyClosed = true;
    this.clearReconnectTimer();

    const socket = this.socket;
    this.socket = null;

    if (
      socket &&
      (socket.readyState === WebSocket.CONNECTING ||
        socket.readyState === WebSocket.OPEN)
    ) {
      socket.close();
    }

    this.options.onConnectionStateChange?.("closed");
  }

  private connect(): void {
    if (this.intentionallyClosed || this.reconnectTimer !== null) return;

    if (
      this.socket &&
      (this.socket.readyState === WebSocket.CONNECTING ||
        this.socket.readyState === WebSocket.OPEN)
    ) {
      return;
    }

    this.options.onConnectionStateChange?.(
      this.reconnectAttempt === 0 ? "connecting" : "reconnecting",
    );

    const url = `${WS_BASE_URL}/api/v1/ws/sessions/${encodeURIComponent(
      this.options.sessionId,
    )}`;
    let socket: WebSocket;

    try {
      socket = new WebSocket(url);
    } catch (error) {
      this.options.onError?.(
        error instanceof Error
          ? error
          : new Error("The session WebSocket could not be created."),
      );
      this.scheduleReconnect();
      return;
    }

    this.socket = socket;

    socket.onopen = () => {
      if (this.socket !== socket || this.intentionallyClosed) return;

      const wasReconnecting = this.reconnectAttempt > 0;
      this.reconnectAttempt = 0;
      this.options.onConnectionStateChange?.("connected");
      this.options.onConnected?.();

      if (wasReconnecting) {
        this.options.onReconnected?.();
      }
    };

    socket.onmessage = (event: MessageEvent<unknown>) => {
      if (this.socket !== socket || this.intentionallyClosed) return;

      const analysisEvent = parseAnalysisUpdatedEvent(event.data);
      if (analysisEvent) {
        this.options.onAnalysisUpdated(analysisEvent.data);
      }
    };

    socket.onerror = () => {
      if (this.socket !== socket || this.intentionallyClosed) return;

      this.options.onError?.(
        new Error("The session WebSocket encountered a connection error."),
      );
    };

    socket.onclose = () => {
      if (this.socket !== socket) return;

      this.socket = null;
      if (this.intentionallyClosed) return;

      this.scheduleReconnect();
    };
  }

  private scheduleReconnect(): void {
    if (this.intentionallyClosed || this.reconnectTimer !== null) return;

    const exponentialDelay =
      INITIAL_RECONNECT_DELAY_MS * 2 ** Math.min(this.reconnectAttempt, 10);
    const jitterMultiplier = 0.5 + Math.random();
    const delay = Math.min(
      MAX_RECONNECT_DELAY_MS,
      exponentialDelay * jitterMultiplier,
    );

    this.reconnectAttempt += 1;
    this.options.onConnectionStateChange?.("reconnecting");

    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      this.connect();
    }, delay);
  }

  private clearReconnectTimer(): void {
    if (this.reconnectTimer === null) return;

    clearTimeout(this.reconnectTimer);
    this.reconnectTimer = null;
  }
}

export function createSessionWebSocketClient(
  options: SessionWebSocketOptions,
): SessionWebSocketClient {
  return new BrowserSessionWebSocketClient(options);
}
