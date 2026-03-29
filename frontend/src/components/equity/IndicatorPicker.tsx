import { useEffect, useRef, useState } from 'react';
import { TERMINAL } from '../../lib/theme';

export interface ActiveIndicator {
  id: string;
  name: string;
  label: string;
  params: Record<string, number>;
  paneType: 'overlay' | 'oscillator';
}

export interface IndicatorDefinition {
  name: string;
  label: string;
  paneType: 'overlay' | 'oscillator';
  defaultParams: Record<string, number>;
  disabled?: boolean;
}

const INDICATOR_GROUPS: Record<string, IndicatorDefinition[]> = {
  'Moving Averages': [
    { name: 'SMA', label: 'SMA', paneType: 'overlay', defaultParams: { period: 20 } },
    { name: 'EMA', label: 'EMA', paneType: 'overlay', defaultParams: { period: 20 } },
    { name: 'DEMA', label: 'DEMA', paneType: 'overlay', defaultParams: { period: 20 } },
    { name: 'TEMA', label: 'TEMA', paneType: 'overlay', defaultParams: { period: 20 } },
    { name: 'WMA', label: 'WMA', paneType: 'overlay', defaultParams: { period: 20 } },
    { name: 'HMA', label: 'HMA', paneType: 'overlay', defaultParams: { period: 20 } },
    { name: 'VWMA', label: 'VWMA', paneType: 'overlay', defaultParams: { period: 20 } },
    { name: 'GOLDEN_CROSS', label: 'Golden/Death Cross', paneType: 'overlay', defaultParams: { period: 50, period2: 200 } },
    { name: 'EMA_RIBBON', label: 'EMA Ribbon (8)', paneType: 'overlay', defaultParams: {} },
  ],
  'Momentum': [
    { name: 'RSI', label: 'RSI', paneType: 'oscillator', defaultParams: { period: 14 } },
    { name: 'MACD', label: 'MACD', paneType: 'oscillator', defaultParams: { period: 12, period2: 26, period3: 9 } },
    { name: 'STOCH', label: 'Stochastic %K/%D', paneType: 'oscillator', defaultParams: {} },
    { name: 'STOCH_RSI', label: 'StochRSI', paneType: 'oscillator', defaultParams: {} },
    { name: 'WILLIAMS_R', label: 'Williams %R', paneType: 'oscillator', defaultParams: { period: 14 } },
    { name: 'CCI', label: 'CCI', paneType: 'oscillator', defaultParams: { period: 20 } },
    { name: 'ROC', label: 'ROC', paneType: 'oscillator', defaultParams: { period: 12 } },
    { name: 'MOM', label: 'Momentum', paneType: 'oscillator', defaultParams: { period: 10 } },
    { name: 'TRIX', label: 'TRIX', paneType: 'oscillator', defaultParams: { period: 15 } },
    { name: 'ULTOSC', label: 'Ultimate Oscillator', paneType: 'oscillator', defaultParams: {} },
    { name: 'PPO', label: 'PPO', paneType: 'oscillator', defaultParams: {} },
    { name: 'KDJ', label: 'KDJ', paneType: 'oscillator', defaultParams: {} },
    { name: 'CMO', label: 'CMO', paneType: 'oscillator', defaultParams: { period: 14 } },
    { name: 'DPO', label: 'DPO', paneType: 'oscillator', defaultParams: { period: 20 } },
  ],
  'Trend Strength': [
    { name: 'ADX', label: 'ADX/DI', paneType: 'oscillator', defaultParams: { period: 14 } },
    { name: 'AROON', label: 'Aroon', paneType: 'oscillator', defaultParams: { period: 25 } },
    { name: 'SAR', label: 'Parabolic SAR', paneType: 'overlay', defaultParams: {} },
    { name: 'SUPERTREND', label: 'SuperTrend', paneType: 'overlay', defaultParams: {} },
    { name: 'VORTEX', label: 'Vortex', paneType: 'oscillator', defaultParams: {} },
    { name: 'ICHIMOKU', label: 'Ichimoku Cloud', paneType: 'overlay', defaultParams: {} },
    { name: 'MASS_INDEX', label: 'Mass Index', paneType: 'oscillator', defaultParams: {} },
  ],
  'Volatility': [
    { name: 'BBANDS', label: 'Bollinger Bands', paneType: 'overlay', defaultParams: { period: 20 } },
    { name: 'KC', label: 'Keltner Channel', paneType: 'overlay', defaultParams: {} },
    { name: 'DC', label: 'Donchian Channel', paneType: 'overlay', defaultParams: {} },
    { name: 'ATR', label: 'ATR', paneType: 'oscillator', defaultParams: { period: 14 } },
    { name: 'HV', label: 'Historical Vol (C-C)', paneType: 'oscillator', defaultParams: {} },
    { name: 'HV_PARKINSON', label: 'Historical Vol (Parkinson)', paneType: 'oscillator', defaultParams: {} },
    { name: 'CHAIKIN_VOL', label: 'Chaikin Volatility', paneType: 'oscillator', defaultParams: {} },
    { name: 'ULCER', label: 'Ulcer Index', paneType: 'oscillator', defaultParams: {} },
    { name: 'GARCH', label: 'GARCH(1,1)', paneType: 'oscillator', defaultParams: {} },
  ],
  'Volume': [
    { name: 'OBV', label: 'OBV', paneType: 'oscillator', defaultParams: {} },
    { name: 'VWAP', label: 'VWAP', paneType: 'overlay', defaultParams: {} },
    { name: 'VWAP_BANDS', label: 'VWAP SD Bands', paneType: 'overlay', defaultParams: {} },
    { name: 'CMF', label: 'CMF', paneType: 'oscillator', defaultParams: {} },
    { name: 'MFI', label: 'MFI', paneType: 'oscillator', defaultParams: { period: 14 } },
    { name: 'VOL_PROFILE', label: 'Volume Profile', paneType: 'overlay', defaultParams: {} },
    { name: 'CVD', label: 'CVD', paneType: 'oscillator', defaultParams: {} },
    { name: 'VROC', label: 'VROC', paneType: 'oscillator', defaultParams: {} },
    { name: 'EOM', label: 'Ease of Movement', paneType: 'oscillator', defaultParams: {} },
    { name: 'NVI_PVI', label: 'NVI / PVI', paneType: 'oscillator', defaultParams: {} },
    { name: 'FORCE', label: 'Force Index', paneType: 'oscillator', defaultParams: {} },
    { name: 'AD', label: 'A/D Line', paneType: 'oscillator', defaultParams: {} },
  ],
  'Market Breadth': [
    { name: 'BREADTH_AD', label: 'A/D Line (Index) [n/a]', paneType: 'oscillator', defaultParams: {}, disabled: true },
    { name: 'MCCLELLAN', label: 'McClellan Osc [n/a]', paneType: 'oscillator', defaultParams: {}, disabled: true },
    { name: 'TRIN', label: 'TRIN [n/a]', paneType: 'oscillator', defaultParams: {}, disabled: true },
    { name: 'PCT_ABOVE_200', label: '% Above 200 SMA [n/a]', paneType: 'oscillator', defaultParams: {}, disabled: true },
    { name: 'PCT_ABOVE_50', label: '% Above 50 SMA [n/a]', paneType: 'oscillator', defaultParams: {}, disabled: true },
  ],
  'Pivot Points': [
    { name: 'PIVOT_STANDARD', label: 'Standard Pivots', paneType: 'overlay', defaultParams: {} },
    { name: 'PIVOT_WOODIE', label: "Woodie's Pivots", paneType: 'overlay', defaultParams: {} },
    { name: 'PIVOT_CAMARILLA', label: 'Camarilla Pivots', paneType: 'overlay', defaultParams: {} },
    { name: 'PIVOT_FIBONACCI', label: 'Fibonacci Pivots', paneType: 'overlay', defaultParams: {} },
    { name: 'PIVOT_DEMARK', label: 'DeMark Pivots', paneType: 'overlay', defaultParams: {} },
  ],
};

