import { useEffect, useRef, useState, useCallback } from 'react';
import {
  createChart,
  LineSeries,
  type IChartApi,
  type ISeriesApi,
} from 'lightweight-charts';
import { CandleChart } from './CandleChart';
import type { OverlayConfig } from './CandleChart';
import { CHART_OPTIONS } from '../../lib/chartConfig';
import { TERMINAL } from '../../lib/theme';
import {
  fetchIndicator,
  fetchCandlestickPatterns,
  fetchChartPatterns,
} from '../../lib/ta-api';
import type { CandlestickPatternResult, ChartPatternResult } from '../../lib/ta-api';
import type { OHLCVBar, ChartMarker } from '../../types/equity';
import type { ActiveIndicator } from './IndicatorPicker';
import { useDrawingTools } from './DrawingTools';

// Re-export for external consumers (ChartPanel imports this)
export type { OverlayConfig };

interface ExpandedChartProps {
  ticker: string;
  timeframe: string;
  activeIndicators: ActiveIndicator[];
  onIndicatorParamChange: (id: string, params: Record<string, number>) => void;
  onRemoveIndicator: (id: string) => void;
  chartData: OHLCVBar[];
  markers: ChartMarker[];
  onDrawingActiveChange?: (fibActive: boolean, ewActive: boolean) => void;
  fibTrigger?: number;
  ewTrigger?: number;
}

// Sub-pane chart instance tracker
interface SubPaneInstance {
  chart: IChartApi;
  series: ISeriesApi<'Line'>[];
}

// Height calculation: 75/25 split for <=1 oscillator, proportional for more
function computePaneHeights(
  totalHeight: number,
  oscillatorCount: number
): { mainPx: number; subPanePx: number } {
  if (oscillatorCount === 0) {
    return { mainPx: totalHeight, subPanePx: 0 };
  }
  const MIN_SUB_PANE = 60;
  const rawSubTotal = Math.round(totalHeight * 0.25);
  const rawSub = Math.max(MIN_SUB_PANE, Math.round(rawSubTotal / oscillatorCount));
  const subTotal = rawSub * oscillatorCount;
  const mainPx = Math.max(totalHeight - subTotal, 100);
  return { mainPx, subPanePx: rawSub };
}

// Map indicator API name to reference lines for oscillator panes
function getReferenceLines(indicatorName: string): number[] {
  switch (indicatorName) {
    case 'RSI':
    case 'STOCH_RSI':
      return [30, 50, 70];
    case 'STOCH':
      return [20, 50, 80];
    case 'WILLIAMS_R':
      return [-80, -50, -20];
    case 'MACD':
    case 'OBV':
    case 'CMF':
    case 'MOM':
    case 'ROC':
    case 'DPO':
    case 'CMO':
    case 'FORCE':
    case 'EOM':
    case 'CVD':
      return [0];
    case 'CCI':
      return [-100, 0, 100];
    case 'ADX':
      return [20, 40];
    case 'AROON':
      return [50];
    case 'MFI':
      return [20, 50, 80];
    default:
      return [];
  }
}

// Get a terminal colour for overlay series (cycle through a small palette)
const OVERLAY_COLORS = [
  '#00d084', // green
  '#4fc3f7', // blue
  '#ba68c8', // purple
  '#ffd54f', // yellow
  '#ff7043', // orange-red
  '#26c6da', // cyan
  '#66bb6a', // light green
  '#ef5350', // red
];

function getOverlayColor(index: number): string {
  return OVERLAY_COLORS[index % OVERLAY_COLORS.length];
}

