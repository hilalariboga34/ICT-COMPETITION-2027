import { create } from "zustand";
import type { AnalysisResult, Session } from "../types/backend";
import type { ParticipantViewModel } from "../types/viewModels";

export type AnalysisConnectionState =
  | "idle"
  | "connecting"
  | "connected"
  | "reconnecting"
  | "disconnected";

interface AnalysisStoreState {
  session: Session | null;
  participants: ParticipantViewModel[];
  removedParticipants: ParticipantViewModel[];
  isLoading: boolean;
  connectionState: AnalysisConnectionState;
  error: string | null;

  setSession: (session: Session | null) => void;
  setParticipants: (participants: ParticipantViewModel[]) => void;
  setSnapshot: (
    session: Session,
    participants: ParticipantViewModel[],
  ) => void;
  applyAnalysisResult: (result: AnalysisResult) => void;
  setParticipantDisconnected: (
    participantId: string,
    leftAt?: string | null,
  ) => void;
  removeParticipantForDemo: (participantId: string) => void;
  setLoading: (isLoading: boolean) => void;
  setConnectionState: (connectionState: AnalysisConnectionState) => void;
  setError: (error: string | null) => void;
  reset: () => void;
}

function isIncomingAnalysisNewer(
  incomingTimestamp: string,
  currentTimestamp: string,
): boolean {
  const incomingTime = Date.parse(incomingTimestamp);
  const currentTime = Date.parse(currentTimestamp);

  if (Number.isFinite(incomingTime) && Number.isFinite(currentTime)) {
    return incomingTime > currentTime;
  }

  return incomingTimestamp > currentTimestamp;
}

export const useAnalysisStore = create<AnalysisStoreState>((set) => ({
  session: null,
  participants: [],
  removedParticipants: [],
  isLoading: false,
  connectionState: "idle",
  error: null,

  setSession: (session) => set({ session }),

  setParticipants: (participants) => set({ participants }),

  setSnapshot: (session, participants) =>
    set({
      session,
      participants,
      isLoading: false,
      error: null,
    }),

  applyAnalysisResult: (result) =>
    set((state) => {
      const participantIndex = state.participants.findIndex(
        ({ participant }) =>
          participant.participantId === result.participantId,
      );

      if (participantIndex === -1) return state;

      const currentParticipant = state.participants[participantIndex];
      if (
        currentParticipant.latestAnalysis &&
        !isIncomingAnalysisNewer(
          result.timestamp,
          currentParticipant.latestAnalysis.timestamp,
        )
      ) {
        return state;
      }

      const participants = [...state.participants];
      participants[participantIndex] = {
        participant: {
          ...currentParticipant.participant,
          status: result.status,
        },
        latestAnalysis: result,
      };

      return { participants };
    }),

  setParticipantDisconnected: (participantId, leftAt) =>
    set((state) => ({
      participants: state.participants.map((viewModel) =>
        viewModel.participant.participantId === participantId
          ? {
              ...viewModel,
              participant: {
                ...viewModel.participant,
                status: "disconnected",
                leftAt:
                  leftAt === undefined
                    ? viewModel.participant.leftAt
                    : leftAt,
              },
            }
          : viewModel,
      ),
    })),

  removeParticipantForDemo: (participantId) =>
    set((state) => {
      const participantIndex = state.participants.findIndex(
        ({ participant }) => participant.participantId === participantId,
      );

      if (
        participantIndex === -1 ||
        state.removedParticipants.some(
          ({ participant }) => participant.participantId === participantId,
        )
      ) {
        return state;
      }

      const removedParticipant = state.participants[participantIndex];

      return {
        participants: state.participants.filter(
          ({ participant }) => participant.participantId !== participantId,
        ),
        removedParticipants: [
          ...state.removedParticipants,
          removedParticipant,
        ],
      };
    }),

  setLoading: (isLoading) => set({ isLoading }),

  setConnectionState: (connectionState) => set({ connectionState }),

  setError: (error) => set({ error }),

  reset: () =>
    set({
      session: null,
      participants: [],
      removedParticipants: [],
      isLoading: false,
      connectionState: "idle",
      error: null,
    }),
}));
