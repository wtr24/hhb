/**
 * ShortInterestPanel — right sidebar panel for short interest data.
 *
 * D-01: Right sidebar, compact terminal styling.
 * EQUITY-07: Short interest % float, short ratio, days to cover.
 * US-only: LSE tickers show US-only message.
 */
import { useEffect, useState } from "react";

interface ShortInterestData {
  ticker: string;
  available: boolean;
  short_interest?: number | null;
  shares_outstanding?: number | null;
  pct_float?: number | null;
  date?: string | null;
  message?: string;
  source?: string;
}

interface Props {
  ticker: string;
}

function formatLargeNum(value: number | null | undefined): string {
  if (value === null || value === undefined) return "--";
  if (value >= 1_000_000_000) return `${(value / 1_000_000_000).toFixed(1)}B`;
  if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `${(value / 1_000).toFixed(1)}K`;
  return value.toLocaleString();
}

function fmt(value: number | null | undefined, decimals = 2): string {
  if (value === null || value === undefined) return "--";
  return value.toFixed(decimals);
}

export function ShortInterestPanel({ ticker }: Props) {
  const [data, setData] = useState<ShortInterestData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!ticker) return;
    setLoading(true);
    setError(null);
    setData(null);

    fetch(`/api/equity/short-interest/${ticker}`)
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((json: ShortInterestData) => {
        setData(json);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, [ticker]);

  return (
    <div className="border border-terminal-border p-2 text-xs font-terminal">
      {/* Header row */}
      <div className="flex justify-between items-center mb-1 border-b border-terminal-border pb-1">
        <span className="text-terminal-amber font-bold tracking-wider">
          SHORT INTEREST
          {data && !data.available && (
            <span className="text-terminal-dim ml-1">[US ONLY]</span>
          )}
        </span>
      </div>

      {/* Content */}
      {loading && (
        <div className="text-terminal-dim text-xs py-1">Loading...</div>
      )}
      {error && (
        <div className="text-terminal-red text-xs py-1">Error: {error}</div>
      )}
      {data && !data.available && (
        <div className="text-terminal-dim text-xs py-1">
          {data.message || "US tickers only"}
        </div>
      )}
      {data && data.available && (
        <>
          <div className="flex justify-between py-0.5">
            <span className="text-terminal-amber">% Float Short</span>
            <span className="text-terminal-green">{fmt(data.pct_float)}%</span>
          </div>
          <div className="flex justify-between py-0.5">
            <span className="text-terminal-amber">Short Interest</span>
            <span className="text-terminal-green">{formatLargeNum(data.short_interest)}</span>
          </div>
          <div className="flex justify-between py-0.5">
            <span className="text-terminal-amber">Date</span>
            <span className="text-terminal-green">{data.date ?? "--"}</span>
          </div>
        </>
      )}
      {!loading && !error && !data && (
        <div className="text-terminal-dim text-xs py-1">No data</div>
      )}
    </div>
  );
}

export default ShortInterestPanel;
