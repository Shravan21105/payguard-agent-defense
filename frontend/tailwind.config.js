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
        // Deep Navy / Midnight Base (Phase 8 Design Tokens)
        navy: {
          950: '#070B18', // Primary Canvas
          900: '#0B1020', // Layer 1 Base
          850: '#10172B', // Layer 2 Card Base
          800: '#111A30', // Surface Primary
          750: '#17213A', // Surface Secondary
          700: '#1C2945', // Surface Raised
          600: '#28385E', // Border Subtly Elevated
          500: '#3D5285', // Muted Text / Icons
          400: '#627CB0', // Secondary Text
          300: '#94A7CE', // Primary Body Text
          200: '#C7D4EC', // Emphasized Text
          100: '#E2E9F6', // High-Contrast Headings
        },
        // Cyber Accents & Neon Highlights
        cyber: {
          blue: '#3B82F6',
          indigo: '#6366F1',
          violet: '#8B5CF6',
          purple: '#A855F7',
          cyan: '#22D3EE',
          teal: '#14B8A6',
          emerald: '#10B981',
          amber: '#F59E0B',
          rose: '#EF4444',
        },
        // Retain charcoal alias mapping to navy tokens for 100% backward compatibility
        charcoal: {
          950: '#070B18',
          900: '#0B1020',
          850: '#10172B',
          800: '#111A30',
          750: '#17213A',
          700: '#1C2945',
          600: '#28385E',
          400: '#627CB0',
          300: '#94A7CE',
          200: '#C7D4EC',
        },
        // Retain forest alias mapped to cyber emerald
        forest: {
          950: '#041716',
          900: '#062923',
          800: '#0B3F35',
          700: '#0F5448',
          600: '#147060',
          500: '#10B981',
        },
        shield: {
          allow: '#10B981',
          warn: '#F59E0B',
          block: '#EF4444',
          info: '#22D3EE',
          neutral: '#627CB0',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'Menlo', 'monospace'],
      },
      boxShadow: {
        'shield-glow': '0 0 25px -4px rgba(34, 211, 238, 0.25)',
        'shield-card': '0 8px 32px 0 rgba(0, 0, 0, 0.45)',
        'danger-glow': '0 0 25px -4px rgba(239, 68, 68, 0.35)',
        'warning-glow': '0 0 25px -4px rgba(245, 158, 11, 0.35)',
        'success-glow': '0 0 25px -4px rgba(16, 185, 129, 0.35)',
        'primary-glow': '0 0 30px -5px rgba(99, 102, 241, 0.35)',
        'cyan-glow': '0 0 25px -5px rgba(34, 211, 238, 0.3)',
        'glass-edge': 'inset 0 1px 1px 0 rgba(255, 255, 255, 0.12)',
        'glass-panel': '0 8px 32px 0 rgba(0, 0, 0, 0.37), inset 0 1px 0 0 rgba(255, 255, 255, 0.08)',
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'primary-gradient': 'linear-gradient(135deg, #2563EB 0%, #6366F1 50%, #8B5CF6 100%)',
        'secondary-gradient': 'linear-gradient(135deg, #06B6D4 0%, #3B82F6 100%)',
        'cyber-gradient': 'linear-gradient(135deg, #3B82F6 0%, #8B5CF6 50%, #22D3EE 100%)',
        'glass-gradient': 'linear-gradient(135deg, rgba(255, 255, 255, 0.05) 0%, rgba(255, 255, 255, 0.01) 100%)',
        'danger-gradient': 'linear-gradient(135deg, #DC2626 0%, #EF4444 100%)',
      },
      animation: {
        'pulse-slow': 'pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'fade-in-up': 'fadeInUp 0.3s cubic-bezier(0.16, 1, 0.3, 1) forwards',
        'radar-ping': 'radarPing 2s cubic-bezier(0, 0, 0.2, 1) infinite',
        'shimmer': 'shimmer 2.5s infinite',
      },
      keyframes: {
        fadeInUp: {
          '0%': { opacity: '0', transform: 'translateY(8px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        radarPing: {
          '75%, 100%': { transform: 'scale(2.2)', opacity: '0' },
        },
        shimmer: {
          '100%': { transform: 'translateX(100%)' },
        },
      },
    },
  },
  plugins: [],
}
