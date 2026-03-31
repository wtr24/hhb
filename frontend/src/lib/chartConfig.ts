import { ColorType, CrosshairMode } from 'lightweight-charts';
import { TERMINAL } from './theme';

export const CHART_OPTIONS = {
  layout: {
    background: { type: ColorType.Solid, color: TERMINAL.PANEL },
    textColor: TERMINAL.MUTED,
    fontSize: 10,
    fontFamily: "'JetBrains Mono', monospace",
  },
  grid: {
    vertLines: { color: 'rgba(26, 37, 53, 0.6)', style: 1 },
    horzLines: { color: 'rgba(26, 37, 53, 0.6)', style: 1 },
  },
  rightPriceScale: {
    borderColor: TERMINAL.BORDER,
    borderVisible: true,
    textColor: TERMINAL.MUTED,
  },
  timeScale: {
    borderColor: TERMINAL.BORDER,
    timeVisible: true,
    secondsVisible: false,
    borderVisible: true,
    tickMarkFormatter: undefined,
  },
  crosshair: {
    mode: CrosshairMode.Normal,
    vertLine: {
      color: 'rgba(0, 194, 224, 0.3)',
      width: 1,
      style: 1,
      labelBackgroundColor: TERMINAL.CYAN,
    },
    horzLine: {
      color: 'rgba(0, 194, 224, 0.3)',
      width: 1,
      style: 1,
      labelBackgroundColor: TERMINAL.CYAN,
    },
  },
  handleScroll: true,
  handleScale: true,
} as const;

export const CANDLE_STYLE = {
  upColor: TERMINAL.GREEN,
  downColor: TERMINAL.RED,
  borderVisible: false,
  wickUpColor: 'rgba(0, 217, 134, 0.7)',
  wickDownColor: 'rgba(240, 64, 96, 0.7)',
} as const;
