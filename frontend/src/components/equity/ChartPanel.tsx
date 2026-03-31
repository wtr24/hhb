import { useEffect, useState } from 'react';
import { CandleChart } from './CandleChart';
import { ExpandedChart } from './ExpandedChart';
import { IndicatorPicker } from './IndicatorPicker';
import type { OHLCVBar, ChartMarker, Timeframe } from '../../types/equity';
import { TIMEFRAME_LABELS } from '../../types/equity';
import type { ActiveIndicator, IndicatorDefinition } from './IndicatorPicker';
import { TERMINAL } from '../../lib/theme';

const ToolBtn = ({
  onClick,
  active,
  children,
}: {
  onClick?: () => void;
  active?: boolean;
  children: React.ReactNode;
}) => (
  <button
    onClick={onClick}
    style={{
      fontFamily: "'JetBrains Mono', monospace",
      fontSize: 9,
      fontWeight: active ? 600 : 400,
      letterSpacing: '0.1em',
      padding: '2px 8px',
      background: active ? `${TERMINAL.CYAN}18` : 'transparent',
      border: active
        ? `1px solid ${TERMINAL.CYAN}80`
        : `1px solid ${TERMINAL.BORDER_BRIGHT}`,
      borderRadius: 3,
      color: active ? TERMINAL.CYAN : TERMINAL.MUTED,
      cursor: 'pointer',
    }}
  >
    {children}
  </button>
);

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
  fibTrigger?: number;
  ewTrigger?: number;
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
  fibTrigger,
  ewTrigger,
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
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 10px',
          height: 30,
          borderBottom: `1px solid ${TERMINAL.BORDER}`,
          backgroundColor: TERMINAL.PANEL,
          flexShrink: 0,
        }}>
          <span style={{ fontSize: 10, fontWeight: 600, color: TERMINAL.AMBER, letterSpacing: '0.1em' }}>
            {ticker} <span style={{ color: TERMINAL.MUTED }}>·</span> {TIMEFRAME_LABELS[expandedPanel]}
          </span>

          <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
            <div style={{ position: 'relative' }}>
              <ToolBtn onClick={onIndicatorsClick} active={activeIndicatorCount > 0}>
                INDICATORS {activeIndicatorCount > 0 ? `(${activeIndicatorCount})` : ''}
              </ToolBtn>
              <IndicatorPicker
                isOpen={indicatorPickerOpen}
                onClose={onCloseIndicatorPicker ?? (() => {})}
                activeIndicators={activeIndicators}
                onToggle={onToggleIndicator ?? (() => {})}
                onParamChange={onIndicatorParamChange ?? (() => {})}
              />
            </div>
            <ToolBtn onClick={onFibClick} active={fibActive}>FIB</ToolBtn>
            <ToolBtn onClick={onEwClick} active={ewActive}>EW</ToolBtn>
            <ToolBtn onClick={() => setExpandedPanel(null)}>ESC</ToolBtn>
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
            fibTrigger={fibTrigger}
            ewTrigger={ewTrigger}
          />
        </div>
      </div>
    );
  }

  // Default 4-panel grid view (D-05)
  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: '1fr 1fr',
      gridTemplateRows: '1fr 1fr',
      width: '100%',
      height: '100%',
      gap: 1,
      backgroundColor: TERMINAL.BORDER,
    }}>
      {TIMEFRAMES.map((tf) => (
        <div
          key={tf}
          style={{ overflow: 'hidden', backgroundColor: TERMINAL.BG }}
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
