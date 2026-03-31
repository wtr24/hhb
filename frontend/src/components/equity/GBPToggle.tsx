import { TERMINAL } from '../../lib/theme';

interface GBPToggleProps {
  active: boolean;
  onToggle: () => void;
}

export function GBPToggle({ active, onToggle }: GBPToggleProps) {
  return (
    <button
      onClick={onToggle}
      title={active ? 'Switch to USD' : 'Switch to GBP'}
      style={{
        fontFamily: "'JetBrains Mono', monospace",
        fontSize: 9,
        fontWeight: 600,
        letterSpacing: '0.12em',
        padding: '2px 8px',
        border: active
          ? `1px solid ${TERMINAL.CYAN}`
          : `1px solid ${TERMINAL.BORDER_BRIGHT}`,
        borderRadius: 3,
        backgroundColor: active ? `${TERMINAL.CYAN}18` : 'transparent',
        color: active ? TERMINAL.CYAN : TERMINAL.MUTED,
        cursor: 'pointer',
        transition: 'all 0.15s',
      }}
    >
      GBP
    </button>
  );
}

export default GBPToggle;
