// Colour pairs the site puts text on. Each value mirrors a variable in globals.css, and a unit
// test checks both that they match and that every pair meets WCAG AA (4.5:1).

export const TOKENS = {
  canvas: '#f2f4f6',
  surface: '#ffffff',
  surface2: '#e6ebf0',
  ink: '#0c1722',
  ink2: '#35475a',
  muted: '#566779',
  navy: '#0b2133',
  navy2: '#143149',
  deck: '#0f2a40',
  deckHot: '#1a2f43',
  onNavy: '#eef3f7',
  onNavyMuted: '#a8bbcb',
  signal: '#a83c06',
  signalFill: '#ff8a3d',
  signalHover: '#ffa366',
  pass: '#1c6a3a',
  passWash: '#e1f0e6',
  fail: '#ad2418',
  failWash: '#fbe5e2',
  work: '#7d5600',
  workWash: '#f7eed8',
  layer: '#1d5a85',
  layerWash: '#e2edf6',
  codeBg: '#0a1824',
  codeInk: '#e3ebf2',
  codeMuted: '#9cb0c2',
  codePass: '#8fd8a8',
  codeFail: '#ff9b8f',
  outputBg: '#0f2232',
} as const

export type Token = keyof typeof TOKENS

export const TEXT_PAIRS: readonly [Token, Token][] = [
  ['ink', 'canvas'],
  ['ink2', 'canvas'],
  ['muted', 'canvas'],
  ['ink', 'surface'],
  ['ink2', 'surface'],
  ['muted', 'surface'],
  ['ink2', 'surface2'],
  ['muted', 'surface2'],
  ['signal', 'canvas'],
  ['signal', 'surface'],
  ['pass', 'passWash'],
  ['pass', 'surface'],
  ['fail', 'failWash'],
  ['fail', 'surface'],
  ['work', 'workWash'],
  ['work', 'surface'],
  ['layer', 'layerWash'],
  ['layer', 'surface'],
  ['onNavy', 'navy'],
  ['onNavyMuted', 'navy'],
  ['onNavy', 'navy2'],
  ['onNavyMuted', 'navy2'],
  ['signalFill', 'navy'],
  ['onNavy', 'deck'],
  ['onNavyMuted', 'deck'],
  ['onNavy', 'deckHot'],
  ['onNavyMuted', 'deckHot'],
  ['signalFill', 'deckHot'],
  ['navy', 'signalHover'],
  ['navy', 'signalFill'],
  ['codeInk', 'codeBg'],
  ['codeMuted', 'codeBg'],
  ['codePass', 'codeBg'],
  ['codeFail', 'codeBg'],
  ['codeInk', 'outputBg'],
  ['codeMuted', 'outputBg'],
  ['codePass', 'outputBg'],
  ['codeFail', 'outputBg'],
  ['signalFill', 'codeBg'],
]

function channel(hex: string, offset: number): number {
  const value = parseInt(hex.slice(offset, offset + 2), 16) / 255
  return value <= 0.03928 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4
}

function luminance(hex: string): number {
  return 0.2126 * channel(hex, 1) + 0.7152 * channel(hex, 3) + 0.0722 * channel(hex, 5)
}

export function contrast(a: string, b: string): number {
  const [la, lb] = [luminance(a), luminance(b)]
  return (Math.max(la, lb) + 0.05) / (Math.min(la, lb) + 0.05)
}
