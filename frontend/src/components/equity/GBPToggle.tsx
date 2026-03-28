/**
 * GBPToggle — compact GBP/USD toggle button (D-12, EQUITY-11).
 *
 * When active: amber background with black text (highlighted).
 * When inactive: dim text with border.
 * Placed inside QuoteBar to allow GBP price conversion.
 */

interface GBPToggleProps {
  active: boolean;
  onToggle: () => void;
}

export function GBPToggle({ active, onToggle }: GBPToggleProps) {
  return (
    <button
      onClick={onToggle}
      className={`text-xs px-2 py-0.5 font-terminal font-bold transition-colors ${
        active
          ? 'bg-terminal-amber text-black'
          : 'text-terminal-dim border border-terminal-border hover:border-terminal-amber hover:text-terminal-amber'
      }`}
      title={active ? 'Switch to USD' : 'Switch to GBP'}
    >
      GBP
    </button>
  );
}

export default GBPToggle;
