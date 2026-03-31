import { TERMINAL } from '../../lib/theme'

const SUB_TABS = ['CURVES', 'INDICATORS', 'RISK', 'SENTIMENT'] as const
type SubTab = typeof SUB_TABS[number]

interface MacroSubTabNavProps {
  activeTab: SubTab
  onTabChange: (tab: SubTab) => void
}

export function MacroSubTabNav({ activeTab, onTabChange }: MacroSubTabNavProps) {
  return (
    <div style={{
      display: 'flex',
      borderBottom: `1px solid ${TERMINAL.BORDER}`,
      backgroundColor: TERMINAL.PANEL,
      flexShrink: 0,
      height: 28,
    }}>
      {SUB_TABS.map((tab) => {
        const isActive = tab === activeTab
        return (
          <button
            key={tab}
            onClick={() => onTabChange(tab)}
            style={{
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: 9,
              fontWeight: isActive ? 600 : 400,
              letterSpacing: '0.15em',
              padding: '0 14px',
              border: 'none',
              borderBottom: isActive
                ? `2px solid ${TERMINAL.AMBER}`
                : '2px solid transparent',
              cursor: 'pointer',
              backgroundColor: 'transparent',
              color: isActive ? TERMINAL.AMBER : TERMINAL.MUTED,
              outline: 'none',
              height: '100%',
              transition: 'color 0.15s',
            }}
          >
            {tab}
          </button>
        )
      })}
    </div>
  )
}
