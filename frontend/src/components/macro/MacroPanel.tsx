import { TERMINAL } from '../../lib/theme'

interface SeriesData {
  current: number | null
  history: number[]
  mom?: number | null
  yoy?: number | null
}

interface MacroPanelProps {
  title: string
  usData: SeriesData | null
  ukData?: SeriesData | null
  euData?: { current: number | null } | null
  loading: boolean
  unit?: string  // e.g. '%' or '$'
}

// Build SVG path for a sparkline given an array of values and target dimensions.
// Maps values to [topPad, height-topPad] vertical range inside a fixed SVG height.
function buildSparklinePath(
  values: number[],
  width: number,
  height: number,
  topPad = 4
): string {
  if (!values || values.length < 2) return ''
  const clean = values.filter((v) => v != null && isFinite(v))
  if (clean.length < 2) return ''
  const min = Math.min(...clean)
  const max = Math.max(...clean)
  const range = max - min || 1
  const usableHeight = height - topPad * 2
  const step = width / (values.length - 1)

  const points = values.map((v, i) => {
    const x = i * step
    const y = topPad + usableHeight - ((v - min) / range) * usableHeight
    return `${x.toFixed(1)},${y.toFixed(1)}`
  })

  return `M ${points.join(' L ')}`
}

function Sparkline({
  history,
  color,
  width = 120,
  height = 48,
}: {
  history: number[]
  color: string
  width?: number
  height?: number
}) {
  const path = buildSparklinePath(history, width, height)
  if (!path) return null
  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      width="100%"
      height={height}
      preserveAspectRatio="none"
      style={{ display: 'block', overflow: 'visible' }}
    >
      <path d={path} fill="none" stroke={color} strokeWidth={1.5} />
    </svg>
  )
}

function DeltaBadge({ value, label }: { value: number | null | undefined; label: string }) {
  if (value == null) return null
  const color = value > 0 ? TERMINAL.GREEN : value < 0 ? TERMINAL.RED : TERMINAL.DIM
  const sign = value > 0 ? '+' : ''
  return (
    <span style={{ fontFamily: 'inherit', fontSize: '10px', color, marginRight: '8px' }}>
      {label} {sign}{value.toFixed(1)}%
    </span>
  )
}

export function MacroPanel({
  title,
  usData,
  ukData,
  euData,
  loading,
  unit = '%',
}: MacroPanelProps) {
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
      {/* Panel title */}
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
        {title}
      </div>

      {loading || !usData ? (
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
          {/* US sparkline */}
          <div style={{ flexShrink: 0 }}>
            <Sparkline history={usData.history} color={TERMINAL.AMBER} height={48} />
          </div>

          {/* UK sparkline (if available) */}
          {ukData?.history && ukData.history.length > 1 && (
            <div style={{ flexShrink: 0 }}>
              <Sparkline history={ukData.history} color={TERMINAL.GREEN} height={32} />
            </div>
          )}

          {/* Current values */}
          <div style={{ flexShrink: 0, marginTop: '2px' }}>
            {usData.current != null && (
              <div style={{ fontFamily: 'inherit', fontSize: '12px', fontWeight: 'bold', color: TERMINAL.AMBER }}>
                US: {usData.current.toFixed(1)}{unit}
              </div>
            )}
            {ukData?.current != null && (
              <div style={{ fontFamily: 'inherit', fontSize: '12px', color: TERMINAL.GREEN }}>
                UK: {ukData.current.toFixed(1)}{unit}
              </div>
            )}
            {euData?.current != null && (
              <div style={{ fontFamily: 'inherit', fontSize: '12px', color: TERMINAL.GREEN }}>
                EU: {euData.current.toFixed(1)}{unit}
              </div>
            )}
          </div>

          {/* Delta row */}
          <div style={{ flexShrink: 0, marginTop: '2px', display: 'flex', flexWrap: 'wrap' }}>
            <DeltaBadge value={usData.mom} label="MoM" />
            <DeltaBadge value={usData.yoy} label="YoY" />
          </div>
        </>
      )}
    </div>
  )
}
