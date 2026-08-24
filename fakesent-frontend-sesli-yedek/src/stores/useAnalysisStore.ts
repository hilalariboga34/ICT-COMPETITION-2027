import { create } from "zustand";
import type { AnalysisSnapshot, AnalysisStatus, ConnectionState, AnalysisError } from "../types/analysis";

const WARNING_THRESHOLD = 60;
const CRITICAL_THRESHOLD = 40;
const CONSECUTIVE_TICKS_REQUIRED = 3; // ani zıplamayı engellemek için

interface AnalysisStoreState {
  status: AnalysisStatus;
  connection: ConnectionState;
  currentSnapshot: AnalysisSnapshot | null;
  timeline: AnalysisSnapshot[];
  selectedParticipantId: string | null;
  dashboardOpen: boolean;
  currentError: AnalysisError | null; // YENİ EKLENDİ

  // internal — hysteresis sayaçları
  _lowScoreStreak: number;
  _highScoreStreak: number;

  ingestSnapshot: (snapshot: AnalysisSnapshot) => void;
  setConnection: (state: ConnectionState) => void;
  reset: () => void;
  toggleDashboard: (open: boolean) => void;
  setError: (error: AnalysisError | null) => void; // YENİ EKLENDİ
  clearError: () => void; // YENİ EKLENDİ
}

export const useAnalysisStore = create<AnalysisStoreState>((set, get) => ({
  status: "idle",
  connection: "disconnected",
  currentSnapshot: null,
  timeline: [],
  selectedParticipantId: null,
  dashboardOpen: false,
  currentError: null, // YENİ EKLENDİ
  _lowScoreStreak: 0,
  _highScoreStreak: 0,

  ingestSnapshot: (snapshot) => {
    const { _lowScoreStreak, _highScoreStreak, status } = get();

    let lowStreak = _lowScoreStreak;
    let highStreak = _highScoreStreak;
    let nextStatus: AnalysisStatus = status;

    if (snapshot.overallScore < CRITICAL_THRESHOLD) {
      lowStreak += 1;
      highStreak = 0;
    } else if (snapshot.overallScore < WARNING_THRESHOLD) {
      lowStreak += 1;
      highStreak = 0;
    } else {
      highStreak += 1;
      lowStreak = 0;
    }

    // Sadece art arda N ölçümde eşik aşıldıysa state değiştir — tek kötü frame'de zıplamaz.
    if (lowStreak >= CONSECUTIVE_TICKS_REQUIRED) {
      nextStatus = snapshot.overallScore < CRITICAL_THRESHOLD ? "critical" : "warning";
    } else if (highStreak >= CONSECUTIVE_TICKS_REQUIRED) {
      nextStatus = "analyzing";
    }

    set((s) => ({
      currentSnapshot: snapshot,
      timeline: [...s.timeline, snapshot].slice(-200), // bellek şişmesin diye son 200 kayıt
      status: nextStatus,
      _lowScoreStreak: lowStreak,
      _highScoreStreak: highStreak,
    }));
  },

  setConnection: (connection) => set({ connection }),

  reset: () =>
    set({
      status: "idle",
      currentSnapshot: null,
      timeline: [],
      currentError: null, // YENİ EKLENDİ
      _lowScoreStreak: 0,
      _highScoreStreak: 0,
    }),

  toggleDashboard: (open) => set({ dashboardOpen: open }),
  
  // YENİ EKLENEN FONKSİYONLAR
  setError: (error) => set({ currentError: error }),
  clearError: () => set({ currentError: null }),
}));