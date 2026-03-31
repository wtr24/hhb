import { useEffect, useState } from "react";
import { TERMINAL } from "../../lib/theme";

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
      .then((json: FundamentalsData) => { setData(json); setLoading(false); })
      .catch((err) => { setError(err.message); setLoading(false); });
  }, [ticker]);

  const rows: Array<{ label: string; value: string }> = data
    ? [
        { label: "P/E", value: fmt(data.pe_ratio) },
        { label: "EV/EBITDA", value: fmt(data.ev_ebitda) },
        { label: "ROE", value: formatPct(data.roe) },
        { label: "D/E", value: fmt(data.debt_equity) },
        { label: "MKT CAP", value: formatMarketCap(data.market_cap) },
      ]
    : [];

  return (
    <div style={{
      height: '100%',
      display: 'flex',
      flexDirection: 'column',
      backgroundColor: TERMINAL.PANEL,
      overflow: 'hidden',
    }}>
      {/* Header */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '5px 10px',
        borderBottom: `1px solid ${TERMINAL.BORDER}`,
        flexShrink: 0,
      }}>
        <span style={{
          fontSize: 9,
          fontWeight: 600,
          letterSpacing: '0.15em',
          color: TERMINAL.CYAN,
        }}>
          FUNDAMENTALS
        </span>
        <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
          {data?.stale && (
            <span style={{
              fontSize: 8,
              color: TERMINAL.AMBER,
              border: `1px solid ${TERMINAL.AMBER}50`,
              padding: '0px 4px',
              borderRadius: 2,
              letterSpacing: '0.1em',
            }}>STALE</span>
          )}
          {data?.source && (
            <span style={{ fontSize: 8, color: TERMINAL.DIM, letterSpacing: '0.08em' }}>24h</span>
          )}
        </div>
      </div>

      {/* Content */}
      <div style={{ flex: 1, padding: '4px 10px', overflow: 'hidden' }}>
        {loading && (
          <div style={{ color: TERMINAL.MUTED, fontSize: 9, paddingTop: 8 }}>LOADING...</div>
        )}
        {error && (
          <div style={{ color: TERMINAL.RED, fontSize: 9, paddingTop: 8 }}>ERR: {error}</div>
        )}
        {rows.map(({ label, value }) => (
          <div key={label} style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            padding: '3px 0',
            borderBottom: `1px solid ${TERMINAL.BORDER}`,
          }}>
            <span style={{ fontSize: 9, color: TERMINAL.MUTED, letterSpacing: '0.08em' }}>
              {label}
            </span>
            <span style={{ fontSize: 11, fontWeight: 600, color: TERMINAL.TEXT }}>
              {value}
            </span>
          </div>
        ))}
        {!loading && !error && !data && (
          <div style={{ color: TERMINAL.DIM, fontSize: 9, paddingTop: 8 }}>NO DATA</div>
        )}
      </div>
    </div>
  );
}

export default FundamentalsPanel;
