import { useEffect, useRef } from "react";
import { MockAnalysisService } from "../services/mockAnalysisService";
import type { IAnalysisService } from "../services/analysisService.interface";
import { useAnalysisStore } from "../stores/useAnalysisStore";

const service: IAnalysisService = new MockAnalysisService();

export function useAnalysis() {
  const unsubscribeRef = useRef<(() => void) | null>(null);
  const { status, currentSnapshot, timeline, ingestSnapshot, reset, connection, setConnection } =
    useAnalysisStore();

  useEffect(() => {
    return () => {
      unsubscribeRef.current?.();
    };
  }, []);

  async function start() {
    // UX için 'starting' ara adımı tetikleniyor
    useAnalysisStore.setState({ status: "starting" });
    setConnection("connecting");

    // Model yüklenme / hazırlanma simülasyonu (800ms)
    await new Promise((resolve) => setTimeout(resolve, 800));

    await service.startAnalysis();
    setConnection("connected");
    
    // Canlı akış başlatılıyor
    unsubscribeRef.current = service.subscribeToLiveAnalysis(ingestSnapshot);
  }

  async function stop() {
    unsubscribeRef.current?.();
    await service.stopAnalysis();
    setConnection("disconnected");
    reset();
  }

  return { status, currentSnapshot, timeline, connection, start, stop };
}