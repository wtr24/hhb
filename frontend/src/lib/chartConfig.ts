import { ColorType } from 'lightweight-charts';
import { TERMINAL } from './theme';

export const CHART_OPTIONS = {
  layout: {
    background: { type: ColorType.Solid, color: TERMINAL.BG },
    textColor: TERMINAL.AMBER,
    fontSize: 10,
  },
  grid: {
    vertLines: { color: TERMINAL.BORDER },
    horzLines: { color: TERMINAL.BORDER },
  },
  rightPriceScale: { borderColor: TERMINAL.BORDER },
  timeScale: {
    borderColor: TERMINAL.BORDER,
    timeVisible: true,
    secondsVisible: false,
  },
  crosshair: { mode: 0 },
} as const;

export const CANDLE_STYLE = {
  upColor: TERMINAL.GREEN,
  downColor: TERMINAL.RED,
  borderVisible: false,
  wickUpColor: TERMINAL.GREEN,
  wickDownColor: TERMINAL.RED,
} as const;
