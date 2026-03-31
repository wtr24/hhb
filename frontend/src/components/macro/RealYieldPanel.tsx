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
import type { CurvesData } from '../../hooks/useMacroData'

interface RealYieldPanelProps {
  data: CurvesData | null
  loading: boolean
}

export function RealYieldPanel({ data, loading }: RealYieldPanelProps) {
  if (loading || !data || !data.real_yield?.length) {
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
            padding: '2px 4px',
            flexShrink: 0,
          }}
        >
          REAL YIELD (10Y)
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
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', minHeight: 0 }}>
      <div
        style={{
          fontFamily: 'inherit',
          fontSize: '11px',
          fontWeight: 'bold',
          color: TERMINAL.AMBER,
          letterSpacing: '0.1em',
          padding: '2px 4px',
          flexShrink: 0,
        }}
      >
        REAL YIELD (10Y)
      </div>
      <div style={{ flex: 1, minHeight: 0 }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data.real_yield} margin={{ top: 2, right: 4, bottom: 2, left: 0 }}>
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
              tickFormatter={(v: number) => `${v.toFixed(1)}%`}
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
              formatter={(value: unknown) => [`${(value as number | undefined)?.toFixed(2) ?? ""}%`]}
            />
            <ReferenceLine y={0} stroke={TERMINAL.DIM} strokeDasharray="2 2" />
            <Line
              type="monotone"
              dataKey="value"
              stroke={TERMINAL.GREEN}
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
