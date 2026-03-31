import {
  ComposedChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceLine,
  ReferenceArea,
  ResponsiveContainer,
} from 'recharts'
import { TERMINAL } from '../../lib/theme'
import type { CurvesData } from '../../hooks/useMacroData'

interface SpreadPanelProps {
  data: CurvesData | null
  loading: boolean
}

// Find contiguous negative-value zones for recession overlay
function findNegativeZones(series: { date: string; value: number }[]) {
  const zones: { start: string; end: string }[] = []
  let start: string | null = null
  for (const point of series) {
    if (point.value < 0 && start === null) {
      start = point.date
    } else if (point.value >= 0 && start !== null) {
      zones.push({ start, end: point.date })
      start = null
    }
  }
  if (start !== null && series.length > 0) {
    zones.push({ start, end: series[series.length - 1].date })
  }
  return zones
}

function SpreadChart({
  series,
  color,
  label,
}: {
  series: { date: string; value: number }[]
  color: string
  label: string
}) {
  const negZones = findNegativeZones(series)

  return (
    <div style={{ height: '100%', minHeight: 0 }}>
      <div
        style={{
          fontFamily: 'inherit',
          fontSize: '11px',
          fontWeight: 'bold',
          color: TERMINAL.AMBER,
          letterSpacing: '0.1em',
          padding: '2px 4px',
        }}
      >
        {label}
      </div>
      <ResponsiveContainer width="100%" height="85%">
        <ComposedChart data={series} margin={{ top: 2, right: 4, bottom: 2, left: 0 }}>
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
            tickFormatter={(v: number) => `${v.toFixed(1)}`}
            width={32}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: TERMINAL.BG,
              border: `1px solid ${TERMINAL.BORDER}`,
              fontFamily: 'inherit',
              fontSize: '10px',
              color: TERMINAL.AMBER,
            }}
            formatter={(value: number | undefined) => [`${value?.toFixed(2) ?? ''}%`]}
          />
          <ReferenceLine y={0} stroke={TERMINAL.DIM} strokeDasharray="2 2" />
          {negZones.map((zone, i) => (
            <ReferenceArea
              key={i}
              x1={zone.start}
              x2={zone.end}
              fill="rgba(255, 68, 68, 0.15)"
              label={{ value: 'REC', fill: TERMINAL.RED, fontSize: 8, fontFamily: 'inherit' }}
            />
          ))}
          <Line
            type="monotone"
            dataKey="value"
            stroke={color}
            strokeWidth={1.5}
            dot={false}
            connectNulls
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  )
}

export function SpreadPanel({ data, loading }: SpreadPanelProps) {
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

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', minHeight: 0 }}>
      <div style={{ flex: 1, minHeight: 0 }}>
        <SpreadChart
          series={data.spreads_2s10s}
          color={TERMINAL.AMBER}
          label="2s10s SPREAD"
        />
      </div>
      <div
        style={{ height: '1px', backgroundColor: TERMINAL.BORDER, flexShrink: 0 }}
      />
      <div style={{ flex: 1, minHeight: 0 }}>
        <SpreadChart
          series={data.spreads_5s30s}
          color={TERMINAL.GREEN}
          label="5s30s SPREAD"
        />
      </div>
    </div>
  )
}
