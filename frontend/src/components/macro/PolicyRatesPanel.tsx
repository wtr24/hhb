import React from 'react'
import { TERMINAL } from '../../lib/theme'
import type { PolicyRatesPanel as PolicyRatesData } from '../../hooks/useMacroData'

function buildSparklinePath(values: number[], width: number, height: number): string {
  if (!values || values.length < 2) return ''
  const clean = values.filter((v) => v != null && isFinite(v))
  if (clean.length < 2) return ''
  const min = Math.min(...clean)
  const max = Math.max(...clean)
  const range = max - min || 1
  const topPad = 4
  const usableHeight = height - topPad * 2
  const step = width / (values.length - 1)
  const points = values.map((v, i) => {
    const x = i * step
    const y = topPad + usableHeight - ((v - min) / range) * usableHeight
    return `${x.toFixed(1)},${y.toFixed(1)}`
  })
  return `M ${points.join(' L ')}`
}

interface Props {
  data: PolicyRatesData | null
  loading: boolean
}

export function PolicyRatesPanel({ data, loading }: Props) {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        padding: '6px 8px',
        height: '100%',
        overflow: 'hidden',
        borderRight: `1px solid ${TERMINAL.BORDER}`,
        borderBottom: `1px solid ${TERMINAL.BORDER}`,
        backgroundColor: TERMINAL.BG,
        boxSizing: 'border-box',
      }}
    >
      <div
        style={{
          fontFamily: 'inherit',
          fontSize: '12px',
          fontWeight: 'bold',
          color: TERMINAL.AMBER,
          letterSpacing: '0.1em',
          marginBottom: '4px',
          flexShrink: 0,
        }}
      >
        POLICY RATES
      </div>

      {loading || !data ? (
        <div
          style={{
            flex: 1,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: TERMINAL.DIM,
            fontFamily: 'inherit',
            fontSize: '12px',
            letterSpacing: '0.1em',
          }}
        >
          LOADING...
        </div>
      ) : (
        <>
          {/* Combined sparkline using Fed as primary signal */}
          {data.history_fed && data.history_fed.length > 1 && (
            <div style={{ flexShrink: 0 }}>
              <svg
                viewBox="0 0 120 36"
                width="100%"
                height={36}
                preserveAspectRatio="none"
                style={{ display: 'block' }}
              >
                <path
                  d={buildSparklinePath(data.history_fed, 120, 36)}
                  fill="none"
                  stroke={TERMINAL.AMBER}
                  strokeWidth={1.5}
                />
                {data.history_boe && data.history_boe.length > 1 && (
                  <path
                    d={buildSparklinePath(data.history_boe, 120, 36)}
                    fill="none"
                    stroke={TERMINAL.GREEN}
                    strokeWidth={1}
                    strokeDasharray="3 2"
                  />
                )}
              </svg>
            </div>
          )}

          <div style={{ flexShrink: 0, marginTop: '4px' }}>
            {data.fed != null && (
              <div style={{ fontFamily: 'inherit', fontSize: '12px', fontWeight: 'bold', color: TERMINAL.AMBER }}>
                FED: {data.fed.toFixed(2)}%
              </div>
            )}
            {data.boe != null && (
              <div style={{ fontFamily: 'inherit', fontSize: '12px', color: TERMINAL.GREEN }}>
                BOE: {data.boe.toFixed(2)}%
              </div>
            )}
            {data.ecb != null && (
              <div style={{ fontFamily: 'inherit', fontSize: '12px', color: TERMINAL.GREEN }}>
                ECB: {data.ecb.toFixed(2)}%
              </div>
            )}
          </div>
        </>
      )}
    </div>
  )
}
