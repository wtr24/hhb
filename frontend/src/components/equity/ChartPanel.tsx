import { useEffect, useState } from 'react';
import { CandleChart } from './CandleChart';
import { ExpandedChart } from './ExpandedChart';
import { IndicatorPicker } from './IndicatorPicker';
import type { OHLCVBar, ChartMarker, Timeframe } from '../../types/equity';
import { TIMEFRAME_LABELS } from '../../types/equity';
import type { ActiveIndicator, IndicatorDefinition } from './IndicatorPicker';
import { TERMINAL } from '../../lib/theme';

interface ChartPanelProps {
  ticker: string;
  chartData: Record<Timeframe, OHLCVBar[]>;
  earningsMarkers: ChartMarker[];
  dividendMarkers: ChartMarker[];
  // TA indicator controls (only relevant in expanded mode)
  onIndicatorsClick?: () => void;
  onFibClick?: () => void;
  onEwClick?: () => void;
  activeIndicatorCount?: number;
  fibActive?: boolean;
  ewActive?: boolean;
  activeIndicators?: ActiveIndicator[];
  onToggleIndicator?: (def: IndicatorDefinition) => void;
  onIndicatorParamChange?: (id: string, params: Record<string, number>) => void;
  onRemoveIndicator?: (id: string) => void;
  indicatorPickerOpen?: boolean;
  onCloseIndicatorPicker?: () => void;
}

const TIMEFRAMES: Timeframe[] = ['1wk', '1d', '4h', '1h'];

export function ChartPanel({
  ticker,
  chartData,
  earningsMarkers,
  dividendMarkers,
  onIndicatorsClick,
  onFibClick,
  onEwClick,
  activeIndicatorCount = 0,
  fibActive = false,
  ewActive = false,
  activeIndicators = [],
  onToggleIndicator,
  onIndicatorParamChange,
  onRemoveIndicator,
  indicatorPickerOpen = false,
  onCloseIndicatorPicker,
}: ChartPanelProps) {
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
    const indicatorsBtnLabel = activeIndicatorCount > 0
      ? `[Indicators ▾ (${activeIndicatorCount})]`
      : '[Indicators ▾]';

    return (
      <div className="w-full h-full border border-terminal-border flex flex-col">
        {/* Expanded header with TA controls */}
        <div className="flex items-center justify-between px-2 py-0.5 border-b border-terminal-border text-xs flex-shrink-0" style={{ minHeight: 24 }}>
          <span className="text-terminal-amber">
            {ticker} — {TIMEFRAME_LABELS[expandedPanel]}
          </span>

          {/* TA toolbar — only in expanded mode */}
          <div className="flex items-center gap-1 relative">
            {/* Indicators button with picker anchor */}
            <div style={{ position: 'relative' }}>
              <button
                onClick={onIndicatorsClick}
                style={{
                  background: TERMINAL.BG,
                  border: `1px solid ${TERMINAL.BORDER}`,
                  color: TERMINAL.AMBER,
                  padding: '4px 8px',
                  fontSize: 11,
                  cursor: 'pointer',
                }}
              >
                {indicatorsBtnLabel}
              </button>
              <IndicatorPicker
                isOpen={indicatorPickerOpen}
                onClose={onCloseIndicatorPicker ?? (() => {})}
                activeIndicators={activeIndicators}
                onToggle={onToggleIndicator ?? (() => {})}
                onParamChange={onIndicatorParamChange ?? (() => {})}
              />
            </div>

            {/* Fibonacci button */}
            <button
              onClick={onFibClick}
              style={{
                background: TERMINAL.BG,
                border: fibActive ? `1px solid ${TERMINAL.AMBER}` : `1px solid ${TERMINAL.BORDER}`,
                color: TERMINAL.AMBER,
                padding: '4px 8px',
                fontSize: 11,
                cursor: 'pointer',
              }}
            >
              [Fib]
            </button>

            {/* Elliott Wave button */}
            <button
              onClick={onEwClick}
              style={{
                background: TERMINAL.BG,
                border: ewActive ? `1px solid ${TERMINAL.AMBER}` : `1px solid ${TERMINAL.BORDER}`,
                color: TERMINAL.AMBER,
                padding: '4px 8px',
                fontSize: 11,
                cursor: 'pointer',
              }}
            >
              [EW]
            </button>

            <button
              onClick={() => setExpandedPanel(null)}
              className="text-terminal-dim hover:text-terminal-amber"
              style={{ marginLeft: 8 }}
            >
              [ESC] COLLAPSE
            </button>
          </div>
        </div>

        {/* Chart area — ExpandedChart handles sub-panes */}
        <div className="flex-1 min-h-0 overflow-hidden">
          <ExpandedChart
            ticker={ticker}
            timeframe={expandedPanel}
            activeIndicators={activeIndicators}
            onIndicatorParamChange={onIndicatorParamChange ?? (() => {})}
            onRemoveIndicator={onRemoveIndicator ?? (() => {})}
            chartData={chartData[expandedPanel]}
            markers={allMarkers}
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
