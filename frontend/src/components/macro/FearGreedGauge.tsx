import { TERMINAL } from '../../lib/theme'
import type { SentimentData, FearGreedComponent } from '../../hooks/useMacroData'

interface FearGreedGaugeProps {
  data: SentimentData | null
  loading: boolean
}

// Band definitions matching D-15 / UI-SPEC
const BANDS = [
  { label: 'EXTREME FEAR', min: 0,  max: 25,  color: TERMINAL.RED },
  { label: 'FEAR',         min: 25, max: 45,  color: 'var(--color-terminal-orange, #ff6600)' },
  { label: 'NEUTRAL',      min: 45, max: 55,  color: TERMINAL.AMBER },
  { label: 'GREED',        min: 55, max: 75,  color: TERMINAL.GREEN },
  { label: 'EXTREME GREED',min: 75, max: 100, color: 'var(--color-terminal-bright-green, #00ff66)' },
]

function getBand(score: number) {
  return BANDS.find((b) => score >= b.min && score <= b.max) ?? BANDS[2]
}

// Compute SVG arc path for a donut segment.
// startAngle and endAngle are in degrees, measured from 0° = left (3 o'clock on standard unit circle).
// For a semi-circle: leftmost = 180°, rightmost = 0°.
function arcPath(
  cx: number,
  cy: number,
  outerR: number,
  innerR: number,
  startDeg: number,
  endDeg: number
): string {
  function polar(cx: number, cy: number, r: number, deg: number) {
    const rad = (deg * Math.PI) / 180
    return { x: cx + r * Math.cos(rad), y: cy + r * Math.sin(rad) }
  }

  const o1 = polar(cx, cy, outerR, startDeg)
  const o2 = polar(cx, cy, outerR, endDeg)
  const i1 = polar(cx, cy, innerR, endDeg)
  const i2 = polar(cx, cy, innerR, startDeg)
  const largeArc = Math.abs(endDeg - startDeg) > 180 ? 1 : 0

  return [
    `M ${o1.x.toFixed(2)} ${o1.y.toFixed(2)}`,
    `A ${outerR} ${outerR} 0 ${largeArc} 1 ${o2.x.toFixed(2)} ${o2.y.toFixed(2)}`,
    `L ${i1.x.toFixed(2)} ${i1.y.toFixed(2)}`,
    `A ${innerR} ${innerR} 0 ${largeArc} 0 ${i2.x.toFixed(2)} ${i2.y.toFixed(2)}`,
    'Z',
  ].join(' ')
}

function Gauge({ score }: { score: number }) {
  const cx = 100
  const cy = 100
  const outerR = 90
  const innerR = 60

  // Semi-circle spans from 180° (left) to 0° (right) going clockwise.
  // We go counter-clockwise in SVG coordinates (y-axis flipped).
  // Split 180° into 5 equal 36° segments, starting from 180° (left).
  const segmentDeg = 36

  // Needle angle: score=0 → 180° (left), score=100 → 0° (right)
  // In SVG: rotate from center, needleAngle = 180 - (score/100)*180
  // But we need to express this as a CSS transform rotate from the center
  const needleAngleDeg = 180 - (score / 100) * 180 // degrees from right (0°)
  const needleRad = (needleAngleDeg * Math.PI) / 180
  const needleLength = outerR - 5
  const nx = cx + needleLength * Math.cos(needleRad)
  const ny = cy - needleLength * Math.sin(needleRad) // SVG y-axis flips sign

  const band = getBand(score)

  // Each segment spans 36°, leftmost segment = EXTREME FEAR (180°–144°), etc.
  const segments = BANDS.map((b, i) => {
    const startDeg = 180 - i * segmentDeg       // e.g. 180, 144, 108, 72, 36
    const endDeg   = 180 - (i + 1) * segmentDeg // e.g. 144, 108, 72,  36,  0
    // arcPath uses standard math angles (counter-clockwise from right)
    const isActive = b.label === band.label
    return { b, startDeg, endDeg, isActive }
  })

  return (
    <svg viewBox="0 0 200 110" width="100%" height="auto" style={{ maxHeight: '120px' }}>
      {/* Arc segments */}
      {segments.map(({ b, startDeg, endDeg, isActive }) => (
        <path
          key={b.label}
          d={arcPath(cx, cy, outerR, innerR, endDeg, startDeg)}
          fill={b.color}
          opacity={isActive ? 1.0 : 0.35}
        />
      ))}

      {/* Needle */}
      <line
        x1={cx}
        y1={cy}
        x2={nx.toFixed(2)}
        y2={ny.toFixed(2)}
        stroke={TERMINAL.AMBER}
        strokeWidth={2}
        strokeLinecap="round"
      />
      {/* Needle pivot dot */}
      <circle cx={cx} cy={cy} r={4} fill={TERMINAL.AMBER} />

      {/* Score number */}
      <text
        x={cx}
        y={82}
        textAnchor="middle"
        dominantBaseline="middle"
        fontFamily="'Courier New', monospace"
        fontSize={24}
        fontWeight="bold"
        fill={TERMINAL.AMBER}
      >
        {Math.round(score)}
      </text>

      {/* Band label */}
      <text
        x={cx}
        y={106}
        textAnchor="middle"
        dominantBaseline="middle"
        fontFamily="'Courier New', monospace"
        fontSize={9}
        fontWeight="bold"
        fill={band.color}
        letterSpacing="1"
      >
        {band.label}
      </text>
    </svg>
  )
}

function ComponentTable({ components }: { components: FearGreedComponent[] }) {
  return (
    <div style={{ overflow: 'auto', flex: 1 }}>
      <table
        style={{
          width: '100%',
          borderCollapse: 'collapse',
          fontFamily: 'inherit',
          fontSize: '10px',
          color: TERMINAL.AMBER,
        }}
      >
        <thead>
          <tr>
            {['COMPONENT', 'SCORE', 'SOURCE'].map((h) => (
              <th
                key={h}
                style={{
                  textAlign: 'left',
                  padding: '2px 4px',
                  borderBottom: `1px solid ${TERMINAL.BORDER}`,
                  color: TERMINAL.DIM,
                  fontWeight: 'bold',
                  letterSpacing: '0.05em',
                }}
              >
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {components.map((c, i) => (
            <tr key={i}>
              <td style={{ padding: '2px 4px', color: TERMINAL.AMBER }}>{c.name}</td>
              <td
                style={{
                  padding: '2px 4px',
                  color: getBand(c.score).color,
                  fontWeight: 'bold',
                }}
              >
                {Math.round(c.score)}
              </td>
              <td style={{ padding: '2px 4px', color: TERMINAL.DIM }}>{c.source}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export function FearGreedGauge({ data, loading }: FearGreedGaugeProps) {
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

  const { score, components } = data.fear_greed

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        overflow: 'hidden',
        padding: '8px',
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
          marginBottom: '4px',
          flexShrink: 0,
        }}
      >
        FEAR & GREED INDEX
      </div>

      {/* Gauge SVG */}
      <div style={{ flexShrink: 0 }}>
        <Gauge score={score} />
      </div>

      {/* Component breakdown table */}
      <ComponentTable components={components} />
    </div>
  )
}
