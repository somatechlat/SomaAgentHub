/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        soma: {
          primary: '#2563eb',
          secondary: '#7c3aed',
          accent: '#10b981',
        },
      },
    },
  },
  plugins: [],
}
