export interface OHLCVBar {
  time: string | number; // 'YYYY-MM-DD' for daily+, Unix seconds for intraday
  open: number;
  high: number;
  low: number;
  close: number;
  volume?: number;
}

export interface Quote {
  ticker: string;
  price: number;
  change_pct: number | null;
  open: number | null;
  high: number | null;
  low: number | null;
  close: number | null;
  volume: number | null;
  stale: boolean;
  timestamp?: string;
}

export interface ChartMarker {
  time: string;
  position: 'aboveBar' | 'belowBar';
  color: string;
  shape: 'arrowDown' | 'circle';
  text: string;
}

export type Timeframe = '1wk' | '1d' | '4h' | '1h';
export type TimeRange = '1D' | '1W' | '1M' | '1Y' | '5Y';

export const TIMEFRAME_LABELS: Record<Timeframe, string> = {
  '1wk': 'Weekly',
  '1d': 'Daily',
  '4h': '4H',
  '1h': '1H',
};
