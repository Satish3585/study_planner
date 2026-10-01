/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      fontFamily: { sans: ['Inter', 'system-ui', 'sans-serif'] },
      colors: { brand: { 50:'#eef2ff',100:'#e0e7ff',400:'#818cf8',500:'#6366f1',600:'#4f46e5',700:'#4338ca' } },
      keyframes: {
        float: { '0%,100%': { transform: 'translateY(0)' }, '50%': { transform: 'translateY(-12px)' } },
        fadeUp: { '0%': { opacity: 0, transform: 'translateY(12px)' }, '100%': { opacity: 1, transform: 'none' } },
      },
      animation: { float: 'float 6s ease-in-out infinite', fadeUp: 'fadeUp .5s ease both' },
    },
  },
  plugins: [],
}
