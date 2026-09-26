import type { Config } from 'tailwindcss'

const config: Config = {
  content: ['./src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      colors: {
        flow: {
          green:  '#22c55e',
          amber:  '#f59e0b',
          red:    '#ef4444',
          violet: '#a78bfa',
          blue:   '#3b82f6',
        },
      },
      keyframes: {
        pulse_slow: { '0%,100%': { opacity: '1' }, '50%': { opacity: '0.4' } },
        blink: { '0%,100%': { opacity: '1' }, '49%': { opacity: '1' }, '50%': { opacity: '0' } },
        slide_in_right: { from: { transform: 'translateX(100%)' }, to: { transform: 'translateX(0)' } },
        fade_in: { from: { opacity: '0', transform: 'translateY(4px)' }, to: { opacity: '1', transform: 'translateY(0)' } },
      },
      animation: {
        pulse_slow: 'pulse_slow 2s ease-in-out infinite',
        blink: 'blink 1s step-end infinite',
        slide_in_right: 'slide_in_right 0.2s ease-out',
        fade_in: 'fade_in 0.15s ease-out',
      },
    },
  },
  plugins: [],
}
export default config
