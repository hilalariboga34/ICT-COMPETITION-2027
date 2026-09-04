import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  createSessionWebSocketClient,
  type SessionWebSocketClient,
} from "./sessionWebSocket";

class MockWebSocket {
  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;

  static instances: MockWebSocket[] = [];

  readyState = MockWebSocket.CONNECTING;
  onopen: (() => void) | null = null;
  onmessage: ((event: MessageEvent<unknown>) => void) | null = null;
  onerror: (() => void) | null = null;
  onclose: (() => void) | null = null;

  constructor(public readonly url: string) {
    MockWebSocket.instances.push(this);
  }

  open(): void {
    this.readyState = MockWebSocket.OPEN;
    this.onopen?.();
  }

  close(): void {
    this.readyState = MockWebSocket.CLOSED;
    this.onclose?.();
  }

  simulateRemoteClose(): void {
    this.readyState = MockWebSocket.CLOSED;
    this.onclose?.();
  }
}

describe("session WebSocket connection callbacks", () => {
  let originalWebSocket: typeof WebSocket;
  let client: SessionWebSocketClient | null = null;

  beforeEach(() => {
    vi.useFakeTimers();

    originalWebSocket = globalThis.WebSocket;

    MockWebSocket.instances = [];

    vi.stubGlobal(
      "WebSocket",
      MockWebSocket as unknown as typeof WebSocket,
    );

    vi.spyOn(Math, "random").mockReturnValue(0.5);
  });

  afterEach(() => {
    client?.close();
    client = null;

    vi.restoreAllMocks();
    vi.useRealTimers();

    globalThis.WebSocket = originalWebSocket;
  });

  it("calls onConnected on the initial successful connection", () => {
    const onConnected = vi.fn();

    client = createSessionWebSocketClient({
      sessionId: "11111111-1111-4111-8111-111111111111",
      onAnalysisUpdated: vi.fn(),
      onConnected,
    });

    expect(MockWebSocket.instances).toHaveLength(1);

    MockWebSocket.instances[0].open();

    expect(onConnected).toHaveBeenCalledTimes(1);
  });

  it("calls onConnected again after reconnecting", () => {
    const onConnected = vi.fn();

    client = createSessionWebSocketClient({
      sessionId: "11111111-1111-4111-8111-111111111111",
      onAnalysisUpdated: vi.fn(),
      onConnected,
    });

    const firstSocket = MockWebSocket.instances[0];

    firstSocket.open();

    expect(onConnected).toHaveBeenCalledTimes(1);

    firstSocket.simulateRemoteClose();

    vi.runOnlyPendingTimers();

    expect(MockWebSocket.instances).toHaveLength(2);

    const secondSocket = MockWebSocket.instances[1];

    secondSocket.open();

    expect(onConnected).toHaveBeenCalledTimes(2);
  });

  it("does not call onConnected after intentional close", () => {
    const onConnected = vi.fn();

    client = createSessionWebSocketClient({
      sessionId: "11111111-1111-4111-8111-111111111111",
      onAnalysisUpdated: vi.fn(),
      onConnected,
    });

    const socket = MockWebSocket.instances[0];

    client.close();

    socket.open();

    expect(onConnected).not.toHaveBeenCalled();

    vi.runOnlyPendingTimers();

    expect(MockWebSocket.instances).toHaveLength(1);
  });
});
