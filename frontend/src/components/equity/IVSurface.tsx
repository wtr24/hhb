/**
 * IVSurface — compact HTML canvas heatmap for implied volatility surface.
 *
 * Renders a grid: rows = strikes (y-axis), columns = expiry dates (x-axis).
 * Color scale: dark (#1a1a1a) -> amber (#ff9900) -> red (#ff4444) on normalized IV.
 * D-09: sits above the options table in a narrow strip.
 */
import { useEffect, useRef } from 'react';

export interface IVSurfaceData {
  strikes: number[];
  expiries: string[];
  iv_matrix: number[][];
}

interface IVSurfaceProps {
  surfaceData: IVSurfaceData | null;
}

/** Map normalized IV value t [0,1] to RGB color string. */
function ivToColor(t: number): string {
  const clamped = Math.max(0, Math.min(1, t));
  if (clamped < 0.5) {
    const f = clamped * 2; // 0->1 in first half
    const r = Math.round(26 + (255 - 26) * f);
    const g = Math.round(26 + (153 - 26) * f);
    const b = 26;
    return `rgb(${r},${g},${b})`;
  } else {
    const f = (clamped - 0.5) * 2; // 0->1 in second half
    const r = 255;
    const g = Math.round(153 - 153 * f);
    const b = 26;
    return `rgb(${r},${g},${b})`;
  }
}

/** Format expiry string "2026-04-25" -> "Apr 25" */
function fmtExpiry(exp: string): string {
  try {
    const d = new Date(exp + 'T00:00:00Z');
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', timeZone: 'UTC' });
  } catch {
    return exp.slice(5); // fallback: "04-25"
  }
}

export default function IVSurface({ surfaceData }: IVSurfaceProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx || !surfaceData) {
      // Clear canvas if no data
      ctx?.clearRect(0, 0, canvas.width, canvas.height);
      return;
    }

    const { strikes, expiries, iv_matrix } = surfaceData;
    if (!strikes.length || !expiries.length || !iv_matrix.length) return;

    // Compute min/max IV for normalization
    let minIV = Infinity;
    let maxIV = -Infinity;
    for (const row of iv_matrix) {
      for (const v of row) {
        if (v > 0) {
          if (v < minIV) minIV = v;
          if (v > maxIV) maxIV = v;
        }
      }
    }
    if (maxIV === minIV) maxIV = minIV + 0.01; // avoid divide-by-zero

    const LABEL_LEFT = 40; // px reserved for strike labels
    const LABEL_BOTTOM = 16; // px reserved for expiry labels
    const drawW = canvas.width - LABEL_LEFT;
    const drawH = canvas.height - LABEL_BOTTOM;

    const nCols = expiries.length;
    const nRows = strikes.length;
    const cellW = drawW / nCols;
    const cellH = drawH / nRows;

    // Background fill
    ctx.fillStyle = '#0a0a0a';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Draw heatmap cells
    for (let si = 0; si < nRows; si++) {
      for (let ei = 0; ei < nCols; ei++) {
        const iv = iv_matrix[si]?.[ei] ?? 0;
        const t = iv > 0 ? (iv - minIV) / (maxIV - minIV) : 0;
        ctx.fillStyle = ivToColor(t);
        ctx.fillRect(
          LABEL_LEFT + ei * cellW,
          si * cellH,
          cellW - 1,
          cellH - 1,
        );
      }
    }

    // Strike labels (left axis, every 3rd strike)
    ctx.fillStyle = '#404040';
    ctx.font = '9px monospace';
    ctx.textAlign = 'right';
    for (let si = 0; si < nRows; si += 3) {
      const y = si * cellH + cellH / 2 + 3;
      ctx.fillText(String(strikes[si]), LABEL_LEFT - 2, y);
    }

    // Expiry labels (bottom axis)
    ctx.fillStyle = '#404040';
    ctx.font = '9px monospace';
    ctx.textAlign = 'center';
    for (let ei = 0; ei < nCols; ei++) {
      const x = LABEL_LEFT + ei * cellW + cellW / 2;
      const y = drawH + 12;
      ctx.fillText(fmtExpiry(expiries[ei]), x, y);
    }
  }, [surfaceData]);

  if (!surfaceData || !surfaceData.strikes.length) {
    return (
      <div className="w-full h-[120px] bg-[#0a0a0a] border border-[#1a1a1a] flex items-center justify-center">
        <span className="text-xs text-[#404040] font-mono">IV SURFACE — NO DATA</span>
      </div>
    );
  }

  return (
    <canvas
      ref={canvasRef}
      width={600}
      height={120}
      className="w-full border border-[#1a1a1a]"
      aria-label="IV Surface Heatmap"
    />
  );
}
