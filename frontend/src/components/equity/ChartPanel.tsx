import { useEffect, useState } from 'react';
import { CandleChart } from './CandleChart';
import type { OHLCVBar, ChartMarker, Timeframe } from '../../types/equity';
import { TIMEFRAME_LABELS } from '../../types/equity';

interface ChartPanelProps {
  ticker: string;
  chartData: Record<Timeframe, OHLCVBar[]>;
  earningsMarkers: ChartMarker[];
  dividendMarkers: ChartMarker[];
}

const TIMEFRAMES: Timeframe[] = ['1wk', '1d', '4h', '1h'];

export function ChartPanel({ ticker, chartData, earningsMarkers, dividendMarkers }: ChartPanelProps) {
  const [expandedPanel, setExpandedPanel] = useState<Timeframe | null>(null);

  // Combined markers for all charts (D-07)
  const allMarkers = [...earningsMarkers, ...dividendMarkers];

  // Collapse expanded panel on Escape key (D-06)
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape' && expandedPanel !== null) {
        setExpandedPanel(null);
      }
    }
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [expandedPanel]);

  // Expanded single-panel view
  if (expandedPanel !== null) {
    return (
      <div className="w-full h-full border border-terminal-border">
        <div className="flex items-center justify-between px-2 py-0.5 border-b border-terminal-border text-xs">
          <span className="text-terminal-amber">
            {ticker} — {TIMEFRAME_LABELS[expandedPanel]}
          </span>
          <button
            onClick={() => setExpandedPanel(null)}
            className="text-terminal-dim hover:text-terminal-amber"
          >
            [ESC] COLLAPSE
          </button>
        </div>
        <div className="w-full" style={{ height: 'calc(100% - 24px)' }}>
          <CandleChart
            data={chartData[expandedPanel]}
            markers={allMarkers}
            label={TIMEFRAME_LABELS[expandedPanel]}
            onExpand={() => setExpandedPanel(null)}
            expanded={true}
          />
        </div>
      </div>
    );
  }

  // Default 4-panel grid view (D-05)
  return (
    <div className="grid grid-cols-2 grid-rows-2 w-full h-full">
      {TIMEFRAMES.map((tf) => (
        <div
          key={tf}
          className="border border-terminal-border overflow-hidden"
        >
          <CandleChart
            data={chartData[tf]}
            markers={allMarkers}
            label={TIMEFRAME_LABELS[tf]}
            onExpand={() => setExpandedPanel(tf)}
            expanded={false}
          />
        </div>
      ))}
    </div>
  );
}
