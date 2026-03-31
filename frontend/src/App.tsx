import { useState } from "react";
import { useKeyboard } from "./hooks/useKeyboard";
import { MODULE_TABS, type ModuleTab, TERMINAL } from "./lib/theme";
import EquityModule from "./components/equity/EquityModule";
import { MacroModule } from "./components/macro/MacroModule";

export default function App() {
  const [activeTab, setActiveTab] = useState<ModuleTab>("EQUITY");

  useKeyboard((key) => {
    const index = parseInt(key) - 1;
    if (index >= 0 && index < MODULE_TABS.length) {
      setActiveTab(MODULE_TABS[index]);
    }
  });

  return (
    <div style={{
      height: '100vh',
      display: 'flex',
      flexDirection: 'column',
      backgroundColor: TERMINAL.BG,
      color: TERMINAL.TEXT,
      fontFamily: "'JetBrains Mono', monospace",
      fontSize: 11,
      overflow: 'hidden',
    }}>
      {/* Top bar */}
      <header style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 12px',
        height: 32,
        borderBottom: `1px solid ${TERMINAL.BORDER}`,
        backgroundColor: TERMINAL.PANEL,
        flexShrink: 0,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          {/* Logo mark */}
          <div style={{
            width: 18,
            height: 18,
            background: `linear-gradient(135deg, ${TERMINAL.CYAN}, ${TERMINAL.AMBER})`,
            borderRadius: 3,
            flexShrink: 0,
          }} />
          <span style={{
            fontWeight: 700,
            fontSize: 11,
            letterSpacing: '0.2em',
            color: TERMINAL.TEXT,
          }}>
            HHBFIN
          </span>
          <span style={{
            fontSize: 9,
            letterSpacing: '0.1em',
            color: TERMINAL.MUTED,
            borderLeft: `1px solid ${TERMINAL.BORDER}`,
            paddingLeft: 10,
          }}>
            TERMINAL v0.1
          </span>
        </div>
        <span style={{
          fontSize: 10,
          color: TERMINAL.CYAN,
          letterSpacing: '0.08em',
          fontWeight: 500,
        }} id="event-countdown">
          --:-- NEXT EVENT
        </span>
      </header>

      {/* Tab nav */}
      <nav style={{
        display: 'flex',
        backgroundColor: TERMINAL.PANEL,
        borderBottom: `1px solid ${TERMINAL.BORDER}`,
        flexShrink: 0,
        height: 28,
      }}>
        {MODULE_TABS.map((tab, i) => {
          const isActive = activeTab === tab;
          return (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 5,
                padding: '0 14px',
                background: 'none',
                border: 'none',
                borderBottom: isActive
                  ? `2px solid ${TERMINAL.CYAN}`
                  : '2px solid transparent',
                borderRight: `1px solid ${TERMINAL.BORDER}`,
                color: isActive ? TERMINAL.CYAN : TERMINAL.MUTED,
                fontSize: 10,
                fontFamily: 'inherit',
                fontWeight: isActive ? 600 : 400,
                letterSpacing: '0.12em',
                cursor: 'pointer',
                transition: 'color 0.15s',
                whiteSpace: 'nowrap',
              }}
            >
              <span style={{
                fontSize: 8,
                color: isActive ? TERMINAL.CYAN : TERMINAL.DIM,
                fontWeight: 400,
              }}>{i + 1}</span>
              {tab}
            </button>
          );
        })}
      </nav>

      {/* Module content */}
      <main style={{ flex: 1, overflow: 'hidden', minHeight: 0 }}>
        {activeTab === "EQUITY" && <EquityModule />}
        {activeTab === "MACRO" && <MacroModule />}
        {activeTab !== "EQUITY" && activeTab !== "MACRO" && (
          <div style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            height: '100%',
            gap: 8,
          }}>
            <div style={{
              fontSize: 9,
              letterSpacing: '0.2em',
              color: TERMINAL.MUTED,
              textTransform: 'uppercase',
            }}>
              {activeTab} MODULE
            </div>
            <div style={{
              width: 40,
              height: 1,
              background: `linear-gradient(90deg, transparent, ${TERMINAL.BORDER}, transparent)`,
            }} />
            <div style={{ fontSize: 9, color: TERMINAL.DIM, letterSpacing: '0.15em' }}>
              COMING SOON
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
