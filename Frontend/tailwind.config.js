/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
      },
      colors: {
        base: '#000000',
        muted: '#050505',
        strong: '#171717',
        raised: '#262626',
        bd: '#333333',
        t1: '#a6a6a6',
        t2: '#fafafa',
        t3: '#ffffff',
        accent: '#3355ff',
        'accent-2': '#7c93ff',
        crit: '#ef4444',
        high: '#f97316',
        med: '#eab308',
        low: '#22c55e',
        // Fallbacks for standard tokens if used
        surface: { base: '#000000', muted: '#050505', strong: '#171717', raised: '#262626' },
        border: { default: '#333333' }
      },
      borderRadius: {
        xs: '4px',
        sm: '6px',
        md: '12px',
        lg: '16px',
      },
      animation: {
        'float': 'float 6s ease-in-out infinite',
        'dash-flow': 'dash-flow 18s linear infinite',
        'packet-pulse': 'packet-pulse 2.4s ease-in-out infinite',
        'gradient-x': 'gradient-x 6s ease infinite',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-8px)' },
        },
        'dash-flow': {
          to: { strokeDashoffset: '-1000' },
        },
        'packet-pulse': {
          '0%, 100%': { opacity: '0.5', transform: 'scale(1)' },
          '50%': { opacity: '1', transform: 'scale(1.15)' },
        },
        'gradient-x': {
          '0%, 100%': { backgroundPosition: '0% 50%' },
          '50%': { backgroundPosition: '100% 50%' },
        },
      },
    },
  },
  plugins: [],
}
