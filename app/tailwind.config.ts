export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        bg: '#000000',
        card: '#0a0a0a',
        accent: '#FFB800',
        'accent-dim': '#CC9400',
        text: '#e5e5e5',
        'text-dim': '#888888',
        'text-faint': '#555555',
        'divider': '#1a1a1a',
        'pill-bg': '#1a1a1a',
      },
      fontFamily: {
        sans: ['-apple-system', 'BlinkMacSystemFont', 'PingFang HK', 'Microsoft JhengHei', 'sans-serif'],
      },
    },
  },
}
