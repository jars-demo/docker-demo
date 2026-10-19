// Colour pairs the site puts text on. Each value mirrors a variable in globals.css, and a unit
// test checks both that they match and that every pair meets WCAG AA (4.5:1).

export const TOKENS = {
  canvas: '#ffffff',
  canvas2: '#f4f7fb',
  surface: '#ffffff',
  ink: '#0b1531',
  ink2: '#33415c',
  muted: '#56647d',
  blue: '#1d63ed',
  blueHover: '#1550c8',
  blueText: '#1854cc',
  blueWash: '#e5f2fc',
  onBlue: '#ffffff',
  navy: '#00084d',
  navy2: '#0c1660',
  onNavy: '#ffffff',
  onNavyMuted: '#b8c2ea',
  sky: '#8cc2ff',
  pass: '#13713b',
  passWash: '#e4f4ea',
  fail: '#b3261e',
  failWash: '#fdeceb',
  codeBg: '#0a0f2c',
  codeHead: '#121a42',
  codeInk: '#e8ecff',
  codeMuted: '#9ba8d0',
  codePass: '#7fe0a6',
  codeFail: '#ff9d93',
  codeBlue: '#93bfff',
} as const

export type Token = keyof typeof TOKENS

export const TEXT_PAIRS: readonly [Token, Token][] = [
  ['ink', 'canvas'],
  ['ink2', 'canvas'],
  ['muted', 'canvas'],
  ['ink', 'canvas2'],
  ['ink2', 'canvas2'],
  ['muted', 'canvas2'],
  ['blueText', 'canvas'],
  ['blueText', 'canvas2'],
  ['blueText', 'blueWash'],
  ['blue', 'canvas'],
  ['ink', 'blueWash'],
  ['onBlue', 'blue'],
  ['onBlue', 'blueHover'],
  ['onNavy', 'navy'],
  ['onNavyMuted', 'navy'],
  ['onNavy', 'navy2'],
  ['onNavyMuted', 'navy2'],
  ['sky', 'navy'],
  ['sky', 'navy2'],
  ['pass', 'passWash'],
  ['pass', 'canvas'],
  ['fail', 'failWash'],
  ['fail', 'canvas'],
  ['codeInk', 'codeBg'],
  ['codeMuted', 'codeBg'],
  ['codePass', 'codeBg'],
  ['codeFail', 'codeBg'],
  ['codeBlue', 'codeBg'],
  ['codeMuted', 'codeHead'],
  ['codeInk', 'codeHead'],
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
