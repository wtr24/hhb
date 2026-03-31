import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Cell,
  ResponsiveContainer,
} from 'recharts'
import { TERMINAL } from '../../lib/theme'
import type { SentimentData } from '../../hooks/useMacroData'

interface SeasonalityChartProps {
  data: SentimentData | null
  loading: boolean
}

export function SeasonalityChart({ data, loading }: SeasonalityChartProps) {
  const ticker = data?.seasonality?.ticker ?? '^GSPC'
  const monthlyAvg = data?.seasonality?.monthly_avg ?? []

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        overflow: 'hidden',
        borderTop: `1px solid ${TERMINAL.BORDER}`,
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
          padding: '4px 8px',
          flexShrink: 0,
        }}
      >
        SEASONALITY — {ticker}
      </div>

      {/* Chart */}
      <div style={{ flex: 1, minHeight: 0 }}>
        {loading || !monthlyAvg.length ? (
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
            {loading ? 'LOADING...' : 'NO DATA'}
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={monthlyAvg}
              margin={{ top: 4, right: 8, bottom: 4, left: 0 }}
            >
              <XAxis
                dataKey="month"
                tick={{ fill: TERMINAL.DIM, fontSize: 9, fontFamily: 'inherit' }}
                axisLine={{ stroke: TERMINAL.BORDER }}
                tickLine={false}
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
                formatter={(value: number | undefined) => [`${value?.toFixed(2) ?? ''}%`, 'Avg Return']}
              />
              <Bar dataKey="avg_return" isAnimationActive={false}>
                {monthlyAvg.map((entry, index) => (
                  <Cell
                    key={index}
                    fill={entry.avg_return >= 0 ? TERMINAL.GREEN : TERMINAL.RED}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  )
}
