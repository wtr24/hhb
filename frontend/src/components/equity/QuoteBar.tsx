import type { Quote } from '../../types/equity';
import { GBPToggle } from './GBPToggle';
import { TERMINAL } from '../../lib/theme';

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

const SEP = (
  <span style={{ color: TERMINAL.BORDER_BRIGHT, margin: '0 4px' }}>│</span>
);

const Label = ({ children }: { children: React.ReactNode }) => (
  <span style={{ fontSize: 9, color: TERMINAL.MUTED, letterSpacing: '0.1em', marginRight: 3 }}>
    {children}
  </span>
);

export function QuoteBar({ quote, gbpMode, gbpRate, onGbpToggle }: QuoteBarProps) {
  const price = convertPrice(quote?.price ?? null, gbpMode, gbpRate);
  const open = convertPrice(quote?.open ?? null, gbpMode, gbpRate);
  const high = convertPrice(quote?.high ?? null, gbpMode, gbpRate);
  const low = convertPrice(quote?.low ?? null, gbpMode, gbpRate);

  const changePct = quote?.change_pct ?? null;
  const isPositive = changePct !== null && changePct >= 0;
  const isNegative = changePct !== null && changePct < 0;

  const changeColor = isPositive ? TERMINAL.GREEN : isNegative ? TERMINAL.RED : TERMINAL.MUTED;
  const priceColor = isPositive ? TERMINAL.GREEN : isNegative ? TERMINAL.RED : TERMINAL.AMBER;

  const changeStr = changePct !== null
    ? `${isPositive ? '+' : ''}${changePct.toFixed(2)}%`
    : '--';

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      padding: '0 12px',
      height: 36,
      borderBottom: `1px solid ${TERMINAL.BORDER}`,
      backgroundColor: TERMINAL.ELEVATED,
      flexShrink: 0,
      gap: 2,
      overflow: 'hidden',
    }}>
      {/* Ticker */}
      <span style={{
        fontSize: 12,
        fontWeight: 700,
        letterSpacing: '0.12em',
        color: TERMINAL.AMBER,
        minWidth: 60,
        textShadow: `0 0 12px rgba(240,165,0,0.3)`,
      }}>
        {quote?.ticker ?? '------'}
      </span>

      {SEP}

      {/* Price — large and prominent */}
      <span style={{
        fontSize: 15,
        fontWeight: 700,
        color: priceColor,
        letterSpacing: '0.04em',
        minWidth: 70,
        textShadow: `0 0 10px ${priceColor}44`,
      }}>
        {fmtPrice(price)}
      </span>

      {/* Change % */}
      <span style={{
        fontSize: 11,
        fontWeight: 600,
        color: changeColor,
        minWidth: 60,
        padding: '1px 6px',
        backgroundColor: `${changeColor}14`,
        borderRadius: 2,
        letterSpacing: '0.04em',
      }}>
        {changeStr}
      </span>

      {gbpMode && gbpRate !== null && (
        <span style={{ fontSize: 9, color: TERMINAL.MUTED, letterSpacing: '0.1em' }}>GBP</span>
      )}

      {SEP}

      {/* OHLV */}
      <span style={{ whiteSpace: 'nowrap' }}>
        <Label>O</Label>
        <span style={{ color: TERMINAL.TEXT, fontSize: 11 }}>{fmtPrice(open)}</span>
      </span>
      <span style={{ whiteSpace: 'nowrap', marginLeft: 8 }}>
        <Label>H</Label>
        <span style={{ color: TERMINAL.GREEN, fontSize: 11 }}>{fmtPrice(high)}</span>
      </span>
      <span style={{ whiteSpace: 'nowrap', marginLeft: 8 }}>
        <Label>L</Label>
        <span style={{ color: TERMINAL.RED, fontSize: 11 }}>{fmtPrice(low)}</span>
      </span>

      {SEP}

      <span style={{ whiteSpace: 'nowrap' }}>
        <Label>VOL</Label>
        <span style={{ color: TERMINAL.TEXT, fontSize: 11 }}>{formatVolume(quote?.volume ?? null)}</span>
      </span>

      {/* Stale badge */}
      {quote?.stale && (
        <>
          {SEP}
          <span style={{
            fontSize: 9,
            color: TERMINAL.AMBER,
            border: `1px solid ${TERMINAL.AMBER}60`,
            padding: '1px 5px',
            borderRadius: 2,
            letterSpacing: '0.1em',
          }}>
            STALE
          </span>
        </>
      )}

      <div style={{ flex: 1 }} />
      <GBPToggle active={gbpMode} onToggle={onGbpToggle} />
    </div>
  );
}

export default QuoteBar;
