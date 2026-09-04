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
  isLoading: boolean;
  connectionState: AnalysisConnectionState;
  error: string | null;

  setSession: (session: Session | null) => void;
  setParticipants: (participants: ParticipantViewModel[]) => void;
  setSnapshot: (
    session: Session,
    participants: ParticipantViewModel[],
  ) => void;
  mergeSnapshot: (
    session: Session,
    participants: ParticipantViewModel[],
  ) => void;
  applyAnalysisResult: (result: AnalysisResult) => void;
  setParticipantDisconnected: (
    participantId: string,
    leftAt?: string | null,
  ) => void;
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

const SESSION_STATUS_ORDER: Record<Session["status"], number> = {
  waiting: 0,
  active: 1,
  ended: 2,
};

function getNewerSessionState(
  currentSession: Session | null,
  snapshotSession: Session,
): Session {
  if (
    currentSession &&
    currentSession.sessionId === snapshotSession.sessionId &&
    SESSION_STATUS_ORDER[currentSession.status] >
      SESSION_STATUS_ORDER[snapshotSession.status]
  ) {
    return currentSession;
  }

  return snapshotSession;
}

export const useAnalysisStore = create<AnalysisStoreState>((set) => ({
  session: null,
  participants: [],
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

  mergeSnapshot: (session, participants) =>
    set((state) => {
      const currentByParticipantId = new Map(
        state.participants.map((viewModel) => [
          viewModel.participant.participantId,
          viewModel,
        ]),
      );

      const mergedParticipants = participants.map((snapshotViewModel) => {
        const participantId =
          snapshotViewModel.participant.participantId;

        const currentViewModel =
          currentByParticipantId.get(participantId);

        if (!currentViewModel) {
          return snapshotViewModel;
        }

        if (currentViewModel.participant.status === "disconnected") {
          return currentViewModel;
        }

        const currentAnalysis = currentViewModel.latestAnalysis;
        const snapshotAnalysis = snapshotViewModel.latestAnalysis;

        const shouldKeepCurrentAnalysis =
          currentAnalysis &&
          (!snapshotAnalysis ||
            isIncomingAnalysisNewer(
              currentAnalysis.timestamp,
              snapshotAnalysis.timestamp,
            ));

        if (snapshotViewModel.participant.status === "disconnected") {
          return {
            participant: snapshotViewModel.participant,
            latestAnalysis: shouldKeepCurrentAnalysis
              ? currentAnalysis
              : snapshotAnalysis,
          };
        }

        if (shouldKeepCurrentAnalysis) {
          return {
            participant: {
              ...snapshotViewModel.participant,
              status: currentViewModel.participant.status,
            },
            latestAnalysis: currentAnalysis,
          };
        }

        return snapshotViewModel;
      });

      return {
        session: getNewerSessionState(state.session, session),
        participants: mergedParticipants,
        isLoading: false,
        error: null,
      };
    }),

  applyAnalysisResult: (result) =>
    set((state) => {
      const participantIndex = state.participants.findIndex(
        ({ participant }) =>
          participant.participantId === result.participantId,
      );

      if (participantIndex === -1) return state;

      const currentParticipant = state.participants[participantIndex];

      if (currentParticipant.participant.status === "disconnected") {
        return state;
      }

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

  setLoading: (isLoading) => set({ isLoading }),

  setConnectionState: (connectionState) => set({ connectionState }),

  setError: (error) => set({ error }),

  reset: () =>
    set({
      session: null,
      participants: [],
      isLoading: false,
      connectionState: "idle",
      error: null,
    }),
}));
