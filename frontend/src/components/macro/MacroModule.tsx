import React, { useState } from 'react'
import { TERMINAL } from '../../lib/theme'
import { MacroSubTabNav } from './MacroSubTabNav'
import { useMacroData } from '../../hooks/useMacroData'

// Sub-tab components — imported below (created in plans 05-06 through 05-09)
// Use lazy placeholders here so this plan compiles independently.
// Each is replaced by the real component as its plan executes.
const CurvesTab = React.lazy(() =>
  import('./CurvesTab').catch(() => ({ default: () => <PlaceholderTab name="CURVES" /> }))
)
const IndicatorsTab = React.lazy(() =>
  import('./IndicatorsTab').catch(() => ({ default: () => <PlaceholderTab name="INDICATORS" /> }))
)
const RiskTab = React.lazy(() =>
  import('./RiskTab').catch(() => ({ default: () => <PlaceholderTab name="RISK" /> }))
)
const SentimentTab = React.lazy(() =>
  import('./SentimentTab').catch(() => ({ default: () => <PlaceholderTab name="SENTIMENT" /> }))
)

function PlaceholderTab({ name }: { name: string }) {
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
      {name} — LOADING...
    </div>
  )
}

type SubTab = 'CURVES' | 'INDICATORS' | 'RISK' | 'SENTIMENT'

export function MacroModule() {
  const [activeSubTab, setActiveSubTab] = useState<SubTab>('CURVES')
  const macroData = useMacroData()

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        overflow: 'hidden',
        backgroundColor: TERMINAL.BG,
      }}
    >
      {/* Module header */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 12px',
        height: 32,
        borderBottom: `1px solid ${TERMINAL.BORDER}`,
        backgroundColor: TERMINAL.PANEL,
        flexShrink: 0,
      }}>
        <span style={{
          fontSize: 9,
          fontWeight: 600,
          color: TERMINAL.CYAN,
          letterSpacing: '0.18em',
        }}>
          MACRO OVERVIEW
        </span>
        {macroData.error && (
          <span style={{
            fontSize: 9,
            color: TERMINAL.RED,
            letterSpacing: '0.08em',
          }}>
            {macroData.error}
          </span>
        )}
        {macroData.loading && (
          <span style={{ fontSize: 9, color: TERMINAL.MUTED, letterSpacing: '0.1em' }}>
            LOADING...
          </span>
        )}
      </div>

      {/* Sub-tab nav */}
      <MacroSubTabNav activeTab={activeSubTab} onTabChange={setActiveSubTab} />

      {/* Sub-tab content area */}
      <div style={{ flex: 1, overflow: 'hidden', minHeight: 0 }}>
        <React.Suspense fallback={<PlaceholderTab name={activeSubTab} />}>
          {activeSubTab === 'CURVES' && (
            <CurvesTab data={macroData.curves} loading={macroData.loading} />
          )}
          {activeSubTab === 'INDICATORS' && (
            <IndicatorsTab data={macroData.indicators} loading={macroData.loading} />
          )}
          {activeSubTab === 'RISK' && (
            <RiskTab data={macroData.risk} loading={macroData.loading} />
          )}
          {activeSubTab === 'SENTIMENT' && (
            <SentimentTab data={macroData.sentiment} loading={macroData.loading} />
          )}
        </React.Suspense>
      </div>
    </div>
  )
}
