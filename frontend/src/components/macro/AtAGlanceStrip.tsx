import React, { useState, useEffect, useRef } from 'react'
import { TERMINAL } from '../../lib/theme'

interface TickerQuote {
  ticker: string
  label: string
  price: number | null
  changePct: number | null
  stale: boolean
  lastUpdated: number  // epoch ms
}

const TICKERS = [
  { ticker: 'DX-Y.NYB', label: 'DXY' },
  { ticker: '^GSPC',    label: 'SPX' },
  { ticker: '^FTSE',    label: 'FTSE' },
]

const STALE_THRESHOLD_MS = 30_000

export function AtAGlanceStrip() {
  const [quotes, setQuotes] = useState<Record<string, TickerQuote>>(
    Object.fromEntries(
      TICKERS.map(({ ticker, label }) => [
        ticker,
        { ticker, label, price: null, changePct: null, stale: false, lastUpdated: 0 },
      ])
    )
  )

  const wsRef = useRef<WebSocket | null>(null)
  const staleTimerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    const ws = new WebSocket(`ws://${window.location.host}/ws`)
    wsRef.current = ws

    ws.onopen = () => {
      TICKERS.forEach(({ ticker }) => {
        ws.send(JSON.stringify({ action: 'subscribe', channel: `quotes:${ticker}` }))
      })
    }

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data)
        const tickerKey = TICKERS.find((t) => `quotes:${t.ticker}` === msg.channel)?.ticker
        if (!tickerKey) return
        setQuotes((prev) => ({
          ...prev,
          [tickerKey]: {
            ...prev[tickerKey],
            price: msg.price ?? prev[tickerKey].price,
            changePct: msg.change_pct ?? prev[tickerKey].changePct,
            stale: msg.stale ?? false,
            lastUpdated: Date.now(),
          },
        }))
      } catch {
        // ignore malformed messages
      }
    }

    ws.onerror = () => {
      setQuotes((prev) => {
        const next = { ...prev }
        Object.keys(next).forEach((k) => { next[k] = { ...next[k], stale: true } })
        return next
      })
    }

    // Stale check every 5s
    staleTimerRef.current = setInterval(() => {
      const now = Date.now()
      setQuotes((prev) => {
        const next = { ...prev }
        let changed = false
        Object.keys(next).forEach((k) => {
          const isStale = next[k].lastUpdated > 0 && now - next[k].lastUpdated > STALE_THRESHOLD_MS
          if (isStale !== next[k].stale) {
            next[k] = { ...next[k], stale: isStale }
            changed = true
          }
        })
        return changed ? next : prev
      })
    }, 5_000)

    return () => {
      ws.close()
      if (staleTimerRef.current) clearInterval(staleTimerRef.current)
    }
  }, [])

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        padding: '8px',
        overflow: 'hidden',
      }}
    >
      <div
        style={{
          fontFamily: 'inherit',
          fontSize: '11px',
          fontWeight: 'bold',
          color: TERMINAL.AMBER,
          letterSpacing: '0.1em',
          marginBottom: '6px',
          flexShrink: 0,
        }}
      >
        MARKET SNAPSHOT
      </div>

      {TICKERS.map(({ ticker, label }) => {
        const q = quotes[ticker]
        const priceColor = TERMINAL.AMBER
        const deltaColor =
          q.changePct == null
            ? TERMINAL.DIM
            : q.changePct > 0
            ? TERMINAL.GREEN
            : q.changePct < 0
            ? TERMINAL.RED
            : TERMINAL.DIM

        return (
          <div
            key={ticker}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '3px 0',
              borderBottom: `1px solid ${TERMINAL.BORDER}`,
              fontFamily: 'inherit',
              fontSize: '12px',
            }}
          >
            <span
              style={{
                color: TERMINAL.DIM,
                width: '44px',
                flexShrink: 0,
                letterSpacing: '0.05em',
              }}
            >
              {label}
            </span>
            <span style={{ color: priceColor, fontWeight: 'bold', flex: 1 }}>
              {q.price != null ? q.price.toLocaleString(undefined, { maximumFractionDigits: 2 }) : '—'}
            </span>
            <span style={{ color: deltaColor, width: '56px', textAlign: 'right', flexShrink: 0 }}>
              {q.changePct != null
                ? `${q.changePct >= 0 ? '+' : ''}${q.changePct.toFixed(2)}%`
                : '—'}
            </span>
            {q.stale && (
              <span
                style={{
                  color: TERMINAL.RED,
                  fontSize: '10px',
                  letterSpacing: '0.05em',
                  flexShrink: 0,
                }}
              >
                STALE
              </span>
            )}
          </div>
        )
      })}
    </div>
  )
}
