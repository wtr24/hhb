export const TERMINAL = {
  // Surfaces
  BG: '#0b0e14',
  PANEL: '#0f1520',
  ELEVATED: '#141d2e',

  // Accents
  CYAN: '#00c2e0',
  AMBER: '#f0a500',
  AMBER_DIM: '#a06c00',

  // Data
  GREEN: '#00d986',
  RED: '#f04060',
  ORANGE: '#f07020',
  BRIGHT_GREEN: '#00ff88',
  BLUE: '#3d8bff',

  // Text
  TEXT: '#c8d4e8',
  DIM: '#3a4a60',
  MUTED: '#566880',

  // Structure
  BORDER: '#1a2535',
  BORDER_BRIGHT: '#2a3f5a',
  BORDER_ACTIVE: '#00c2e0',
} as const;

export const MODULE_TABS = [
  'EQUITY',
  'MACRO',
  'FX',
  'CRYPTO',
  'NEWS',
  'SCREENER',
] as const;

export type ModuleTab = (typeof MODULE_TABS)[number];
