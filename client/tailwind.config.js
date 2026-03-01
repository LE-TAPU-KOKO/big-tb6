/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: '#0891B2',
        'primary-light': '#22D3EE',
        secondary: '#22D3EE',
        cta: '#22C55E',
        background: '#F0FDFA',
        text: '#134E4A',
        'text-muted': '#64748B',
        surface: '#FFFFFF',
        border: '#E2E8F0',
        error: '#EF4444',
      },
      fontFamily: {
        heading: ['Figtree', 'sans-serif'],
        body: ['Noto Sans', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
