/**
 * FundamentalsPanel — right sidebar panel for key valuation metrics.
 *
 * D-01: Right sidebar, compact vertical list with amber/green terminal styling.
 * D-02: Stale badge shown when data is not fresh.
 * EQUITY-06: P/E, EV/EBITDA, ROE, Debt/Equity, Market Cap.
 */
import { useEffect, useState } from "react";

interface FundamentalsData {
  ticker: string;
  pe_ratio: number | null;
  ev_ebitda: number | null;
  roe: number | null;
  debt_equity: number | null;
  market_cap: number | null;
  stale: boolean;
  source: string;
}

interface Props {
  ticker: string;
}

function formatMarketCap(value: number | null): string {
  if (value === null || value === undefined) return "--";
  if (value >= 1_000_000_000_000) return `$${(value / 1_000_000_000_000).toFixed(2)}T`;
  if (value >= 1_000_000_000) return `$${(value / 1_000_000_000).toFixed(2)}B`;
  if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(2)}M`;
  return `$${value.toLocaleString()}`;
}

function formatPct(value: number | null): string {
  if (value === null || value === undefined) return "--";
  // ROE from yfinance is a decimal (e.g. 0.45 = 45%)
  const pct = Math.abs(value) <= 5 ? value * 100 : value;
  return `${pct.toFixed(2)}%`;
}

function fmt(value: number | null, decimals = 2): string {
  if (value === null || value === undefined) return "--";
  return value.toFixed(decimals);
}

export function FundamentalsPanel({ ticker }: Props) {
  const [data, setData] = useState<FundamentalsData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!ticker) return;
    setLoading(true);
    setError(null);
    setData(null);

    fetch(`/api/equity/fundamentals/${ticker}`)
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((json: FundamentalsData) => {
        setData(json);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, [ticker]);

  const rows: Array<{ label: string; value: string }> = data
    ? [
        { label: "P/E", value: fmt(data.pe_ratio) },
        { label: "EV/EBITDA", value: fmt(data.ev_ebitda) },
        { label: "ROE", value: formatPct(data.roe) },
        { label: "Debt/Equity", value: fmt(data.debt_equity) },
        { label: "Market Cap", value: formatMarketCap(data.market_cap) },
      ]
    : [];

  return (
    <div className="border border-terminal-border p-2 text-xs font-terminal">
      {/* Header row */}
      <div className="flex justify-between items-center mb-1 border-b border-terminal-border pb-1">
        <span className="text-terminal-amber font-bold tracking-wider">FUNDAMENTALS</span>
        <div className="flex gap-1">
          {data?.stale && (
            <span className="text-terminal-amber text-xs border border-terminal-amber px-1">
              STALE
            </span>
          )}
          {data?.source && (
            <span className="text-terminal-dim text-xs">24h</span>
          )}
        </div>
      </div>

      {/* Content */}
      {loading && (
        <div className="text-terminal-dim text-xs py-1">Loading...</div>
      )}
      {error && (
        <div className="text-terminal-red text-xs py-1">Error: {error}</div>
      )}
      {data && rows.map(({ label, value }) => (
        <div key={label} className="flex justify-between py-0.5">
          <span className="text-terminal-amber">{label}</span>
          <span className="text-terminal-green">{value}</span>
        </div>
      ))}
      {!loading && !error && !data && (
        <div className="text-terminal-dim text-xs py-1">No data</div>
      )}
    </div>
  );
}

export default FundamentalsPanel;
