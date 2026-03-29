import { useEffect, useRef } from 'react';
import {
  createChart,
  CandlestickSeries,
  LineSeries,
  createSeriesMarkers,
  type IChartApi,
  type ISeriesApi,
  type SeriesMarkerPosition,
  type SeriesMarkerShape,
} from 'lightweight-charts';
import { CHART_OPTIONS, CANDLE_STYLE } from '../../lib/chartConfig';
import type { OHLCVBar, ChartMarker, TimeRange } from '../../types/equity';

// OverlayConfig defined here (canonical location); re-exported for ExpandedChart
export interface OverlayConfig {
  id: string;
  seriesType: 'line' | 'histogram' | 'band';
  data:
    | Array<{ time: string; value: number }>
    | Record<string, Array<{ time: string; value: number }>>;
  color: string;
  lineWidth?: number;
  title?: string;
}

interface CandleChartProps {
  data: OHLCVBar[];
  markers?: ChartMarker[];
  label: string;
  onExpand?: () => void;
  expanded?: boolean;
  overlays?: OverlayConfig[];
}

const TIME_RANGES: TimeRange[] = ['1D', '1W', '1M', '1Y', '5Y'];
const RANGE_DAYS: Record<TimeRange, number> = {
  '1D': 1,
  '1W': 7,
  '1M': 30,
  '1Y': 365,
  '5Y': 1825,
};

export function CandleChart({ data, markers = [], label, onExpand, expanded = false, overlays = [] }: CandleChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);
  const markersInstanceRef = useRef<ReturnType<typeof createSeriesMarkers> | null>(null);
  const overlaySeriesRef = useRef<ISeriesApi<'Line'>[]>([]);

  // Create chart once on mount
  useEffect(() => {
    if (!containerRef.current) return;

    const chart = createChart(containerRef.current, {
      ...CHART_OPTIONS,
      width: containerRef.current.clientWidth,
      height: containerRef.current.clientHeight,
    });
    chartRef.current = chart;
    seriesRef.current = chart.addSeries(CandlestickSeries, CANDLE_STYLE);

    // Resize observer
    const obs = new ResizeObserver(() => {
      if (containerRef.current && chartRef.current) {
        chartRef.current.applyOptions({
          width: containerRef.current.clientWidth,
          height: containerRef.current.clientHeight,
        });
      }
    });
    obs.observe(containerRef.current);

    return () => {
      obs.disconnect();
      overlaySeriesRef.current = [];
      chartRef.current?.remove();
      chartRef.current = null;
      seriesRef.current = null;
      markersInstanceRef.current = null;
    };
  }, []);

  // Update data without remounting chart
  useEffect(() => {
    if (!seriesRef.current || !data.length) return;
    seriesRef.current.setData(data as Parameters<typeof seriesRef.current.setData>[0]);
    chartRef.current?.timeScale().fitContent();
  }, [data]);

  // Update markers using v5 createSeriesMarkers API
  useEffect(() => {
    if (!seriesRef.current) return;
    // Remove previous markers instance
    if (markersInstanceRef.current) {
      markersInstanceRef.current.setMarkers([]);
      markersInstanceRef.current = null;
    }
    if (markers.length > 0) {
      const formattedMarkers = markers.map((m) => ({
        time: m.time,
        position: m.position as SeriesMarkerPosition,
        color: m.color,
        shape: m.shape as SeriesMarkerShape,
        text: m.text,
      }));
      markersInstanceRef.current = createSeriesMarkers(
        seriesRef.current,
        formattedMarkers as Parameters<typeof createSeriesMarkers>[1]
      );
    }
  }, [markers]);

  // Overlay series — re-render when overlays prop changes
  useEffect(() => {
    if (!chartRef.current) return;

    // Remove previous overlay series
    overlaySeriesRef.current.forEach((s) => {
      try { chartRef.current?.removeSeries(s); } catch { /* already removed */ }
    });
    overlaySeriesRef.current = [];

    // Add new overlay series
    overlays.forEach((overlay) => {
      if (!chartRef.current) return;
      if (overlay.seriesType === 'line') {
        const series = chartRef.current.addSeries(LineSeries, {
          color: overlay.color,
          lineWidth: overlay.lineWidth ?? 1,
          title: overlay.title ?? '',
        }, 0);
        const pts = Array.isArray(overlay.data) ? overlay.data : [];
        if (pts.length > 0) {
          series.setData(pts as Parameters<typeof series.setData>[0]);
        }
        overlaySeriesRef.current.push(series);
      }
    });
  }, [overlays]);

  function setTimeRange(range: TimeRange) {
    if (!chartRef.current) return;
    const now = Math.floor(Date.now() / 1000);
    const days = RANGE_DAYS[range];
    chartRef.current.timeScale().setVisibleRange({
      from: (now - days * 86400) as Parameters<ReturnType<IChartApi['timeScale']>['setVisibleRange']>[0]['from'],
      to: now as Parameters<ReturnType<IChartApi['timeScale']>['setVisibleRange']>[0]['to'],
    });
  }

  return (
    <div className="relative w-full h-full">
      {/* Label overlay */}
      <span className="absolute top-1 left-1 text-terminal-dim text-xs z-10 pointer-events-none">
        {label}
      </span>

      {/* Time range buttons — only shown in expanded mode */}
      {expanded && (
        <div className="absolute top-1 right-1 z-10 flex gap-1">
          {TIME_RANGES.map((r) => (
            <button
              key={r}
              onClick={(e) => {
                e.stopPropagation();
                setTimeRange(r);
              }}
              className="px-1 py-0.5 text-xs border border-terminal-border hover:bg-terminal-border text-terminal-amber"
            >
              {r}
            </button>
          ))}
        </div>
      )}

      {/* Chart container */}
      <div
        ref={containerRef}
        onClick={onExpand}
        className="w-full h-full cursor-pointer"
      />
    </div>
  );
}
