/**
 * QuoteBar — live quote strip (D-01 top strip, EQUITY-01, D-02, D-12).
 *
 * Full-width single row displaying:
 *   AAPL  189.50  +0.65%  O:187.20 H:190.10 L:186.80  Vol:42.8M  [STALE] [GBP]
 *
 * - Ticker name: amber bold
 * - Price + change %: green if positive, red if negative
 * - O/H/L: dim
 * - Volume: K/M/B formatted
 * - Stale badge (D-02): amber STALE border badge when quote.stale === true
 * - GBP mode (D-12): multiplies all price fields by gbpRate when gbpMode active
 */
import type { Quote } from '../../types/equity';
import { GBPToggle } from './GBPToggle';

interface QuoteBarProps {
  quote: Quote | null;
  gbpMode: boolean;
  gbpRate: number | null;
  onGbpToggle: () => void;
}

function formatVolume(vol: number | null): string {
  if (vol === null || vol === undefined) return '--';
  if (vol >= 1_000_000_000) return `${(vol / 1_000_000_000).toFixed(1)}B`;
  if (vol >= 1_000_000) return `${(vol / 1_000_000).toFixed(1)}M`;
  if (vol >= 1_000) return `${(vol / 1_000).toFixed(1)}K`;
  return vol.toLocaleString();
}

function convertPrice(price: number | null, gbpMode: boolean, gbpRate: number | null): number | null {
  if (price === null || price === undefined) return null;
  if (gbpMode && gbpRate !== null) return price * gbpRate;
  return price;
}

function fmtPrice(price: number | null): string {
  if (price === null) return '--';
  return price.toFixed(2);
}

export function QuoteBar({ quote, gbpMode, gbpRate, onGbpToggle }: QuoteBarProps) {
  const currency = gbpMode && gbpRate !== null ? 'GBP' : 'USD';

  const price = convertPrice(quote?.price ?? null, gbpMode, gbpRate);
  const open = convertPrice(quote?.open ?? null, gbpMode, gbpRate);
  const high = convertPrice(quote?.high ?? null, gbpMode, gbpRate);
  const low = convertPrice(quote?.low ?? null, gbpMode, gbpRate);

  const changePct = quote?.change_pct ?? null;
  const isPositive = changePct !== null && changePct >= 0;
  const isNegative = changePct !== null && changePct < 0;

  const priceColor = isPositive
    ? 'text-terminal-green'
    : isNegative
    ? 'text-terminal-red'
    : 'text-terminal-amber';

  const changeStr = changePct !== null
    ? `${isPositive ? '+' : ''}${changePct.toFixed(2)}%`
    : '--';

  return (
    <div className="flex items-center gap-3 border-b border-terminal-border py-0.5 px-2 bg-terminal-bg text-xs font-terminal overflow-x-auto shrink-0">
      {/* Ticker */}
      <span className="text-terminal-amber font-bold tracking-wider min-w-fit">
        {quote?.ticker ?? '--'}
      </span>

      {/* Currency label */}
      {gbpMode && gbpRate !== null && (
        <span className="text-terminal-dim min-w-fit">{currency}</span>
      )}

      {/* Price */}
      <span className={`font-bold min-w-fit ${priceColor}`}>
        {fmtPrice(price)}
      </span>

      {/* Change % */}
      <span className={`min-w-fit ${priceColor}`}>
        {changeStr}
      </span>

      {/* Separator */}
      <span className="text-terminal-border">|</span>

      {/* OHLV */}
      <span className="text-terminal-dim min-w-fit">
        O:<span className="text-terminal-amber">{fmtPrice(open)}</span>
      </span>
      <span className="text-terminal-dim min-w-fit">
        H:<span className="text-terminal-green">{fmtPrice(high)}</span>
      </span>
      <span className="text-terminal-dim min-w-fit">
        L:<span className="text-terminal-red">{fmtPrice(low)}</span>
      </span>

      {/* Separator */}
      <span className="text-terminal-border">|</span>

      {/* Volume */}
      <span className="text-terminal-dim min-w-fit">
        Vol:<span className="text-terminal-amber">{formatVolume(quote?.volume ?? null)}</span>
      </span>

      {/* Stale badge (D-02) */}
      {quote?.stale && (
        <span className="text-terminal-amber text-xs border border-terminal-amber px-1 min-w-fit">
          STALE
        </span>
      )}

      {/* Spacer */}
      <div className="flex-1" />

      {/* GBP toggle (D-12) */}
      <GBPToggle active={gbpMode} onToggle={onGbpToggle} />
    </div>
  );
}

export default QuoteBar;
