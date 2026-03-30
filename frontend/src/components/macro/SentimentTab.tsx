import React from 'react'
import { TERMINAL } from '../../lib/theme'
import { FearGreedGauge } from './FearGreedGauge'
import { AtAGlanceStrip } from './AtAGlanceStrip'
import { SeasonalityChart } from './SeasonalityChart'
import type { SentimentData } from '../../hooks/useMacroData'

interface SentimentTabProps {
  data: SentimentData | null
  loading: boolean
}

export function SentimentTab({ data, loading }: SentimentTabProps) {
  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: '50% 50%',
        height: '100%',
        overflow: 'hidden',
        backgroundColor: TERMINAL.BG,
      }}
    >
      {/* Left 50%: Fear & Greed gauge + component table */}
      <div
        style={{
          borderRight: `1px solid ${TERMINAL.BORDER}`,
          overflow: 'hidden',
          minHeight: 0,
        }}
      >
        <FearGreedGauge data={data} loading={loading} />
      </div>

      {/* Right 50%: at-a-glance strip (top) + seasonality chart (bottom) */}
      <div
        style={{
          display: 'grid',
          gridTemplateRows: '40% 60%',
          height: '100%',
          overflow: 'hidden',
          minHeight: 0,
        }}
      >
        <div style={{ overflow: 'hidden', minHeight: 0 }}>
          <AtAGlanceStrip />
        </div>
        <div style={{ overflow: 'hidden', minHeight: 0 }}>
          <SeasonalityChart data={data} loading={loading} />
        </div>
      </div>
    </div>
  )
}
