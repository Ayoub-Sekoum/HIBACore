import type { Config } from 'tailwindcss'

export default {
  darkMode: 'class',   // ← this is the only change that matters
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {},
  },
  plugins: [],
} satisfies Config