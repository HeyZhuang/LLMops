/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        /* 深空灰色阶 */
        abyss: {
          50: '#f0f1f4',
          100: '#d4d7e0',
          200: '#a8afc1',
          300: '#7c87a2',
          400: '#505f83',
          500: '#2a3a5c',
          600: '#1e2d4a',
          700: '#162240',
          800: '#0F172A',
          900: '#0a1020',
          950: '#060b16',
        },
        /* 鎏金色阶 */
        gold: {
          50: '#fdf9ef',
          100: '#f9f0d5',
          200: '#f0dda6',
          300: '#e6c76e',
          400: '#D4AF37',
          500: '#c49b2a',
          600: '#a67d1f',
          700: '#8a6319',
          800: '#6e4f14',
          900: '#523b0f',
          950: '#362709',
        },
        /* 羊皮纸白色阶 */
        parchment: {
          50: '#fdfcfb',
          100: '#FAF8F5',
          200: '#F8F5F0',
          300: '#f0ebe2',
          400: '#e4dccf',
          500: '#d1c7b5',
          600: '#b5a88e',
          700: '#978a6e',
          800: '#796e57',
          900: '#5b5341',
          950: '#3d382c',
        },
      },
      backgroundImage: {
        'gold-gradient': 'linear-gradient(135deg, #D4AF37 0%, #f0dda6 50%, #D4AF37 100%)',
        'gold-subtle': 'linear-gradient(135deg, rgba(212,175,55,0.08) 0%, rgba(212,175,55,0.02) 100%)',
        'abyss-gradient': 'linear-gradient(180deg, #162240 0%, #0F172A 100%)',
        'abyss-radial': 'radial-gradient(ellipse at top, #1e2d4a 0%, #0F172A 70%)',
      },
      boxShadow: {
        'gold-sm': '0 1px 3px rgba(212,175,55,0.15)',
        'gold-md': '0 4px 12px rgba(212,175,55,0.2)',
        'gold-lg': '0 8px 24px rgba(212,175,55,0.25)',
        'gold-glow': '0 0 20px rgba(212,175,55,0.15)',
        'glass': '0 8px 32px rgba(0,0,0,0.12)',
        'inner-gold': 'inset 0 1px 0 rgba(212,175,55,0.1)',
      },
      borderColor: {
        'gold-dim': 'rgba(212,175,55,0.2)',
        'gold-bright': 'rgba(212,175,55,0.5)',
      },
    },
  },
  plugins: [],
}
