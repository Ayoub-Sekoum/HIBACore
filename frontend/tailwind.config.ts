import type { Config } from 'tailwindcss'

export default {
  darkMode: 'class',   // ← questa è l'unica modifica che conta
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {},
  },
  plugins: [],
} satisfies Config