function extractSeriesData(
  data: Record<string, unknown>,
  indicatorName: string
): Array<{ time: string; value: number }> {
  // Most indicators return {times: [...], values: [...]} or named series
  const raw = data as Record<string, unknown>;

  // Common single-series pattern
  if (Array.isArray(raw.times) && Array.isArray(raw.values)) {
    const times = raw.times as string[];
    const values = raw.values as number[];
    return times
      .map((t, i) => ({ time: t, value: values[i] }))
      .filter((p) => p.value != null && !isNaN(p.value));
  }

  // MACD returns {macd, signal, histogram}
  if (indicatorName === 'MACD' && Array.isArray(raw.times) && Array.isArray(raw.macd)) {
    const times = raw.times as string[];
    const values = raw.macd as number[];
    return times
      .map((t, i) => ({ time: t, value: values[i] }))
      .filter((p) => p.value != null && !isNaN(p.value));
  }

  // STOCH returns {k, d}
  if (indicatorName === 'STOCH' && Array.isArray(raw.times) && Array.isArray(raw.k)) {
    const times = raw.times as string[];
    const k = raw.k as number[];
    return times
      .map((t, i) => ({ time: t, value: k[i] }))
      .filter((p) => p.value != null && !isNaN(p.value));
  }

  // ADX returns {adx, plus_di, minus_di}
  if (indicatorName === 'ADX' && Array.isArray(raw.times) && Array.isArray(raw.adx)) {
    const times = raw.times as string[];
    const adx = raw.adx as number[];
    return times
      .map((t, i) => ({ time: t, value: adx[i] }))
      .filter((p) => p.value != null && !isNaN(p.value));
  }

  return [];
}

// Chart pattern shaded region overlay (TA-10)
// Positions a semi-transparent div proportionally by bar index within the chart container.
// The chart canvas has a right price scale (~50px) so we account for that.
const PRICE_SCALE_WIDTH = 50;

interface ChartPatternOverlayProps {
  pattern: ChartPatternResult;
  chartData: OHLCVBar[];
  containerHeight: number;
}

function ChartPatternOverlay({ pattern, chartData, containerHeight }: ChartPatternOverlayProps) {
  const n = chartData.length;
  if (n < 2) return null;
  const availableWidth = `calc(100% - ${PRICE_SCALE_WIDTH}px)`;
  const startPct = (pattern.start_bar / n) * 100;
  const endPct = (pattern.end_bar / n) * 100;
  const widthPct = endPct - startPct;
  if (widthPct <= 0) return null;

  // Breakout bar label position
  const breakoutPct = (pattern.breakout_bar / n) * 100;

  return (
    <>
      {/* Shaded region */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: `calc(${availableWidth} * ${startPct / 100})`,
          width: `calc(${availableWidth} * ${widthPct / 100})`,
          height: containerHeight,
          background: 'rgba(255, 153, 0, 0.08)',
          zIndex: 3,
          pointerEvents: 'none',
        }}
      />
      {/* Breakout label */}
      <div
        style={{
          position: 'absolute',
          top: 4,
          left: `calc(${availableWidth} * ${breakoutPct / 100})`,
          color: TERMINAL.AMBER,
          fontSize: 10,
          zIndex: 4,
          pointerEvents: 'none',
          whiteSpace: 'nowrap',
          transform: 'translateX(-50%)',
        }}
      >
        {pattern.label} [exp]
      </div>
    </>
  );
}

