import React from 'react'
import { TERMINAL } from '../../lib/theme'
import type { RiskData } from '../../hooks/useMacroData'

interface RegimeClassifierProps {
  data: RiskData | null
  loading: boolean
}

// D-20 regime badge colours (from UI-SPEC)
const REGIME_STYLES: Record<string, { bg: string; text: string }> = {
  'LOW VOL':   { bg: TERMINAL.GREEN,                     text: '#000000' },
  'NORMAL':    { bg: TERMINAL.AMBER,                     text: '#000000' },
  'ELEVATED':  { bg: 'var(--color-terminal-orange, #ff6600)', text: '#000000' },
  'CRISIS':    { bg: TERMINAL.RED,                       text: '#ffffff' },
}

function ordinalSuffix(n: number): string {
  const s = ['th', 'st', 'nd', 'rd']
  const v = n % 100
  return n + (s[(v - 20) % 10] || s[v] || s[0])
}

export function RegimeClassifier({ data, loading }: RegimeClassifierProps) {
  if (loading || !data) {
    return (
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          height: '100%',
          color: TERMINAL.DIM,
          fontFamily: 'inherit',
          fontSize: '12px',
          letterSpacing: '0.1em',
        }}
      >
        LOADING...
      </div>
    )
  }

  const regime = data.regime || 'NORMAL'
  const style = REGIME_STYLES[regime] || REGIME_STYLES['NORMAL']
  const pct1y = data.percentile_1y
  const pct5y = data.percentile_5y
  const contango = data.contango

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        padding: '8px',
        gap: '6px',
        height: '100%',
        overflow: 'hidden',
      }}
    >
      {/* Header */}
      <div
        style={{
          fontFamily: 'inherit',
          fontSize: '11px',
          fontWeight: 'bold',
          color: TERMINAL.AMBER,
          letterSpacing: '0.1em',
        }}
      >
        REGIME
      </div>

      {/* Large regime badge */}
      <div>
        <span
          style={{
            fontFamily: 'inherit',
            fontSize: '11px',
            fontWeight: 'bold',
            backgroundColor: style.bg,
            color: style.text,
            padding: '2px 10px',
            letterSpacing: '0.1em',
            display: 'inline-block',
          }}
        >
          {regime}
        </span>
      </div>

      {/* Percentile ranks */}
      {pct1y != null && (
        <div
          style={{
            fontFamily: 'inherit',
            fontSize: '11px',
            color: TERMINAL.DIM,
            letterSpacing: '0.05em',
          }}
        >
          1Y: {ordinalSuffix(Math.round(pct1y))} PCTILE
        </div>
      )}
      {pct5y != null && (
        <div
          style={{
            fontFamily: 'inherit',
            fontSize: '11px',
            color: TERMINAL.DIM,
            letterSpacing: '0.05em',
          }}
        >
          5Y: {ordinalSuffix(Math.round(pct5y))} PCTILE
        </div>
      )}

      {/* Contango / Backwardation badge */}
      <div style={{ marginTop: 'auto' }}>
        <span
          style={{
            fontFamily: 'inherit',
            fontSize: '11px',
            fontWeight: 'bold',
            color: contango ? TERMINAL.AMBER : TERMINAL.RED,
            border: `1px solid ${contango ? TERMINAL.AMBER : TERMINAL.RED}`,
            padding: '2px 6px',
            letterSpacing: '0.1em',
          }}
        >
          {contango ? 'CONTANGO' : 'BACKWARDATION \u26a0'}
        </span>
      </div>
    </div>
  )
}
