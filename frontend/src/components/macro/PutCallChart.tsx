import React from 'react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceLine,
  ResponsiveContainer,
} from 'recharts'
import { TERMINAL } from '../../lib/theme'
import type { RiskData } from '../../hooks/useMacroData'

interface PutCallChartProps {
  data: RiskData | null
  loading: boolean
}

export function PutCallChart({ data, loading }: PutCallChartProps) {
  if (loading || !data || !data.put_call_ratio?.length) {
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
            padding: '2px 8px',
            borderTop: `1px solid ${TERMINAL.BORDER}`,
            flexShrink: 0,
          }}
        >
          PUT/CALL RATIO
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
          {loading ? 'LOADING...' : 'NO DATA'}
        </div>
      </div>
    )
  }

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        minHeight: 0,
        borderTop: `1px solid ${TERMINAL.BORDER}`,
      }}
    >
      <div
        style={{
          fontFamily: 'inherit',
          fontSize: '11px',
          fontWeight: 'bold',
          color: TERMINAL.AMBER,
          letterSpacing: '0.1em',
          padding: '2px 8px',
          flexShrink: 0,
        }}
      >
        PUT/CALL RATIO
      </div>
      <div style={{ flex: 1, minHeight: 0 }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data.put_call_ratio} margin={{ top: 4, right: 8, bottom: 4, left: 0 }}>
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
              tickFormatter={(v: number) => v.toFixed(2)}
              width={36}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: TERMINAL.BG,
                border: `1px solid ${TERMINAL.BORDER}`,
                fontFamily: 'inherit',
                fontSize: '10px',
                color: TERMINAL.AMBER,
              }}
              formatter={(value: number) => [value?.toFixed(2), 'P/C']}
            />
            {/* Neutral reference line at 0.7 — D-06 / UI-SPEC */}
            <ReferenceLine
              y={0.7}
              stroke={TERMINAL.DIM}
              strokeDasharray="3 3"
              label={{
                value: 'NEUTRAL 0.70',
                fill: TERMINAL.DIM,
                fontSize: 9,
                fontFamily: 'inherit',
                position: 'right',
              }}
            />
            <Line
              type="monotone"
              dataKey="value"
              stroke={TERMINAL.AMBER}
              strokeWidth={1.5}
              dot={false}
              connectNulls
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