export function ExpandedChart({
  ticker,
  timeframe,
  activeIndicators,
  onIndicatorParamChange,
  onRemoveIndicator,
  chartData,
  markers,
  onDrawingActiveChange,
  fibTrigger,
  ewTrigger,
}: ExpandedChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [totalHeight, setTotalHeight] = useState(600);

  // Indicator data keyed by indicator id
  const [indicatorData, setIndicatorData] = useState<Record<string, Record<string, unknown>>>({});
  const [loadingIds, setLoadingIds] = useState<Set<string>>(new Set());

  // Overlay configs to pass to CandleChart
  const [overlays, setOverlays] = useState<OverlayConfig[]>([]);

  // Candlestick pattern badges (TA-09, TA-13)
  const [candlePatterns, setCandlePatterns] = useState<CandlestickPatternResult[]>([]);

  // Chart pattern shaded regions (TA-10)
  const [chartPatterns, setChartPatterns] = useState<ChartPatternResult[]>([]);

  // Drawing tools state machine
  const drawingTools = useDrawingTools(useCallback(() => {}, []));

  // Notify parent of drawing active state changes
  useEffect(() => {
    onDrawingActiveChange?.(drawingTools.fibActive, drawingTools.ewActive);
  }, [drawingTools.fibActive, drawingTools.ewActive, onDrawingActiveChange]);

  // Fire drawing tool toggles when parent increments trigger counters
  const prevFibTrigger = useRef(fibTrigger);
  useEffect(() => {
    if (fibTrigger !== prevFibTrigger.current) {
      prevFibTrigger.current = fibTrigger;
      drawingTools.toggleFib();
    }
  }, [fibTrigger, drawingTools]);

  const prevEwTrigger = useRef(ewTrigger);
  useEffect(() => {
    if (ewTrigger !== prevEwTrigger.current) {
      prevEwTrigger.current = ewTrigger;
      drawingTools.toggleEW();
    }
  }, [ewTrigger, drawingTools]);

  // Refs to oscillator chart instances, keyed by indicator id
  const subPaneRefs = useRef<Map<string, HTMLDivElement>>(new Map());
  const subPaneCharts = useRef<Map<string, SubPaneInstance>>(new Map());

  // Inline param editor state
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editParams, setEditParams] = useState<Record<string, number>>({});

  // Fetch candlestick patterns on ticker/timeframe change (TA-09, TA-13)
  useEffect(() => {
    let cancelled = false;
    if (!ticker) return;
    fetchCandlestickPatterns(ticker, timeframe)
      .then((res) => {
        if (!cancelled) setCandlePatterns(res.patterns);
      })
      .catch(() => {
        if (!cancelled) setCandlePatterns([]);
      });
    return () => { cancelled = true; };
  }, [ticker, timeframe]);

  // Fetch chart patterns on ticker/timeframe change (TA-10)
  useEffect(() => {
    let cancelled = false;
    if (!ticker) return;
    fetchChartPatterns(ticker, timeframe)
      .then((res) => {
        if (!cancelled) setChartPatterns(res.patterns);
      })
      .catch(() => {
        if (!cancelled) setChartPatterns([]);
      });
    return () => { cancelled = true; };
  }, [ticker, timeframe]);

  // Clear drawings when ticker or timeframe changes
  useEffect(() => {
    drawingTools.clearAllDrawings();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ticker, timeframe]);

  // Escape key cancels active drawing mode
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape' && (drawingTools.fibActive || drawingTools.ewActive)) {
        drawingTools.cancelDrawing();
      }
    }
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [drawingTools]);

  // Measure container height
  useEffect(() => {
    if (!containerRef.current) return;
    const obs = new ResizeObserver(() => {
      if (containerRef.current) {
        setTotalHeight(containerRef.current.clientHeight || 600);
      }
    });
    obs.observe(containerRef.current);
    setTotalHeight(containerRef.current.clientHeight || 600);
    return () => obs.disconnect();
  }, []);

  // Fetch indicator data with 200ms debounce
  const fetchTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const fetchAll = useCallback(() => {
    if (!ticker || activeIndicators.length === 0) {
      setIndicatorData({});
      setOverlays([]);
      return;
    }

    setLoadingIds(new Set(activeIndicators.map((i) => i.id)));

    activeIndicators.forEach((ind) => {
      fetchIndicator(ticker, {
        indicator: ind.name,
        timeframe,
        ...ind.params,
      })
        .then((res) => {
          setIndicatorData((prev) => ({ ...prev, [ind.id]: res.data }));
          setLoadingIds((prev) => {
            const next = new Set(prev);
            next.delete(ind.id);
            return next;
          });
        })
        .catch(() => {
          setLoadingIds((prev) => {
            const next = new Set(prev);
            next.delete(ind.id);
            return next;
          });
        });
    });
  }, [ticker, timeframe, activeIndicators]);

  useEffect(() => {
    if (fetchTimer.current) clearTimeout(fetchTimer.current);
    fetchTimer.current = setTimeout(fetchAll, 200);
    return () => {
      if (fetchTimer.current) clearTimeout(fetchTimer.current);
    };
  }, [fetchAll]);

  // Derive overlay configs whenever indicatorData changes
  useEffect(() => {
    const newOverlays: OverlayConfig[] = [];
    let colorIdx = 0;
    activeIndicators.forEach((ind) => {
      if (ind.paneType !== 'overlay') return;
      if (ind.name === 'VOL_PROFILE') return; // handled separately
      const data = indicatorData[ind.id];
      if (!data) return;
      const series = extractSeriesData(data, ind.name);
      if (series.length === 0) return;
      newOverlays.push({
        id: ind.id,
        seriesType: 'line',
        data: series,
        color: getOverlayColor(colorIdx++),
        lineWidth: 1,
        title: ind.label,
      });
    });
    setOverlays(newOverlays);
  }, [indicatorData, activeIndicators]);

  // Build / destroy oscillator sub-pane charts
  useEffect(() => {
    const oscillators = activeIndicators.filter((i) => i.paneType === 'oscillator');
    const activeIds = new Set(oscillators.map((i) => i.id));

    // Destroy charts for removed indicators
    subPaneCharts.current.forEach((instance, id) => {
      if (!activeIds.has(id)) {
        instance.chart.remove();
        subPaneCharts.current.delete(id);
      }
    });

    // Create or update charts for active oscillators
    oscillators.forEach((ind) => {
      const divEl = subPaneRefs.current.get(ind.id);
      if (!divEl) return;

      let instance = subPaneCharts.current.get(ind.id);
      if (!instance) {
        const chart = createChart(divEl, {
          ...CHART_OPTIONS,
          width: divEl.clientWidth,
          height: divEl.clientHeight,
          grid: {
            vertLines: { visible: false },
            horzLines: { color: TERMINAL.BORDER },
          },
          rightPriceScale: { borderColor: TERMINAL.BORDER },
          timeScale: { visible: false },
          leftPriceScale: { visible: false },
        });
        instance = { chart, series: [] };
        subPaneCharts.current.set(ind.id, instance);

        // Resize observer for this sub-pane
        const obs = new ResizeObserver(() => {
          if (divEl && chart) {
            chart.applyOptions({
              width: divEl.clientWidth,
              height: divEl.clientHeight,
            });
          }
        });
        obs.observe(divEl);
      }

      // Update series data
      const { chart, series: existingSeries } = instance;
      existingSeries.forEach((s) => chart.removeSeries(s));
      instance.series = [];

      const data = indicatorData[ind.id];
      if (data) {
        const pts = extractSeriesData(data, ind.name);
        if (pts.length > 0) {
          const mainSeries = chart.addSeries(LineSeries, {
            color: TERMINAL.AMBER,
            lineWidth: 1,
          });
          mainSeries.setData(pts as Parameters<typeof mainSeries.setData>[0]);
          instance.series.push(mainSeries);
        }
      }

      // Reference lines
      const refLines = getReferenceLines(ind.name);
      refLines.forEach((level) => {
        const refSeries = chart.addSeries(LineSeries, {
          color: TERMINAL.DIM,
          lineWidth: 1,
          lineStyle: 1, // dashed
        });
        // Use a wide time range for the reference line
        if (chartData.length > 0) {
          const pts = chartData.map((bar) => ({
            time: bar.time,
            value: level,
          }));
          refSeries.setData(pts as Parameters<typeof refSeries.setData>[0]);
          instance!.series.push(refSeries);
        }
      });
    });
  }, [activeIndicators, indicatorData, chartData]);

  // Cleanup all sub-pane charts on unmount
  useEffect(() => {
    return () => {
      subPaneCharts.current.forEach((instance) => instance.chart.remove());
      subPaneCharts.current.clear();
    };
  }, []);

  const oscillators = activeIndicators.filter((i) => i.paneType === 'oscillator');
  const { mainPx, subPanePx } = computePaneHeights(totalHeight, oscillators.length);

  function handleLabelClick(ind: ActiveIndicator) {
    if (editingId === ind.id) {
      setEditingId(null);
    } else {
      setEditingId(ind.id);
      setEditParams({ ...ind.params });
    }
  }

  function handleParamKeyDown(e: React.KeyboardEvent, id: string) {
    if (e.key === 'Enter') {
      onIndicatorParamChange(id, editParams);
      setEditingId(null);
    } else if (e.key === 'Escape') {
      setEditingId(null);
    }
  }

  // Volume Profile renderer (canvas-based histogram on right edge)
  function renderVolumeProfile(ind: ActiveIndicator) {
    const data = indicatorData[ind.id] as
      | { bins: number[]; volumes: number[]; poc: number }
      | undefined;
    if (!data || !data.bins || !data.volumes) return null;
    const maxVol = Math.max(...data.volumes);
    const barWidth = 60;
    const barHeight = Math.max(2, Math.floor(mainPx / data.bins.length));

    return (
      <div
        style={{
          position: 'absolute',
          right: 40,
          top: 0,
          width: barWidth,
          height: mainPx,
          zIndex: 5,
          pointerEvents: 'none',
          overflow: 'hidden',
        }}
      >
        {data.bins.map((bin, i) => {
          const vol = data.volumes[i];
          const pct = maxVol > 0 ? vol / maxVol : 0;
          const isPoc = Math.abs(bin - data.poc) < 0.001;
          return (
            <div
              key={i}
              style={{
                position: 'absolute',
                right: 0,
                top: i * barHeight,
                width: Math.max(2, Math.round(pct * barWidth)),
                height: barHeight,
                background: isPoc ? TERMINAL.AMBER : 'rgba(0,208,132,0.4)',
              }}
            />
          );
        })}
      </div>
    );
  }

  const volProfileInd = activeIndicators.find((i) => i.name === 'VOL_PROFILE');

  return (
    <div ref={containerRef} className="w-full h-full flex flex-col relative">
      {/* Main candle pane */}
      <div style={{ height: mainPx, position: 'relative', flexShrink: 0 }}>
        <CandleChart
          data={chartData}
          markers={markers}
          label=""
          expanded={true}
          overlays={overlays}
          onChartClick={drawingTools.handleChartClick}
          fibDrawings={drawingTools.fibDrawings}
          ewLabels={drawingTools.ewLabels}
        />
        {volProfileInd && renderVolumeProfile(volProfileInd)}

        {/* Candlestick pattern badges (TA-09, TA-13) — top-right stack */}
        {candlePatterns.length > 0 && (
          <div
            style={{
              position: 'absolute',
              top: 28,
              right: 4,
              zIndex: 20,
              display: 'flex',
              flexDirection: 'column',
              gap: 2,
              pointerEvents: 'none',
            }}
          >
            {candlePatterns.map((p) => (
              <div
                key={p.name}
                style={{
                  background: TERMINAL.BG,
                  color: p.win_rate !== null ? TERMINAL.AMBER : TERMINAL.DIM,
                  fontSize: 10,
                  padding: '2px 4px',
                  border: `1px solid ${TERMINAL.BORDER}`,
                  borderLeft: p.is_bullish
                    ? `2px solid ${TERMINAL.GREEN}`
                    : `2px solid ${TERMINAL.RED}`,
                  whiteSpace: 'nowrap',
                }}
              >
                {p.name}: {p.win_rate !== null
                  ? `${(p.win_rate * 100).toFixed(0)}% win`
                  : 'no data'} | n={p.n_occurrences}
                {p.p_value !== null ? ` | p=${p.p_value.toFixed(2)}` : ''}
              </div>
            ))}
          </div>
        )}

        {/* Chart pattern shaded regions (TA-10) */}
        {chartPatterns.map((cp) => (
          <ChartPatternOverlay
            key={`${cp.pattern}-${cp.start_bar}`}
            pattern={cp}
            chartData={chartData}
            containerHeight={mainPx}
          />
        ))}

        {/* EW validation badges — bottom-right when >= 4 labels placed */}
        {drawingTools.ewLabels.length >= 4 && drawingTools.ewValidations.length > 0 && (
          <div
            style={{
              position: 'absolute',
              bottom: 4,
              right: 4,
              zIndex: 20,
              background: TERMINAL.BG,
              border: `1px solid ${TERMINAL.BORDER}`,
              padding: '4px 6px',
              display: 'flex',
              flexDirection: 'column',
              gap: 2,
              pointerEvents: 'none',
            }}
          >
            {drawingTools.ewValidations.map((v, i) => (
              <div
                key={i}
                style={{
                  fontSize: 10,
                  color: v.valid ? TERMINAL.GREEN : TERMINAL.RED,
                  display: 'flex',
                  gap: 4,
                }}
              >
                <span>{v.valid ? '[✓]' : '[✗]'}</span>
                <span>{v.message}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Oscillator sub-panes */}
      {oscillators.map((ind) => {
        const isLoading = loadingIds.has(ind.id);
        const isEditing = editingId === ind.id;

        return (
          <div
            key={ind.id}
            style={{
              height: subPanePx,
              borderTop: `1px solid ${TERMINAL.BORDER}`,
              position: 'relative',
              flexShrink: 0,
            }}
          >
            {/* Sub-pane label */}
            <div
              style={{
                position: 'absolute',
                top: 2,
                left: 4,
                zIndex: 10,
                display: 'flex',
                flexDirection: 'column',
                gap: 2,
              }}
            >
              <button
                onClick={() => handleLabelClick(ind)}
                style={{
                  background: 'transparent',
                  border: 'none',
                  cursor: 'pointer',
                  padding: 0,
                  color: isLoading ? TERMINAL.DIM : TERMINAL.AMBER,
                  fontSize: 10,
                  textAlign: 'left',
                }}
              >
                {isLoading ? `${ind.label} ---` : ind.label}
              </button>

              {/* Inline param editor */}
              {isEditing && Object.keys(ind.params).length > 0 && (
                <div
                  style={{
                    display: 'flex',
                    gap: 4,
                    background: TERMINAL.BG,
                    border: `1px solid ${TERMINAL.BORDER}`,
                    padding: '2px 4px',
                  }}
                >
                  {Object.entries(editParams).map(([key, val]) => (
                    <label key={key} style={{ fontSize: 9, color: '#c0c0c0', display: 'flex', alignItems: 'center', gap: 2 }}>
                      {key}:
                      <input
                        type="number"
                        value={val}
                        onChange={(e) =>
                          setEditParams((prev) => ({
                            ...prev,
                            [key]: Number(e.target.value),
                          }))
                        }
                        onKeyDown={(e) => handleParamKeyDown(e, ind.id)}
                        style={{
                          width: 36,
                          background: TERMINAL.BG,
                          border: `1px solid ${TERMINAL.BORDER}`,
                          color: TERMINAL.AMBER,
                          fontSize: 9,
                          padding: '1px 2px',
                        }}
                      />
                    </label>
                  ))}
                </div>
              )}
            </div>

            {/* Remove button */}
            <button
              onClick={() => onRemoveIndicator(ind.id)}
              style={{
                position: 'absolute',
                top: 2,
                right: 4,
                zIndex: 10,
                background: 'transparent',
                border: 'none',
                cursor: 'pointer',
                color: TERMINAL.DIM,
                fontSize: 9,
              }}
              title="Remove indicator"
            >
              [x]
            </button>

            {/* Sub-pane chart container */}
            <div
              ref={(el) => {
                if (el) {
                  subPaneRefs.current.set(ind.id, el);
                } else {
                  subPaneRefs.current.delete(ind.id);
                }
              }}
              style={{ width: '100%', height: '100%' }}
            />
          </div>
        );
      })}
    </div>
  );
}
