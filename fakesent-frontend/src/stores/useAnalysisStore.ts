import { create } from "zustand";
import type { Participant, AnalysisStatus, AnalysisError } from "../types/analysis";

const INITIAL_PARTICIPANTS: Participant[] = [
  { id: "1", name: "Ahmet Yılmaz", realityScore: 0, status: "idle" },
  { id: "2", name: "Mehmet Demir", realityScore: 0, status: "idle" },
  { id: "3", name: "Ayşe Kaya", realityScore: 0, status: "idle" },
  { id: "4", name: "Veli Çelik", realityScore: 0, status: "idle", isDemoTarget: true },
  { id: "5", name: "Fatma Yıldırım", realityScore: 0, status: "idle" },
  { id: "6", name: "Ali Yıldız", realityScore: 0, status: "idle" },
  { id: "7", name: "Elif Öztürk", realityScore: 0, status: "idle", isDemoTarget: true },
  { id: "8", name: "Can Arslan", realityScore: 0, status: "idle" },
  { id: "9", name: "Zeynep Koç", realityScore: 0, status: "idle" },
];

interface AnalysisStoreState {
  status: AnalysisStatus;
  participants: Participant[];
  simulationInterval: number | null;
  currentError: AnalysisError | null;

  startAnalysis: () => void;
  stopAnalysis: () => void;
  kickParticipant: (id: string) => void;
  reset: () => void;
  setError: (error: AnalysisError | null) => void;
  clearError: () => void;
}

export const useAnalysisStore = create<AnalysisStoreState>((set, get) => ({
  status: "idle",
  participants: INITIAL_PARTICIPANTS,
  simulationInterval: null,
  currentError: null,

  startAnalysis: () => {
    set({ status: "analyzing", currentError: null });
    
    set((state) => ({
      participants: state.participants.map(p => ({
        ...p,
        realityScore: p.isDemoTarget ? Math.floor(Math.random() * 15) + 40 : Math.floor(Math.random() * 13) + 85,
        status: p.isDemoTarget ? "suspicious" : "safe"
      }))
    }));

    const interval = setInterval(() => {
      set((state) => ({
        participants: state.participants.map(p => {
          // Atılan veya atılmakta olan kişilerin skorlarını dondur
          if (p.status === "kicked" || p.status === "kicking") return p;

          const fluctuation = Math.floor(Math.random() * 5) - 2; 
          let newScore = p.realityScore + fluctuation;

          if (p.isDemoTarget) {
            newScore = Math.max(30, Math.min(58, newScore));
          } else {
            newScore = Math.max(80, Math.min(99, newScore));
          }

          return { 
            ...p, 
            realityScore: newScore,
            status: newScore < 60 ? "suspicious" : "safe"
          };
        })
      }));
    }, 1000) as unknown as number;

    set({ simulationInterval: interval });
  },

  stopAnalysis: () => {
    const { simulationInterval } = get();
    if (simulationInterval) clearInterval(simulationInterval);
    set({ status: "completed", simulationInterval: null });
  },

  kickParticipant: (id: string) => {
    // 1. Önce durumu "çıkarılıyor" yap (Ekrandaki animasyon için)
    set((state) => ({
      participants: state.participants.map(p => 
        p.id === id ? { ...p, status: "kicking" } : p
      )
    }));

    // 2. 1.5 saniye sonra sistemden tamamen (kicked) çıkar
    setTimeout(() => {
      set((state) => ({
        participants: state.participants.map(p => 
          p.id === id ? { ...p, status: "kicked", realityScore: 0 } : p
        )
      }));
    }, 1500);
  },

  reset: () => {
    const { simulationInterval } = get();
    if (simulationInterval) clearInterval(simulationInterval);
    set({ status: "idle", participants: INITIAL_PARTICIPANTS, simulationInterval: null, currentError: null });
  },

  setError: (error) => set({ currentError: error }),
  clearError: () => set({ currentError: null }),
}));