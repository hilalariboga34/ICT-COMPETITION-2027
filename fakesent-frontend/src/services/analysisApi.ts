import { API_BASE_URL } from "../constants/env";
import type { AnalysisInput, AnalysisResult } from "../types/backend";

export async function evaluateAnalysis(
  input: AnalysisInput,
  signal?: AbortSignal,
): Promise<AnalysisResult> {
  const response = await fetch(`${API_BASE_URL}/api/v1/analysis/evaluate`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(input),
    signal,
  });

  if (!response.ok) {
    throw new Error(
      `Analysis evaluation failed with HTTP status ${response.status}`,
    );
  }

  return (await response.json()) as AnalysisResult;
}
