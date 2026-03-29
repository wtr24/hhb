/**
 * TA API client — typed fetch helpers for /api/ta/ routes.
 * All functions return typed response objects.
 */

export interface IndicatorData {
  ticker: string;
  indicator: string;
  timeframe: string;
  data: Record<string, unknown>;
}

export interface PivotData {
  method: string;
  pp: number;
  r1: number | null;
  r2: number | null;
  r3: number | null;
  s1: number | null;
  s2: number | null;
  s3: number | null;
  r4?: number | null;
  s4?: number | null;
}

export interface ChartPatternResult {
  pattern: string;
  start_bar: number;
  end_bar: number;
  breakout_bar: number;
  confidence: number;
  label: string;
  experimental: true;
}

export interface CandlestickPatternResult {
  name: string;
  signal: 100 | -100;
  win_rate: number | null;
  p_value: number | null;
  n_occurrences: number;
  is_bullish: boolean;
}

export type IndicatorParams = {
  indicator: string;
  timeframe?: string;
  period?: number;
  period2?: number;
  period3?: number;
};

export async function fetchIndicator(
  ticker: string,
  params: IndicatorParams
): Promise<IndicatorData> {
  const qs = new URLSearchParams({
    indicator: params.indicator,
    timeframe: params.timeframe ?? "1d",
    ...(params.period !== undefined && { period: String(params.period) }),
    ...(params.period2 !== undefined && { period2: String(params.period2) }),
    ...(params.period3 !== undefined && { period3: String(params.period3) }),
  });
  const res = await fetch(`/api/ta/indicators/${encodeURIComponent(ticker)}?${qs}`);
  if (!res.ok) throw new Error(`TA indicator fetch failed: ${res.status}`);
  return res.json();
}

export async function fetchPivots(
  ticker: string,
  timeframe = "1d"
): Promise<{ ticker: string; pivots: PivotData[] }> {
  const res = await fetch(
    `/api/ta/pivots/${encodeURIComponent(ticker)}?timeframe=${timeframe}`
  );
  if (!res.ok) throw new Error(`Pivot fetch failed: ${res.status}`);
  return res.json();
}

export async function fetchChartPatterns(
  ticker: string,
  timeframe = "1d"
): Promise<{ ticker: string; timeframe: string; patterns: ChartPatternResult[] }> {
  const res = await fetch(
    `/api/ta/chart-patterns/${encodeURIComponent(ticker)}?timeframe=${timeframe}`
  );
  if (!res.ok) throw new Error(`Chart pattern fetch failed: ${res.status}`);
  return res.json();
}

export async function fetchCandlestickPatterns(
  ticker: string,
  timeframe = "1d"
): Promise<{ ticker: string; timeframe: string; patterns: CandlestickPatternResult[] }> {
  const res = await fetch(
    `/api/ta/patterns/${encodeURIComponent(ticker)}?timeframe=${timeframe}`
  );
  if (!res.ok) throw new Error(`Candlestick pattern fetch failed: ${res.status}`);
  return res.json();
}

export async function fetchFibonacciLevels(
  swingHigh: number,
  swingLow: number
): Promise<{ levels: Array<{ ratio: number; price: number; label: string; is_key_level: boolean }> }> {
  const res = await fetch("/api/ta/fibonacci", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ swing_high: swingHigh, swing_low: swingLow }),
  });
  if (!res.ok) throw new Error(`Fibonacci fetch failed: ${res.status}`);
  return res.json();
}

export async function validateElliottWave(
  wavePoints: Array<{ bar_idx: number; price: number }>
): Promise<{ validations: Array<{ valid: boolean; rule: string; message: string }> }> {
  const res = await fetch("/api/ta/elliott-wave/validate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ wave_points: wavePoints }),
  });
  if (!res.ok) throw new Error(`EW validation failed: ${res.status}`);
  return res.json();
}
