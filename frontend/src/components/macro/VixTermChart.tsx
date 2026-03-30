import React from 'react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import { TERMINAL } from '../../lib/theme'
import type { RiskData } from '../../hooks/useMacroData'

interface VixTermChartProps {
  data: RiskData | null
  loading: boolean
}

export function VixTermChart({ data, loading }: VixTermChartProps) {
  if (loading || !data) {
    return (
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          height: '100%',
          minHeight: 0,
        }}
      >
        <div
          style={{
            fontFamily: 'inherit',
            fontSize: '11px',
            fontWeight: 'bold',
            color: TERMINAL.AMBER,
            letterSpacing: '0.1em',
            padding: '4px 8px',
            borderBottom: `1px solid ${TERMINAL.BORDER}`,
            flexShrink: 0,
          }}
        >
          VIX TERM STRUCTURE
        </div>
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
      </div>
    )
  }

  const series = data.vix_term_structure
  const historyDepthOk = data.history_depth_ok

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', minHeight: 0 }}>
      {/* Header */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '4px 8px',
          borderBottom: `1px solid ${TERMINAL.BORDER}`,
          flexShrink: 0,
        }}
      >
        <span
          style={{
            fontFamily: 'inherit',
            fontSize: '11px',
            fontWeight: 'bold',
            color: TERMINAL.AMBER,
            letterSpacing: '0.1em',
          }}
        >
          VIX TERM STRUCTURE
        </span>
        {!historyDepthOk && (
          <span
            style={{
              fontFamily: 'inherit',
              fontSize: '10px',
              color: TERMINAL.DIM,
              letterSpacing: '0.05em',
            }}
          >
            ACCUMULATING HISTORY
          </span>
        )}
      </div>

      {/* Chart */}
      <div style={{ flex: 1, minHeight: 0 }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={series} margin={{ top: 8, right: 8, bottom: 8, left: 0 }}>
            <XAxis
              dataKey="date"
              tick={{ fill: TERMINAL.DIM, fontSize: 9, fontFamily: 'inherit' }}
              axisLine={{ stroke: TERMINAL.BORDER }}
              tickLine={false}
              tickFormatter={(v: string) => v.slice(0, 7)}
              interval="preserveStartEnd"
            />
            <YAxis
              tick={{ fill: TERMINAL.DIM, fontSize: 9, fontFamily: 'inherit' }}
              axisLine={{ stroke: TERMINAL.BORDER }}
              tickLine={false}
              tickFormatter={(v: number) => v.toFixed(0)}
              width={28}
              domain={[0, 'auto']}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: TERMINAL.BG,
                border: `1px solid ${TERMINAL.BORDER}`,
                fontFamily: 'inherit',
                fontSize: '10px',
                color: TERMINAL.AMBER,
              }}
            />
            {/* Spot VIX — amber, primary */}
            <Line
              type="monotone"
              dataKey="spot"
              stroke={TERMINAL.AMBER}
              strokeWidth={2}
              dot={false}
              name="VIX"
              connectNulls
            />
            {/* VIX3M — green */}
            <Line
              type="monotone"
              dataKey="vix3m"
              stroke={TERMINAL.GREEN}
              strokeWidth={1.5}
              dot={false}
              name="VIX3M"
              connectNulls
            />
            {/* VIX6M — dim dashed; only if historyDepthOk */}
            {historyDepthOk && (
              <Line
                type="monotone"
                dataKey="vix6m"
                stroke={TERMINAL.DIM}
                strokeWidth={1}
                strokeDasharray="4 3"
                dot={false}
                name="VIX6M"
                connectNulls
              />
            )}
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Colour legend */}
      <div
        style={{
          display: 'flex',
          gap: '12px',
          padding: '2px 8px',
          borderTop: `1px solid ${TERMINAL.BORDER}`,
          flexShrink: 0,
        }}
      >
        <span style={{ fontFamily: 'inherit', fontSize: '9px', color: TERMINAL.AMBER }}>
          ── VIX
        </span>
        <span style={{ fontFamily: 'inherit', fontSize: '9px', color: TERMINAL.GREEN }}>
          ── VIX3M
        </span>
        {historyDepthOk && (
          <span style={{ fontFamily: 'inherit', fontSize: '9px', color: TERMINAL.DIM }}>
            - - VIX6M
          </span>
        )}
      </div>
    </div>
  )
}
