import React from 'react'
import { TERMINAL } from '../../lib/theme'

const SUB_TABS = ['CURVES', 'INDICATORS', 'RISK', 'SENTIMENT'] as const
type SubTab = typeof SUB_TABS[number]

interface MacroSubTabNavProps {
  activeTab: SubTab
  onTabChange: (tab: SubTab) => void
}

export function MacroSubTabNav({ activeTab, onTabChange }: MacroSubTabNavProps) {
  return (
    <div
      style={{
        display: 'flex',
        borderBottom: `1px solid ${TERMINAL.BORDER}`,
        backgroundColor: TERMINAL.BG,
      }}
    >
      {SUB_TABS.map((tab) => {
        const isActive = tab === activeTab
        return (
          <button
            key={tab}
            onClick={() => onTabChange(tab)}
            style={{
              fontFamily: 'inherit',
              fontSize: '11px',
              fontWeight: 'bold',
              letterSpacing: '0.1em',
              padding: '4px 16px',
              border: 'none',
              cursor: 'pointer',
              backgroundColor: isActive ? TERMINAL.AMBER : 'transparent',
              color: isActive ? '#000000' : TERMINAL.AMBER,
              outline: 'none',
            }}
            onMouseEnter={(e) => {
              if (!isActive) {
                (e.currentTarget as HTMLButtonElement).style.backgroundColor = TERMINAL.BORDER
              }
            }}
            onMouseLeave={(e) => {
              if (!isActive) {
                (e.currentTarget as HTMLButtonElement).style.backgroundColor = 'transparent'
              }
            }}
          >
            {tab}
          </button>
        )
      })}
    </div>
  )
}
