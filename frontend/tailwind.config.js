/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        charcoal: {
          950: '#070B0E',
          900: '#0C1115',
          850: '#10161C',
          800: '#161F27',
          750: '#1D2833',
          700: '#263442',
          600: '#394A5C',
          400: '#7F93A7',
          300: '#A2B4C5',
          200: '#CBD7E3',
        },
        forest: {
          950: '#03140D',
          900: '#062418',
          800: '#0B3A28',
          700: '#12543B',
          600: '#1A7251',
          500: '#24956B',
        },
        emerald: {
          DEFAULT: '#10B981',
          hover: '#059669',
          glow: 'rgba(16, 185, 129, 0.15)',
        },
        shield: {
          allow: '#10B981',
          warn: '#F59E0B',
          block: '#EF4444',
          neutral: '#64748B',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      boxShadow: {
        'shield-glow': '0 0 20px -5px rgba(16, 185, 129, 0.25)',
        'shield-card': '0 4px 20px -2px rgba(0, 0, 0, 0.5)',
        'danger-glow': '0 0 20px -5px rgba(239, 68, 68, 0.25)',
      }
    },
  },
  plugins: [],
}
