/**
 * EquityModule — master Bloomberg grid layout (D-01).
 *
 * Fixed-height viewport layout. Nothing scrolls except the news panel (D-11).
 * Layout zones:
 *   Row 1: TickerCommandBar (auto height, ~30px)
 *   Row 2: QuoteBar with GBP toggle (auto height, ~24px)
 *   Row 3: Main content area — ChartPanel (60%) | Fundamentals+ShortInterest+Insider sidebar (40%)
 *   Row 4: Bottom row — OptionsChain (60%) | NewsPanel (40%)
 *
 * On ticker submit (D-04): all panels refresh simultaneously via ticker state change.
 * GBP toggle (D-12): fetches /api/fx/USD/GBP on activation, applies rate to QuoteBar.
 */
import { useState, useEffect } from 'react';
import { useEquityWebSocket } from '../../hooks/useEquityWebSocket';
import { useEquityData } from '../../hooks/useEquityData';
import { TickerCommandBar } from './TickerCommandBar';
import { QuoteBar } from './QuoteBar';
import { ChartPanel } from './ChartPanel';
import { FundamentalsPanel } from './FundamentalsPanel';
import { ShortInterestPanel } from './ShortInterestPanel';
import { InsiderPanel } from './InsiderPanel';
import { NewsPanel } from './NewsPanel';
import OptionsChain from './OptionsChain';
import type { ActiveIndicator, IndicatorDefinition } from './IndicatorPicker';

interface FXRateResponse {
  rate: number;
}

export function EquityModule() {
  const [ticker, setTicker] = useState<string>('');
  const [gbpMode, setGbpMode] = useState(false);
  const [gbpRate, setGbpRate] = useState<number | null>(null);

  // TA indicator state (TA-01 through TA-08)
  const [activeIndicators, setActiveIndicators] = useState<ActiveIndicator[]>([]);
  const [fibActive, setFibActive] = useState(false);
  const [ewActive, setEwActive] = useState(false);
  const [fibTrigger, setFibTrigger] = useState(0);
  const [ewTrigger, setEwTrigger] = useState(0);
  const [indicatorPickerOpen, setIndicatorPickerOpen] = useState(false);

  const quote = useEquityWebSocket(ticker);
  const { chartData, earningsMarkers, dividendMarkers } = useEquityData(ticker);

  // Fetch GBP rate when gbpMode is toggled on (EQUITY-11, D-12)
  useEffect(() => {
    if (gbpMode && gbpRate === null) {
      fetch('/api/fx/USD/GBP')
        .then((r) => r.json())
        .then((data: FXRateResponse) => {
          if (data?.rate) {
            setGbpRate(data.rate);
          }
        })
        .catch(() => {
          // Silently fail — GBPToggle will remain active but no conversion applied
        });
    }
  }, [gbpMode, gbpRate]);

  function handleGbpToggle() {
    setGbpMode((prev) => !prev);
  }

  // Indicator handlers
  function handleToggleIndicator(def: IndicatorDefinition) {
    setActiveIndicators((prev) => {
      const existing = prev.find((a) => a.name === def.name);
      if (existing) {
        // Remove it
        return prev.filter((a) => a.name !== def.name);
      }
      // Add it with a unique id
      const id = `${def.name}_${Object.values(def.defaultParams).join('_') || 'default'}`;
      return [
        ...prev,
        {
          id,
          name: def.name,
          label: def.label,
          params: { ...def.defaultParams },
          paneType: def.paneType,
        },
      ];
    });
  }

  function handleIndicatorParamChange(id: string, params: Record<string, number>) {
    setActiveIndicators((prev) =>
      prev.map((a) => {
        if (a.id !== id) return a;
        // Rebuild id to reflect new params
        const newId = `${a.name}_${Object.values(params).join('_') || 'default'}`;
        return { ...a, id: newId, params };
      })
    );
  }

  function handleRemoveIndicator(id: string) {
    setActiveIndicators((prev) => prev.filter((a) => a.id !== id));
  }

  function handleTickerSubmit(newTicker: string) {
    setTicker(newTicker);
    // Clear indicator state on ticker change (D-04 extension)
    setActiveIndicators([]);
    setFibActive(false);
    setEwActive(false);
    setIndicatorPickerOpen(false);
  }

  return (
    <div className="h-full flex flex-col bg-terminal-bg text-terminal-amber font-terminal text-xs overflow-hidden">
      {/* Row 1: Ticker command bar */}
      <TickerCommandBar onSubmit={handleTickerSubmit} />

      {/* Row 2: Live quote bar with GBP toggle */}
      <QuoteBar
        quote={quote}
        gbpMode={gbpMode}
        gbpRate={gbpRate}
        onGbpToggle={handleGbpToggle}
      />

      {/* No ticker — placeholder */}
      {!ticker && (
        <div className="flex-1 flex items-center justify-center">
          <span className="text-terminal-dim tracking-widest">
            TYPE A TICKER TO BEGIN
          </span>
        </div>
      )}

      {/* Rows 3 + 4: Main grid — only shown once ticker is entered */}
      {ticker && (
        <div className="flex-1 grid grid-rows-[1fr_minmax(200px,25vh)] overflow-hidden min-h-0">

          {/* Row 3: Main content — ChartPanel (60%) | Right sidebar (40%) */}
          <div className="grid grid-cols-[60%_40%] overflow-hidden min-h-0">

            {/* Left: 4-panel candlestick chart grid (D-05, D-06, D-07) */}
            <div className="border border-terminal-border overflow-hidden min-h-0">
              <ChartPanel
                ticker={ticker}
                chartData={chartData}
                earningsMarkers={earningsMarkers}
                dividendMarkers={dividendMarkers}
                onIndicatorsClick={() => setIndicatorPickerOpen((p) => !p)}
                onFibClick={() => { setFibActive((p) => !p); setFibTrigger((p) => p + 1); }}
                onEwClick={() => { setEwActive((p) => !p); setEwTrigger((p) => p + 1); }}
                activeIndicatorCount={activeIndicators.length}
                fibActive={fibActive}
                ewActive={ewActive}
                fibTrigger={fibTrigger}
                ewTrigger={ewTrigger}
                activeIndicators={activeIndicators}
                onToggleIndicator={handleToggleIndicator}
                onIndicatorParamChange={handleIndicatorParamChange}
                onRemoveIndicator={handleRemoveIndicator}
                indicatorPickerOpen={indicatorPickerOpen}
                onCloseIndicatorPicker={() => setIndicatorPickerOpen(false)}
              />
            </div>

            {/* Right: Stacked fundamentals / short interest / insider panels */}
            <div className="flex flex-col overflow-hidden min-h-0">
              <div className="flex-1 overflow-hidden min-h-0">
                <FundamentalsPanel ticker={ticker} />
              </div>
              <div className="flex-1 overflow-hidden min-h-0">
                <ShortInterestPanel ticker={ticker} />
              </div>
              <div className="flex-1 overflow-hidden min-h-0">
                <InsiderPanel ticker={ticker} />
              </div>
            </div>
          </div>

          {/* Row 4: Bottom row — OptionsChain (60%) | News (40%) */}
          <div className="grid grid-cols-[60%_40%] overflow-hidden min-h-0">

            {/* Left: Options chain + IV surface (D-08, D-09, D-10) */}
            <div className="border border-terminal-border overflow-hidden min-h-0">
              <OptionsChain ticker={ticker} />
            </div>

            {/* Right: News feed — scrollable (D-11 exception) */}
            <div className="border border-terminal-border overflow-hidden min-h-0">
              <NewsPanel ticker={ticker} />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default EquityModule;
