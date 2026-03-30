import { useState } from "react";
import { useKeyboard } from "./hooks/useKeyboard";
import { MODULE_TABS, type ModuleTab } from "./lib/theme";
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
    <div className="h-screen flex flex-col bg-terminal-bg text-terminal-amber font-terminal text-xs">
      {/* Top bar */}
      <header className="border-b border-terminal-border px-2 py-1 flex justify-between items-center">
        <span className="font-bold tracking-wider">HHBFIN TERMINAL</span>
        <span className="text-terminal-dim" id="event-countdown">--:-- NEXT EVENT</span>
      </header>

      {/* Tab nav — keyboard navigable via number keys 1-6 */}
      <nav className="border-b border-terminal-border flex">
        {MODULE_TABS.map((tab, i) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-1 transition-colors ${
              activeTab === tab
                ? "bg-terminal-amber text-black font-bold"
                : "hover:bg-terminal-border"
            }`}
          >
            <span className="text-terminal-dim">{i + 1}:</span>{tab}
          </button>
        ))}
      </nav>

      {/* Main module content area — fixed viewport height (D-01: nothing scrolls) */}
      <main className="flex-1 overflow-hidden">
        {activeTab === "EQUITY" && <EquityModule />}
        {activeTab === 'MACRO' && <MacroModule />}
        {activeTab !== "EQUITY" && activeTab !== "MACRO" && (
          <div className="p-2">
            <div className="text-terminal-green">[{activeTab}] MODULE READY</div>
            <p className="text-terminal-dim mt-2">Press 1-6 to switch modules.</p>
          </div>
        )}
      </main>

      {/* Status bar */}
      <footer className="fixed bottom-0 left-0 right-0 border-t border-terminal-border px-2 py-0.5 bg-terminal-bg text-terminal-dim flex justify-between">
        <span>HHBFin v0.1.0</span>
        <span>Keys: 1-6 modules</span>
      </footer>
    </div>
  );
}
