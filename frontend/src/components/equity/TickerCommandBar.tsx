import { useEffect, useRef, useState } from 'react';
import { TERMINAL } from '../../lib/theme';

interface TickerCommandBarProps {
  onSubmit: (ticker: string) => void;
}

export function TickerCommandBar({ onSubmit }: TickerCommandBarProps) {
  const [value, setValue] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'Enter') {
      const trimmed = value.trim();
      if (trimmed) {
        onSubmit(trimmed);
        setValue('');
      }
    }
  }

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      padding: '0 12px',
      height: 34,
      borderBottom: `1px solid ${TERMINAL.BORDER}`,
      backgroundColor: TERMINAL.PANEL,
      flexShrink: 0,
      gap: 10,
    }}>
      {/* Label */}
      <span style={{
        fontSize: 9,
        fontWeight: 600,
        letterSpacing: '0.15em',
        color: TERMINAL.CYAN,
        textTransform: 'uppercase',
        userSelect: 'none',
        whiteSpace: 'nowrap',
      }}>
        TICKER
      </span>
      <span style={{
        color: TERMINAL.BORDER_BRIGHT,
        fontSize: 12,
        lineHeight: 1,
      }}>›</span>
      <input
        ref={inputRef}
        type="text"
        value={value}
        onChange={(e) => setValue(e.target.value.toUpperCase())}
        onKeyDown={handleKeyDown}
        placeholder="ENTER SYMBOL"
        autoComplete="off"
        autoCorrect="off"
        autoCapitalize="characters"
        spellCheck={false}
        style={{
          flex: 1,
          background: 'transparent',
          border: 'none',
          outline: 'none',
          color: TERMINAL.AMBER,
          fontFamily: "'JetBrains Mono', monospace",
          fontSize: 13,
          fontWeight: 600,
          letterSpacing: '0.1em',
          caretColor: TERMINAL.CYAN,
        }}
      />
      <span style={{
        fontSize: 9,
        color: TERMINAL.DIM,
        letterSpacing: '0.1em',
        whiteSpace: 'nowrap',
      }}>
        PRESS ENTER
      </span>
    </div>
  );
}

export default TickerCommandBar;
