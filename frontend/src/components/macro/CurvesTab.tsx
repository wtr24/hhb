import { useState } from 'react'
import { TERMINAL } from '../../lib/theme'
import { YieldCurveChart } from './YieldCurveChart'
import { SpreadPanel } from './SpreadPanel'
import { CurveShapePanel } from './CurveShapePanel'
import { RealYieldPanel } from './RealYieldPanel'
import type { CurvesData } from '../../hooks/useMacroData'

interface CurvesTabProps {
  data: CurvesData | null
  loading: boolean
}

export function CurvesTab({ data, loading }: CurvesTabProps) {
  const [activeOverlays, setActiveOverlays] = useState<Set<'+1M' | '+1Y'>>(new Set())

  function handleOverlayChange(overlay: '+1M' | '+1Y', active: boolean) {
    setActiveOverlays((prev) => {
      const next = new Set(prev)
      if (active) next.add(overlay)
      else next.delete(overlay)
      return next
    })
  }

  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: '60% 40%',
        height: '100%',
        overflow: 'hidden',
        backgroundColor: TERMINAL.BG,
      }}
    >
      {/* Left 60%: yield curve chart + toggle row */}
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          borderRight: `1px solid ${TERMINAL.BORDER}`,
          minHeight: 0,
          overflow: 'hidden',
        }}
      >
        <div style={{ flex: 1, minHeight: 0, padding: '4px' }}>
          <YieldCurveChart
            data={data}
            activeOverlays={activeOverlays}
            loading={loading}
          />
        </div>
        {/* Colour legend row */}
        <div
          style={{
            display: 'flex',
            gap: '12px',
            padding: '4px 8px',
            borderTop: `1px solid ${TERMINAL.BORDER}`,
            flexShrink: 0,
          }}
        >
          <span
            style={{
              fontFamily: 'inherit',
              fontSize: '10px',
              color: TERMINAL.AMBER,
              letterSpacing: '0.05em',
            }}
          >
            ── US TREASURY
          </span>
          <span
            style={{
              fontFamily: 'inherit',
              fontSize: '10px',
              color: TERMINAL.GREEN,
              letterSpacing: '0.05em',
            }}
          >
            ── UK GILT
          </span>
          {activeOverlays.size > 0 && (
            <span
              style={{
                fontFamily: 'inherit',
                fontSize: '10px',
                color: TERMINAL.DIM,
                letterSpacing: '0.05em',
              }}
            >
              - - HIST OVERLAY
            </span>
          )}
        </div>
      </div>

      {/* Right 40%: three stacked panels */}
      <div
        style={{
          display: 'grid',
          gridTemplateRows: '50% 25% 25%',
          height: '100%',
          overflow: 'hidden',
          minHeight: 0,
        }}
      >
        {/* Spread panel (top 50%) */}
        <div
          style={{
            borderBottom: `1px solid ${TERMINAL.BORDER}`,
            overflow: 'hidden',
            minHeight: 0,
          }}
        >
          <SpreadPanel data={data} loading={loading} />
        </div>

        {/* Curve shape + overlay toggles (middle 25%) */}
        <div
          style={{
            borderBottom: `1px solid ${TERMINAL.BORDER}`,
            overflow: 'hidden',
            minHeight: 0,
          }}
        >
          <CurveShapePanel
            data={data}
            loading={loading}
            activeOverlays={activeOverlays}
            onOverlayChange={handleOverlayChange}
          />
        </div>

        {/* Real yield panel (bottom 25%) */}
        <div style={{ overflow: 'hidden', minHeight: 0 }}>
          <RealYieldPanel data={data} loading={loading} />
        </div>
      </div>
    </div>
  )
}

export default CurvesTab
