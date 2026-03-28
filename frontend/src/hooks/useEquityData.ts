import { useState, useEffect } from 'react';
import type { OHLCVBar, ChartMarker, Timeframe } from '../types/equity';
import { TERMINAL } from '../lib/theme';

const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000';

type ChartDataMap = Record<Timeframe, OHLCVBar[]>;

const TIMEFRAMES: Timeframe[] = ['1wk', '1d', '4h', '1h'];

const EMPTY_CHART_DATA: ChartDataMap = {
  '1wk': [],
  '1d': [],
  '4h': [],
  '1h': [],
};

interface UseEquityDataResult {
  chartData: ChartDataMap;
  earningsMarkers: ChartMarker[];
  dividendMarkers: ChartMarker[];
  loading: boolean;
  error: string | null;
}

export function useEquityData(ticker: string): UseEquityDataResult {
  const [chartData, setChartData] = useState<ChartDataMap>(EMPTY_CHART_DATA);
  const [earningsMarkers, setEarningsMarkers] = useState<ChartMarker[]>([]);
  const [dividendMarkers, setDividendMarkers] = useState<ChartMarker[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!ticker) {
      setChartData(EMPTY_CHART_DATA);
      setEarningsMarkers([]);
      setDividendMarkers([]);
      return;
    }

    let cancelled = false;

    async function fetchAll() {
      setLoading(true);
      setError(null);

      try {
        // Fetch all timeframes and markers in parallel
        const [ohlcvResults, earningsRes, dividendsRes] = await Promise.all([
          Promise.all(
            TIMEFRAMES.map((tf) =>
              fetch(`${API_BASE}/api/equity/ohlcv/${encodeURIComponent(ticker)}/${tf}`)
                .then((r) => r.json())
                .catch(() => ({ bars: [] }))
            )
          ),
          fetch(`${API_BASE}/api/equity/earnings/${encodeURIComponent(ticker)}`)
            .then((r) => r.json())
            .catch(() => ({ earnings_dates: [] })),
          fetch(`${API_BASE}/api/equity/dividends/${encodeURIComponent(ticker)}`)
            .then((r) => r.json())
            .catch(() => ({ dividends: [] })),
        ]);

        if (cancelled) return;

        // Map OHLCV results to chart data
        const newChartData: ChartDataMap = { ...EMPTY_CHART_DATA };
        TIMEFRAMES.forEach((tf, i) => {
          const result = ohlcvResults[i];
          newChartData[tf] = (result?.bars ?? []) as OHLCVBar[];
        });
        setChartData(newChartData);

        // Map earnings dates to chart markers
        const earnings: ChartMarker[] = (earningsRes?.earnings_dates ?? []).map((date: string) => ({
          time: date,
          position: 'aboveBar' as const,
          color: TERMINAL.AMBER,
          shape: 'arrowDown' as const,
          text: 'E',
        }));
        setEarningsMarkers(earnings);

        // Map dividend dates to chart markers
        const dividends: ChartMarker[] = (dividendsRes?.dividends ?? []).map(
          (d: { date: string; amount: number }) => ({
            time: d.date,
            position: 'belowBar' as const,
            color: TERMINAL.GREEN,
            shape: 'circle' as const,
            text: 'D',
          })
        );
        setDividendMarkers(dividends);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Failed to load equity data');
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    fetchAll();

    return () => {
      cancelled = true;
    };
  }, [ticker]);

  return { chartData, earningsMarkers, dividendMarkers, loading, error };
}