interface IndicatorPickerProps {
  isOpen: boolean;
  onClose: () => void;
  activeIndicators: ActiveIndicator[];
  onToggle: (indicatorDef: IndicatorDefinition) => void;
  onParamChange: (id: string, params: Record<string, number>) => void;
}

export function IndicatorPicker({
  isOpen,
  onClose,
  activeIndicators,
  onToggle,
}: IndicatorPickerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  // Track open/closed state per group (all start collapsed)
  const [openGroups, setOpenGroups] = useState<Record<string, boolean>>({});

  // Dismiss on Escape
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape') onClose();
    }
    if (isOpen) {
      document.addEventListener('keydown', handleKeyDown);
    }
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  // Dismiss on click outside
  useEffect(() => {
    function handleMouseDown(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        onClose();
      }
    }
    if (isOpen) {
      document.addEventListener('mousedown', handleMouseDown);
    }
    return () => document.removeEventListener('mousedown', handleMouseDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  function toggleGroup(group: string) {
    setOpenGroups((prev) => ({ ...prev, [group]: !prev[group] }));
  }

  function isActive(indicatorName: string): boolean {
    return activeIndicators.some((a) => a.name === indicatorName);
  }

  return (
    <div
      ref={containerRef}
      style={{
        position: 'absolute',
        zIndex: 50,
        width: 280,
        maxHeight: 400,
        overflowY: 'auto',
        background: TERMINAL.BG,
        border: `1px solid ${TERMINAL.BORDER}`,
        top: '100%',
        left: 0,
      }}
    >
      {Object.entries(INDICATOR_GROUPS).map(([group, indicators], groupIdx) => {
        const isGroupOpen = openGroups[group] ?? false;
        return (
          <div key={group}>
            {groupIdx > 0 && (
              <div style={{ height: 1, background: TERMINAL.BORDER }} />
            )}
            {/* Group heading — clickable to expand/collapse */}
            <button
              onClick={() => toggleGroup(group)}
              style={{
                display: 'flex',
                alignItems: 'center',
                width: '100%',
                padding: '4px 8px',
                background: 'transparent',
                border: 'none',
                cursor: 'pointer',
                textAlign: 'left',
              }}
            >
              <span
                style={{
                  fontSize: 12,
                  fontWeight: 700,
                  color: TERMINAL.AMBER,
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                  flex: 1,
                }}
              >
                {group}
              </span>
              <span style={{ color: TERMINAL.AMBER, fontSize: 10 }}>
                {isGroupOpen ? '[-]' : '[+]'}
              </span>
            </button>

            {/* Indicator rows — only shown when group is expanded */}
            {isGroupOpen &&
              indicators.map((def) => {
                const active = isActive(def.name);
                const isDisabled = def.disabled === true;
                return (
                  <button
                    key={def.name}
                    disabled={isDisabled}
                    onClick={() => !isDisabled && onToggle(def)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      width: '100%',
                      padding: '3px 8px',
                      background: 'transparent',
                      border: 'none',
                      cursor: isDisabled ? 'default' : 'pointer',
                      textAlign: 'left',
                    }}
                    onMouseEnter={(e) => {
                      if (!isDisabled) {
                        (e.currentTarget as HTMLElement).style.background = TERMINAL.BORDER;
                      }
                    }}
                    onMouseLeave={(e) => {
                      (e.currentTarget as HTMLElement).style.background = 'transparent';
                    }}
                  >
                    <span
                      style={{
                        fontFamily: 'monospace',
                        fontSize: 12,
                        color: isDisabled ? TERMINAL.DIM : active ? TERMINAL.AMBER : '#c0c0c0',
                        marginRight: 6,
                        minWidth: 16,
                      }}
                    >
                      {active ? '[✓]' : '[ ]'}
                    </span>
                    <span
                      style={{
                        fontSize: 12,
                        color: isDisabled ? TERMINAL.DIM : active ? TERMINAL.AMBER : '#c0c0c0',
                      }}
                    >
                      {def.label}
                    </span>
                  </button>
                );
              })}
          </div>
        );
      })}
    </div>
  );
}
