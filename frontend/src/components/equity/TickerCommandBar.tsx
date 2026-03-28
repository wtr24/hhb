/**
 * TickerCommandBar — terminal-style ticker input (D-03, D-04).
 *
 * Bloomberg-style command bar: `TICKER> ` prefix in amber, monospace font,
 * amber blinking cursor, auto-uppercase. On Enter, calls onSubmit and clears
 * the input. No history or autocomplete (D-04: plain input only).
 */
import { useEffect, useRef, useState } from 'react';

interface TickerCommandBarProps {
  onSubmit: (ticker: string) => void;
}

export function TickerCommandBar({ onSubmit }: TickerCommandBarProps) {
  const [value, setValue] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-focus on mount (D-03: terminal feel requires ready state)
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
    <div className="flex items-center border-b border-terminal-border px-2 py-0.5 bg-terminal-bg">
      {/* Terminal-style prefix — NOT part of the input (D-03) */}
      <span className="text-terminal-amber font-terminal text-xs font-bold select-none mr-1">
        TICKER&gt;
      </span>
      <input
        ref={inputRef}
        type="text"
        value={value}
        onChange={(e) => setValue(e.target.value.toUpperCase())}
        onKeyDown={handleKeyDown}
        className="flex-1 bg-transparent border-none outline-none text-terminal-amber font-terminal text-xs uppercase placeholder:text-terminal-dim"
        placeholder="TYPE TICKER AND PRESS ENTER"
        autoComplete="off"
        autoCorrect="off"
        autoCapitalize="characters"
        spellCheck={false}
        style={{ caretColor: '#ff9900' }}
      />
    </div>
  );
}

export default TickerCommandBar;
