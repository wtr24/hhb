/**
 * OptionsChain — options chain table with Black-Scholes Greeks.
 *
 * Layout per D-08: calls on left, strike in centre column, puts on right.
 * IV surface heatmap above table per D-09. IV rank badge in header per D-09.
 * Greeks per row (delta, gamma, vega, theta) per D-10.
 * LSE tickers show OPTIONS [NOT AVAILABLE] message.
 * Expiry selector allows switching between available expiries.
 */
import { useState, useEffect } from 'react';
import IVSurface, { IVSurfaceData } from './IVSurface';

interface OptionContract {
  strike: number;
  bid: number;
  ask: number;
  lastPrice: number;
  volume: number;
  openInterest: number;
  iv: number;
  delta: number | null;
  gamma: number | null;
  vega: number | null;
  theta: number | null;
}

interface OptionsData {
  ticker: string;
  available: boolean;
  message?: string;
  expiry?: string;
  expiries?: string[];
  current_price?: number;
  iv_rank?: number;
  calls?: OptionContract[];
  puts?: OptionContract[];
  iv_surface?: IVSurfaceData;
  source?: string;
}

interface OptionsChainProps {
  ticker: string;
}

function fmt(val: number | null | undefined, decimals = 2): string {
  if (val === null || val === undefined) return '--';
  return val.toFixed(decimals);
}

function fmtIV(val: number | null | undefined): string {
  if (val === null || val === undefined) return '--';
  return (val * 100).toFixed(1) + '%';
}

