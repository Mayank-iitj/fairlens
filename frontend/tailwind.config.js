/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        cream: '#FFF8F2',
        caramel: '#C48A52',
        walnut: '#875C3C',
        espresso: '#3D2320',
        caramel10: '#C48A521A',
        caramel20: '#C48A5233',
        muted: '#7A5540',
      },
      fontFamily: {
        display: ['Fraunces', 'serif'],
        body: ['Manrope', 'sans-serif'],
      },
      boxShadow: {
        card: '0 12px 28px rgba(61, 35, 32, 0.08)',
      },
    },
  },
  plugins: [],
}
