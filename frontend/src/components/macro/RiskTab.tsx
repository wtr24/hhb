import { TERMINAL } from '../../lib/theme'
import { VixTermChart } from './VixTermChart'
import { RegimeClassifier } from './RegimeClassifier'
import { PutCallChart } from './PutCallChart'
import type { RiskData } from '../../hooks/useMacroData'

interface RiskTabProps {
  data: RiskData | null
  loading: boolean
}

export function RiskTab({ data, loading }: RiskTabProps) {
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
      {/* Left 60%: VIX term structure chart */}
      <div
        style={{
          borderRight: `1px solid ${TERMINAL.BORDER}`,
          overflow: 'hidden',
          minHeight: 0,
        }}
      >
        <VixTermChart data={data} loading={loading} />
      </div>

      {/* Right 40%: regime classifier (top 50%) + put/call chart (bottom 50%) */}
      <div
        style={{
          display: 'grid',
          gridTemplateRows: '50% 50%',
          height: '100%',
          overflow: 'hidden',
          minHeight: 0,
        }}
      >
        <div style={{ overflow: 'hidden', minHeight: 0 }}>
          <RegimeClassifier data={data} loading={loading} />
        </div>
        <div style={{ overflow: 'hidden', minHeight: 0 }}>
          <PutCallChart data={data} loading={loading} />
        </div>
      </div>
    </div>
  )
}

export default RiskTab
