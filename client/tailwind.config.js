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
        severity: {
          critical: '#ef4444',
          warning: '#f97316',
          advisory: '#eab308',
          info: '#3b82f6',
        },
      },
    },
  },
  plugins: [],
}
