import { useState, useEffect, useRef } from 'react';
import type { Quote } from '../types/equity';

const WS_URL = 'ws://localhost:8000/ws';
const RECONNECT_DELAY_MS = 3000;

export function useEquityWebSocket(ticker: string): Quote | null {
  const [quote, setQuote] = useState<Quote | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  useEffect(() => {
    if (!ticker) {
      setQuote(null);
      return;
    }

    let ws: WebSocket;

    function connect() {
      if (!mountedRef.current) return;

      ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.onopen = () => {
        ws.send(
          JSON.stringify({
            action: 'subscribe',
            channels: [`quotes:${ticker}`, 'fx:USDGBP'],
          })
        );
      };

      ws.onmessage = (evt: MessageEvent) => {
        try {
          const msg = JSON.parse(evt.data as string);
          if (msg.channel === `quotes:${ticker}`) {
            setQuote(msg as Quote);
          }
        } catch {
          // Ignore malformed messages
        }
      };

      ws.onclose = () => {
        if (!mountedRef.current) return;
        // Reconnect after delay
        reconnectTimerRef.current = setTimeout(() => {
          if (mountedRef.current) {
            connect();
          }
        }, RECONNECT_DELAY_MS);
      };

      ws.onerror = () => {
        // onclose will fire after onerror — reconnect handled there
      };
    }

    connect();

    return () => {
      // Cancel any pending reconnect
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current);
        reconnectTimerRef.current = null;
      }
      // Unsubscribe and close current connection
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(
          JSON.stringify({
            action: 'unsubscribe',
            channels: [`quotes:${ticker}`, 'fx:USDGBP'],
          })
        );
        wsRef.current.close();
      }
      wsRef.current = null;
      setQuote(null);
    };
  }, [ticker]);

  return quote;
}