export default function OptionsChain({ ticker }: OptionsChainProps) {
  const [data, setData] = useState<OptionsData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedExpiry, setSelectedExpiry] = useState<string | null>(null);
  const [expiryData, setExpiryData] = useState<{ calls: OptionContract[]; puts: OptionContract[] } | null>(null);

  // Fetch full options data when ticker changes
  useEffect(() => {
    if (!ticker) return;
    setLoading(true);
    setError(null);
    setData(null);
    setSelectedExpiry(null);
    setExpiryData(null);

    fetch(`/api/equity/options/${ticker}`)
      .then(r => r.json())
      .then((d: OptionsData) => {
        setData(d);
        if (d.available && d.expiry) {
          setSelectedExpiry(d.expiry);
          setExpiryData({ calls: d.calls ?? [], puts: d.puts ?? [] });
        }
      })
      .catch(err => setError(String(err)))
      .finally(() => setLoading(false));
  }, [ticker]);

  // Re-fetch chain when expiry is changed by user
  useEffect(() => {
    if (!selectedExpiry || !ticker || !data?.available) return;
    // If expiry matches initial fetch, use existing data
    if (selectedExpiry === data.expiry) {
      setExpiryData({ calls: data.calls ?? [], puts: data.puts ?? [] });
      return;
    }
    // Different expiry: re-fetch (backend supports ?expiry= or we use the already-fetched expiry endpoint)
    fetch(`/api/equity/options/${ticker}?expiry=${selectedExpiry}`)
      .then(r => r.json())
      .then((d: OptionsData) => {
        if (d.available) {
          setExpiryData({ calls: d.calls ?? [], puts: d.puts ?? [] });
        }
      })
      .catch(() => {/* keep existing data */});
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedExpiry]);

  if (loading) {
    return (
      <div className="w-full h-full bg-[#0a0a0a] border border-[#1a1a1a] flex items-center justify-center">
        <span className="text-xs text-[#ff9900] font-mono animate-pulse">OPTIONS LOADING...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="w-full h-full bg-[#0a0a0a] border border-[#1a1a1a] flex items-center justify-center">
        <span className="text-xs text-[#ff4444] font-mono">OPTIONS ERROR</span>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="w-full h-full bg-[#0a0a0a] border border-[#1a1a1a] flex items-center justify-center">
        <span className="text-xs text-[#404040] font-mono">OPTIONS —</span>
      </div>
    );
  }

  // LSE or unavailable
  if (!data.available) {
    return (
      <div className="w-full h-full bg-[#0a0a0a] border border-[#1a1a1a] flex flex-col items-center justify-center gap-1">
        <span className="text-xs text-[#ff9900] font-mono">OPTIONS [NOT AVAILABLE]</span>
        {data.message && (
          <span className="text-xs text-[#404040] font-mono text-center px-4">{data.message}</span>
        )}
      </div>
    );
  }

  const calls = expiryData?.calls ?? [];
  const puts = expiryData?.puts ?? [];

  // Merge by strike for the centre-column layout
  // Build a map of strike -> call/put contract
  const callsByStrike = new Map(calls.map(c => [c.strike, c]));
  const putsByStrike = new Map(puts.map(p => [p.strike, p]));
  const allStrikes = Array.from(
    new Set([...calls.map(c => c.strike), ...puts.map(p => p.strike)])
  ).sort((a, b) => a - b);

  // ATM: strike closest to current_price
  const currentPrice = data.current_price ?? 0;
  const atmStrike = allStrikes.reduce(
    (best, s) => Math.abs(s - currentPrice) < Math.abs(best - currentPrice) ? s : best,
    allStrikes[0] ?? 0,
  );

  return (
    <div className="w-full h-full flex flex-col bg-[#0a0a0a] border border-[#1a1a1a] overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-2 py-1 border-b border-[#1a1a1a] shrink-0">
        <span className="text-xs text-[#ff9900] font-mono font-bold">
          OPTIONS — {selectedExpiry ?? data.expiry}
        </span>
        <span className="text-xs font-mono px-1 py-0.5 bg-[#ff9900] text-[#0a0a0a] font-bold">
          IV RANK: {fmt(data.iv_rank, 1)}%
        </span>
      </div>

      {/* Expiry selector */}
      {data.expiries && data.expiries.length > 1 && (
        <div className="flex gap-1 px-2 py-1 border-b border-[#1a1a1a] overflow-x-auto shrink-0">
          {data.expiries.map(exp => (
            <button
              key={exp}
              onClick={() => setSelectedExpiry(exp)}
              className={`text-xs font-mono px-1.5 py-0.5 border whitespace-nowrap ${
                selectedExpiry === exp
                  ? 'border-[#ff9900] text-[#ff9900]'
                  : 'border-[#1a1a1a] text-[#404040] hover:border-[#404040] hover:text-[#ff9900]'
              }`}
            >
              {exp}
            </button>
          ))}
        </div>
      )}

      {/* IV Surface heatmap */}
      {data.iv_surface && (
        <div className="shrink-0">
          <IVSurface surfaceData={data.iv_surface} />
        </div>
      )}

      {/* Options table */}
      <div className="flex-1 overflow-y-auto">
        <table className="w-full text-xs font-mono border-collapse">
          <thead className="sticky top-0 bg-[#0a0a0a]">
            <tr className="border-b border-[#1a1a1a]">
              {/* Calls side */}
              <th className="text-[#ff9900] text-right px-1 py-0.5 w-10">C.Delta</th>
              <th className="text-[#ff9900] text-right px-1 py-0.5 w-10">C.Gamma</th>
              <th className="text-[#ff9900] text-right px-1 py-0.5 w-10">C.Vega</th>
              <th className="text-[#ff9900] text-right px-1 py-0.5 w-10">C.Theta</th>
              <th className="text-[#ff9900] text-right px-1 py-0.5 w-12">C.Bid</th>
              <th className="text-[#ff9900] text-right px-1 py-0.5 w-12">C.Ask</th>
              <th className="text-[#ff9900] text-right px-1 py-0.5 w-10">C.IV</th>
              {/* Strike */}
              <th className="text-[#ff9900] text-center px-1 py-0.5 w-14 border-x border-[#1a1a1a]">STRIKE</th>
              {/* Puts side */}
              <th className="text-[#ff4444] text-left px-1 py-0.5 w-12">P.Bid</th>
              <th className="text-[#ff4444] text-left px-1 py-0.5 w-12">P.Ask</th>
              <th className="text-[#ff4444] text-left px-1 py-0.5 w-10">P.IV</th>
              <th className="text-[#ff4444] text-left px-1 py-0.5 w-10">P.Delta</th>
              <th className="text-[#ff4444] text-left px-1 py-0.5 w-10">P.Gamma</th>
              <th className="text-[#ff4444] text-left px-1 py-0.5 w-10">P.Vega</th>
              <th className="text-[#ff4444] text-left px-1 py-0.5 w-10">P.Theta</th>
            </tr>
          </thead>
          <tbody>
            {allStrikes.map(strike => {
              const call = callsByStrike.get(strike);
              const put = putsByStrike.get(strike);
              const isAtm = strike === atmStrike;
              const isItm = call ? (call.delta !== null && call.delta > 0.5) : false;

              let rowClass = 'border-b border-[#1a1a1a]';
              if (isAtm) rowClass += ' bg-[#1a1a1a]';
              else if (isItm) rowClass += ' bg-[#1a1a1a]/30';

              return (
                <tr key={strike} className={rowClass}>
                  {/* Call side */}
                  <td className="text-[#00d084] text-right px-1 py-0.5">{fmt(call?.delta, 3)}</td>
                  <td className="text-[#00d084] text-right px-1 py-0.5">{fmt(call?.gamma, 4)}</td>
                  <td className="text-[#00d084] text-right px-1 py-0.5">{fmt(call?.vega, 3)}</td>
                  <td className="text-[#00d084] text-right px-1 py-0.5">{fmt(call?.theta, 4)}</td>
                  <td className="text-[#00d084] text-right px-1 py-0.5">{fmt(call?.bid)}</td>
                  <td className="text-[#00d084] text-right px-1 py-0.5">{fmt(call?.ask)}</td>
                  <td className="text-[#00d084] text-right px-1 py-0.5">{fmtIV(call?.iv)}</td>
                  {/* Strike centre */}
                  <td className={`text-center px-1 py-0.5 border-x border-[#1a1a1a] font-bold ${isAtm ? 'text-[#ff9900]' : 'text-[#ff9900]/70'}`}>
                    {strike.toFixed(2)}
                  </td>
                  {/* Put side */}
                  <td className="text-[#ff4444] text-left px-1 py-0.5">{fmt(put?.bid)}</td>
                  <td className="text-[#ff4444] text-left px-1 py-0.5">{fmt(put?.ask)}</td>
                  <td className="text-[#ff4444] text-left px-1 py-0.5">{fmtIV(put?.iv)}</td>
                  <td className="text-[#ff4444] text-left px-1 py-0.5">{fmt(put?.delta, 3)}</td>
                  <td className="text-[#ff4444] text-left px-1 py-0.5">{fmt(put?.gamma, 4)}</td>
                  <td className="text-[#ff4444] text-left px-1 py-0.5">{fmt(put?.vega, 3)}</td>
                  <td className="text-[#ff4444] text-left px-1 py-0.5">{fmt(put?.theta, 4)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
