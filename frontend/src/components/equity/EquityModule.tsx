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
import { TERMINAL } from '../../lib/theme';
import type { ActiveIndicator, IndicatorDefinition } from './IndicatorPicker';

interface FXRateResponse {
  rate: number;
}

export function EquityModule() {
  const [ticker, setTicker] = useState<string>('');
  const [gbpMode, setGbpMode] = useState(false);
  const [gbpRate, setGbpRate] = useState<number | null>(null);

  const [activeIndicators, setActiveIndicators] = useState<ActiveIndicator[]>([]);
  const [fibActive, setFibActive] = useState(false);
  const [ewActive, setEwActive] = useState(false);
  const [fibTrigger, setFibTrigger] = useState(0);
  const [ewTrigger, setEwTrigger] = useState(0);
  const [indicatorPickerOpen, setIndicatorPickerOpen] = useState(false);

  const quote = useEquityWebSocket(ticker);
  const { chartData, earningsMarkers, dividendMarkers } = useEquityData(ticker);

  useEffect(() => {
    if (gbpMode && gbpRate === null) {
      fetch('/api/fx/USD/GBP')
        .then((r) => r.json())
        .then((data: FXRateResponse) => {
          if (data?.rate) setGbpRate(data.rate);
        })
        .catch(() => {});
    }
  }, [gbpMode, gbpRate]);

  function handleGbpToggle() {
    setGbpMode((prev) => !prev);
  }

  function handleToggleIndicator(def: IndicatorDefinition) {
    setActiveIndicators((prev) => {
      const existing = prev.find((a) => a.name === def.name);
      if (existing) return prev.filter((a) => a.name !== def.name);
      const id = `${def.name}_${Object.values(def.defaultParams).join('_') || 'default'}`;
      return [...prev, { id, name: def.name, label: def.label, params: { ...def.defaultParams }, paneType: def.paneType }];
    });
  }

  function handleIndicatorParamChange(id: string, params: Record<string, number>) {
    setActiveIndicators((prev) =>
      prev.map((a) => {
        if (a.id !== id) return a;
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
    setActiveIndicators([]);
    setFibActive(false);
    setEwActive(false);
    setIndicatorPickerOpen(false);
  }

  return (
    <div style={{
      height: '100%',
      display: 'flex',
      flexDirection: 'column',
      backgroundColor: TERMINAL.BG,
      overflow: 'hidden',
    }}>
      <TickerCommandBar onSubmit={handleTickerSubmit} />
      <QuoteBar quote={quote} gbpMode={gbpMode} gbpRate={gbpRate} onGbpToggle={handleGbpToggle} />

      {!ticker && (
        <div style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 14,
        }}>
          <div style={{
            width: 48,
            height: 48,
            borderRadius: '50%',
            border: `1px solid ${TERMINAL.BORDER_BRIGHT}`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}>
            <div style={{
              width: 16,
              height: 16,
              background: `linear-gradient(135deg, ${TERMINAL.CYAN}60, ${TERMINAL.AMBER}60)`,
              borderRadius: '50%',
            }} />
          </div>
          <div style={{
            fontSize: 9,
            letterSpacing: '0.25em',
            color: TERMINAL.MUTED,
            textTransform: 'uppercase',
          }}>
            Enter a ticker symbol to begin
          </div>
          <div style={{
            fontSize: 9,
            color: TERMINAL.DIM,
            letterSpacing: '0.1em',
          }}>
            e.g. AAPL · TSLA · LLOY.L · ^FTSE
          </div>
        </div>
      )}

      {ticker && (
        <div style={{
          flex: 1,
          display: 'grid',
          gridTemplateRows: '1fr minmax(180px, 22vh)',
          overflow: 'hidden',
          minHeight: 0,
          gap: 1,
          backgroundColor: TERMINAL.BORDER,
        }}>
          {/* Row 3: Charts + sidebar */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: '60% 40%',
            overflow: 'hidden',
            minHeight: 0,
            gap: 1,
            backgroundColor: TERMINAL.BORDER,
          }}>
            <div style={{ backgroundColor: TERMINAL.BG, overflow: 'hidden', minHeight: 0 }}>
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

            <div style={{
              display: 'flex',
              flexDirection: 'column',
              overflow: 'hidden',
              minHeight: 0,
              gap: 1,
              backgroundColor: TERMINAL.BORDER,
            }}>
              <div style={{ flex: 1, overflow: 'hidden', minHeight: 0, backgroundColor: TERMINAL.BG }}>
                <FundamentalsPanel ticker={ticker} />
              </div>
              <div style={{ flex: 1, overflow: 'hidden', minHeight: 0, backgroundColor: TERMINAL.BG }}>
                <ShortInterestPanel ticker={ticker} />
              </div>
              <div style={{ flex: 1, overflow: 'hidden', minHeight: 0, backgroundColor: TERMINAL.BG }}>
                <InsiderPanel ticker={ticker} />
              </div>
            </div>
          </div>

          {/* Row 4: Options + News */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: '60% 40%',
            overflow: 'hidden',
            minHeight: 0,
            gap: 1,
            backgroundColor: TERMINAL.BORDER,
          }}>
            <div style={{ backgroundColor: TERMINAL.BG, overflow: 'hidden', minHeight: 0 }}>
              <OptionsChain ticker={ticker} />
            </div>
            <div style={{ backgroundColor: TERMINAL.BG, overflow: 'hidden', minHeight: 0 }}>
              <NewsPanel ticker={ticker} />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default EquityModule;
