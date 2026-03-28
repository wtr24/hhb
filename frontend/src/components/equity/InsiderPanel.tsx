/**
 * InsiderPanel — right sidebar panel for insider transaction clustering.
 *
 * D-01: Right sidebar, compact terminal styling.
 * EQUITY-08: Buy/sell counts, B/S ratio, multi-insider signal.
 * US-only: LSE tickers show US-only message.
 */
import { useEffect, useState } from "react";

interface InsiderCluster {
  start_date: string;
  end_date: string;
  transactions: Array<{
    name: string;
    transactionCode: string;
    transactionDate: string;
    share: number;
    transactionPrice: number;
  }>;
}

interface InsiderData {
  ticker: string;
  available: boolean;
  buy_count?: number;
  sell_count?: number;
  buy_sell_ratio?: number | null;
  multi_insider?: boolean;
  clusters?: InsiderCluster[];
  message?: string;
  source?: string;
}

interface Props {
  ticker: string;
}

function fmt(value: number | null | undefined, decimals = 2): string {
  if (value === null || value === undefined) return "--";
  return value.toFixed(decimals);
}

export function InsiderPanel({ ticker }: Props) {
  const [data, setData] = useState<InsiderData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!ticker) return;
    setLoading(true);
    setError(null);
    setData(null);

    fetch(`/api/equity/insiders/${ticker}`)
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((json: InsiderData) => {
        setData(json);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, [ticker]);

  const clusterCount = data?.clusters?.length ?? 0;

  return (
    <div className="border border-terminal-border p-2 text-xs font-terminal">
      {/* Header row */}
      <div className="flex justify-between items-center mb-1 border-b border-terminal-border pb-1">
        <span className="text-terminal-amber font-bold tracking-wider">
          INSIDER ACTIVITY
          {data && !data.available && (
            <span className="text-terminal-dim ml-1">[US ONLY]</span>
          )}
        </span>
        {data?.available && data?.multi_insider && (
          <span className="text-terminal-amber text-xs border border-terminal-amber px-1">
            MULTI-BUY
          </span>
        )}
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
            <div className="flex gap-3">
              <span className="text-terminal-amber">Buys</span>
              <span className="text-terminal-green">{data.buy_count ?? 0}</span>
            </div>
            <div className="flex gap-3">
              <span className="text-terminal-amber">Sells</span>
              <span className="text-terminal-red">{data.sell_count ?? 0}</span>
            </div>
          </div>
          <div className="flex justify-between py-0.5">
            <span className="text-terminal-amber">B/S Ratio</span>
            <span className="text-terminal-green">{fmt(data.buy_sell_ratio)}</span>
          </div>
          <div className="flex justify-between py-0.5">
            <span className="text-terminal-amber">Clusters</span>
            <span className="text-terminal-green">
              {clusterCount} (last 30d)
            </span>
          </div>
        </>
      )}
      {!loading && !error && !data && (
        <div className="text-terminal-dim text-xs py-1">No data</div>
      )}
    </div>
  );
}

export default InsiderPanel;
