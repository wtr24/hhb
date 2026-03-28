/**
 * NewsPanel — bottom-right panel for company news feed.
 *
 * D-11: Scrollable news list within fixed panel height.
 * EQUITY-10: Auto-refreshes every 5 minutes.
 * Each headline links to its URL; sentiment badge placeholder until Phase 7 FinBERT.
 */
import { useEffect, useState } from "react";

interface NewsItem {
  headline: string;
  source: string;
  url: string;
  datetime: number | string;
  summary: string;
}

interface NewsData {
  ticker: string;
  news: NewsItem[];
  stale: boolean;
  error?: string;
}

interface Props {
  ticker: string;
}

const REFRESH_INTERVAL_MS = 5 * 60 * 1000; // 5 minutes

function relativeTime(ts: number | string): string {
  if (!ts) return "";
  const epoch = typeof ts === "number" ? ts : parseInt(ts, 10);
  if (isNaN(epoch)) return String(ts);
  const diffMs = Date.now() - epoch * 1000;
  const diffMins = Math.floor(diffMs / 60000);
  if (diffMins < 60) return `${diffMins}m ago`;
  const diffHours = Math.floor(diffMins / 60);
  if (diffHours < 24) return `${diffHours}h ago`;
  const diffDays = Math.floor(diffHours / 24);
  return `${diffDays}d ago`;
}

export function NewsPanel({ ticker }: Props) {
  const [data, setData] = useState<NewsData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function fetchNews() {
    if (!ticker) return;
    setLoading(true);
    fetch(`/api/equity/news/${ticker}`)
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((json: NewsData) => {
        setData(json);
        setLoading(false);
        setError(null);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }

  useEffect(() => {
    fetchNews();
    const interval = setInterval(fetchNews, REFRESH_INTERVAL_MS);
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ticker]);

  return (
    <div className="border border-terminal-border p-2 text-xs font-terminal flex flex-col h-full">
      {/* Header row */}
      <div className="flex justify-between items-center mb-1 border-b border-terminal-border pb-1 flex-shrink-0">
        <span className="text-terminal-amber font-bold tracking-wider">NEWS</span>
        <div className="flex gap-1 items-center">
          {data?.stale && (
            <span className="text-terminal-amber text-xs border border-terminal-amber px-1">
              STALE
            </span>
          )}
          {loading && (
            <span className="text-terminal-dim text-xs">...</span>
          )}
        </div>
      </div>

      {/* Scrollable news list */}
      <div className="overflow-y-auto max-h-full flex-grow">
        {error && (
          <div className="text-terminal-red py-1">Error: {error}</div>
        )}
        {!loading && !error && data?.news?.length === 0 && (
          <div className="text-terminal-dim py-1">No news available</div>
        )}
        {data?.news?.map((item, idx) => (
          <div
            key={idx}
            className="py-1 border-b border-terminal-border last:border-b-0"
          >
            <div className="flex justify-between items-start gap-1">
              <a
                href={item.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-terminal-green hover:text-terminal-amber flex-1 min-w-0 truncate"
                title={item.headline}
              >
                {item.headline}
              </a>
              {/* Sentiment placeholder — Phase 7 FinBERT will replace */}
              <span className="text-terminal-dim flex-shrink-0">[--]</span>
            </div>
            <div className="flex gap-2 text-terminal-dim mt-0.5">
              <span className="truncate max-w-24">{item.source}</span>
              <span>{relativeTime(item.datetime)}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default NewsPanel;
