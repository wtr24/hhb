import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import { TERMINAL } from '../../lib/theme'
import type { CurvesData } from '../../hooks/useMacroData'

interface YieldCurveChartProps {
  data: CurvesData | null
  activeOverlays: Set<'+1M' | '+1Y'>
  loading: boolean
}

// Merge US and UK curve arrays into recharts data format.
// Each point: { tenor, us, uk, us_1m?, us_1y?, uk_1m?, uk_1y? }
function buildChartData(data: CurvesData, overlays: Set<'+1M' | '+1Y'>) {
  // Collect all tenor labels from US curve (canonical order)
  const tenors = data.us_curve.map((p) => p.tenor)
  const usMap = Object.fromEntries(data.us_curve.map((p) => [p.tenor, p.yield]))
  const ukMap = Object.fromEntries(data.uk_curve.map((p) => [p.tenor, p.yield]))
  const us1mMap = Object.fromEntries((data.us_curve_1m_ago ?? []).map((p) => [p.tenor, p.yield]))
  const us1yMap = Object.fromEntries((data.us_curve_1y_ago ?? []).map((p) => [p.tenor, p.yield]))
  const uk1mMap = Object.fromEntries((data.uk_curve_1m_ago ?? []).map((p) => [p.tenor, p.yield]))
  const uk1yMap = Object.fromEntries((data.uk_curve_1y_ago ?? []).map((p) => [p.tenor, p.yield]))

  return tenors.map((tenor) => ({
    tenor,
    us: usMap[tenor] ?? null,
    uk: ukMap[tenor] ?? null,
    us_1m: overlays.has('+1M') ? (us1mMap[tenor] ?? null) : undefined,
    us_1y: overlays.has('+1Y') ? (us1yMap[tenor] ?? null) : undefined,
    uk_1m: overlays.has('+1M') ? (uk1mMap[tenor] ?? null) : undefined,
    uk_1y: overlays.has('+1Y') ? (uk1yMap[tenor] ?? null) : undefined,
  }))
}

export function YieldCurveChart({ data, activeOverlays, loading }: YieldCurveChartProps) {
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

  const chartData = buildChartData(data, activeOverlays)

  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart data={chartData} margin={{ top: 8, right: 8, bottom: 8, left: 0 }}>
        <XAxis
          dataKey="tenor"
          tick={{ fill: TERMINAL.DIM, fontSize: 10, fontFamily: 'inherit' }}
          axisLine={{ stroke: TERMINAL.BORDER }}
          tickLine={false}
        />
        <YAxis
          tick={{ fill: TERMINAL.DIM, fontSize: 10, fontFamily: 'inherit' }}
          axisLine={{ stroke: TERMINAL.BORDER }}
          tickLine={false}
          tickFormatter={(v: number) => `${v.toFixed(1)}%`}
          width={40}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: TERMINAL.BG,
            border: `1px solid ${TERMINAL.BORDER}`,
            fontFamily: 'inherit',
            fontSize: '11px',
            color: TERMINAL.AMBER,
          }}
          formatter={(value: unknown) => [`${(value as number | undefined)?.toFixed(2) ?? ""}%`]}
        />

        {/* Primary US line (amber) */}
        <Line
          type="monotone"
          dataKey="us"
          stroke={TERMINAL.AMBER}
          strokeWidth={2}
          dot={false}
          name="US"
          connectNulls
        />
        {/* Primary UK gilt line (green) */}
        <Line
          type="monotone"
          dataKey="uk"
          stroke={TERMINAL.GREEN}
          strokeWidth={2}
          dot={false}
          name="UK"
          connectNulls
        />

        {/* Optional +1M overlays (dashed, dim) */}
        {activeOverlays.has('+1M') && (
          <Line
            type="monotone"
            dataKey="us_1m"
            stroke={TERMINAL.DIM}
            strokeWidth={1}
            strokeDasharray="4 4"
            dot={false}
            name="US +1M"
            opacity={0.5}
            connectNulls
          />
        )}
        {activeOverlays.has('+1M') && (
          <Line
            type="monotone"
            dataKey="uk_1m"
            stroke={TERMINAL.DIM}
            strokeWidth={1}
            strokeDasharray="4 4"
            dot={false}
            name="UK +1M"
            opacity={0.5}
            connectNulls
          />
        )}

        {/* Optional +1Y overlays (dashed, dim) */}
        {activeOverlays.has('+1Y') && (
          <Line
            type="monotone"
            dataKey="us_1y"
            stroke={TERMINAL.DIM}
            strokeWidth={1}
            strokeDasharray="4 4"
            dot={false}
            name="US +1Y"
            opacity={0.5}
            connectNulls
          />
        )}
        {activeOverlays.has('+1Y') && (
          <Line
            type="monotone"
            dataKey="uk_1y"
            stroke={TERMINAL.DIM}
            strokeWidth={1}
            strokeDasharray="4 4"
            dot={false}
            name="UK +1Y"
            opacity={0.5}
            connectNulls
          />
        )}
      </LineChart>
    </ResponsiveContainer>
  )
}
