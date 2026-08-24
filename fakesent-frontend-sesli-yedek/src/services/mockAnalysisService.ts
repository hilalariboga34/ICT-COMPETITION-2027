import type { IAnalysisService } from "./analysisService.interface";
import type { AnalysisSnapshot } from "../types/analysis";

// AÇIKÇA MOCK — gerçek AI çıktısı gibi sunulmamalı (master prompt madde 39).
export class MockAnalysisService implements IAnalysisService {
  private intervalId: ReturnType<typeof setInterval> | null = null;
  private history: AnalysisSnapshot[] = [];
  private tick = 0;

  async startAnalysis(): Promise<void> {
    this.tick = 0;
    this.history = [];
  }

  async stopAnalysis(): Promise<void> {
    if (this.intervalId) clearInterval(this.intervalId);
    this.intervalId = null;
  }

  async getAnalysisStatus(): Promise<AnalysisSnapshot> {
    return this.history.at(-1) ?? this.emptySnapshot();
  }

  async getAnalysisHistory(): Promise<AnalysisSnapshot[]> {
    return this.history;
  }

  subscribeToLiveAnalysis(onSnapshot: (snapshot: AnalysisSnapshot) => void): () => void {
    this.intervalId = setInterval(() => {
      this.tick += 0.5;
      const snapshot = this.generateMockSnapshot(this.tick);
      this.history.push(snapshot);
      onSnapshot(snapshot);
    }, 500); // backend'in 0.5sn güncelleme hedefiyle uyumlu (mock)

    return () => {
      if (this.intervalId) clearInterval(this.intervalId);
    };
  }

  private emptySnapshot(): AnalysisSnapshot {
    return {
      timestamp: 0,
      overallScore: 0,
      scores: { audioLip: 0, audioFace: 0, faceLip: 0 },
      status: "idle",
    };
  }

  // Demo amaçlı: skorları çoğunlukla yüksek tutup ara sıra düşürerek "şüpheli" senaryoyu simüle eder.
  private generateMockSnapshot(timestamp: number): AnalysisSnapshot {
    const isSuspiciousWindow = Math.floor(timestamp) % 20 >= 15; // her 20sn'de 5sn şüpheli
    const base = isSuspiciousWindow ? 45 : 88;
    const jitter = () => base + (Math.random() * 10 - 5);

    const audioLip = Math.max(0, Math.min(100, jitter()));
    const audioFace = Math.max(0, Math.min(100, jitter()));
    const faceLip = Math.max(0, Math.min(100, jitter()));
    const overallScore = Math.round((audioLip + audioFace + faceLip) / 3);

    return {
      timestamp,
      overallScore,
      scores: { audioLip, audioFace, faceLip },
      status: "analyzing", // nihai status kararını store veriyor (hysteresis mantığı için)
    };
  }
}