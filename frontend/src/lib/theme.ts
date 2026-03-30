export const TERMINAL = {
  BG: "#0a0a0a",
  AMBER: "#ff9900",
  GREEN: "#00d084",
  RED: "#ff4444",
  ORANGE: '#ff6600',
  BRIGHT_GREEN: '#00ff66',
  DIM: "#404040",
  BORDER: "#1a1a1a",
} as const;

export const MODULE_TABS = [
  "EQUITY",
  "MACRO",
  "FX",
  "CRYPTO",
  "NEWS",
  "SCREENER",
] as const;

export type ModuleTab = (typeof MODULE_TABS)[number];
