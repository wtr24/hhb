import { TERMINAL } from '../../lib/theme'
import type { CurvesData } from '../../hooks/useMacroData'

interface CurveShapePanelProps {
  data: CurvesData | null
  loading: boolean
  activeOverlays: Set<'+1M' | '+1Y'>
  onOverlayChange: (overlay: '+1M' | '+1Y', active: boolean) => void
}

const SHAPE_COLORS: Record<string, string> = {
  NORMAL: TERMINAL.AMBER,
  FLAT: TERMINAL.DIM,
  'INVERTED ⚠': TERMINAL.RED,
  HUMPED: TERMINAL.AMBER,
}

export function CurveShapePanel({
  data,
  loading,
  activeOverlays,
  onOverlayChange,
}: CurveShapePanelProps) {
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

  const shape = data.curve_shape || 'UNKNOWN'
  const context = data.curve_shape_context || ''
  const badgeColor = SHAPE_COLORS[shape] || TERMINAL.AMBER

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        padding: '8px',
        height: '100%',
        gap: '6px',
      }}
    >
      {/* Shape badge */}
      <div>
        <span
          style={{
            fontFamily: 'inherit',
            fontSize: '11px',
            fontWeight: 'bold',
            color: shape.includes('INVERTED') ? '#000' : badgeColor,
            backgroundColor: shape.includes('INVERTED') ? TERMINAL.RED : 'transparent',
            border: `1px solid ${badgeColor}`,
            padding: '2px 8px',
            letterSpacing: '0.1em',
          }}
        >
          {shape}
        </span>
      </div>

      {/* Historical context */}
      {context && (
        <div
          style={{
            fontFamily: 'inherit',
            fontSize: '11px',
            color: TERMINAL.DIM,
          }}
        >
          {context}
        </div>
      )}

      {/* Overlay toggles */}
      <div
        style={{
          display: 'flex',
          gap: '4px',
          marginTop: 'auto',
        }}
      >
        {(['+1M', '+1Y'] as const).map((overlay) => {
          const isActive = activeOverlays.has(overlay)
          return (
            <button
              key={overlay}
              onClick={() => onOverlayChange(overlay, !isActive)}
              style={{
                fontFamily: 'inherit',
                fontSize: '10px',
                fontWeight: isActive ? 'bold' : 'normal',
                padding: '2px 6px',
                border: `1px solid ${isActive ? TERMINAL.AMBER : TERMINAL.DIM}`,
                backgroundColor: isActive ? TERMINAL.AMBER : 'transparent',
                color: isActive ? '#000' : TERMINAL.DIM,
                cursor: 'pointer',
                letterSpacing: '0.05em',
              }}
            >
              {overlay}
            </button>
          )
        })}
      </div>
    </div>
  )
}
