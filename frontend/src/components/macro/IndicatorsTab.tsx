import React from 'react'
import { TERMINAL } from '../../lib/theme'
import { MacroPanel } from './MacroPanel'
import { PolicyRatesPanel } from './PolicyRatesPanel'
import type { IndicatorsData } from '../../hooks/useMacroData'

interface IndicatorsTabProps {
  data: IndicatorsData | null
  loading: boolean
}

export function IndicatorsTab({ data, loading }: IndicatorsTabProps) {
  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(3, 1fr)',
        gridTemplateRows: 'repeat(2, 1fr)',
        height: '100%',
        overflow: 'hidden',
        backgroundColor: TERMINAL.BG,
      }}
    >
      {/* Row 1 */}
      <MacroPanel
        title="CPI"
        usData={
          data
            ? {
                current: data.cpi.current_us,
                history: data.cpi.history_us,
                mom: data.cpi.mom,
                yoy: data.cpi.yoy,
              }
            : null
        }
        ukData={
          data && data.cpi.current_uk != null
            ? { current: data.cpi.current_uk, history: data.cpi.history_uk ?? [] }
            : null
        }
        loading={loading}
      />
      <MacroPanel
        title="CORE CPI"
        usData={
          data
            ? {
                current: data.core_cpi.current_us,
                history: data.core_cpi.history_us,
                mom: data.core_cpi.mom,
                yoy: data.core_cpi.yoy,
              }
            : null
        }
        loading={loading}
      />
      <MacroPanel
        title="PCE"
        usData={
          data
            ? {
                current: data.pce.current_us,
                history: data.pce.history_us,
                mom: data.pce.mom,
                yoy: data.pce.yoy,
              }
            : null
        }
        loading={loading}
      />

      {/* Row 2 */}
      <MacroPanel
        title="GDP"
        usData={
          data
            ? {
                current: data.gdp.current_us,
                history: data.gdp.history_us,
                mom: data.gdp.mom,
                yoy: data.gdp.yoy,
              }
            : null
        }
        ukData={
          data && data.gdp.current_uk != null
            ? { current: data.gdp.current_uk, history: data.gdp.history_uk ?? [] }
            : null
        }
        euData={
          data && data.gdp.current_eu != null ? { current: data.gdp.current_eu } : null
        }
        loading={loading}
      />
      <MacroPanel
        title="UNEMPLOYMENT"
        usData={
          data
            ? {
                current: data.unemployment.current_us,
                history: data.unemployment.history_us,
                mom: data.unemployment.mom,
                yoy: data.unemployment.yoy,
              }
            : null
        }
        ukData={
          data && data.unemployment.current_uk != null
            ? { current: data.unemployment.current_uk, history: data.unemployment.history_uk ?? [] }
            : null
        }
        loading={loading}
      />
      <PolicyRatesPanel data={data ? data.policy_rates : null} loading={loading} />
    </div>
  )
}
