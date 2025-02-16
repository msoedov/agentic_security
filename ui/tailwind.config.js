/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{vue,js,ts,jsx,tsx}"],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        technopollas: ['Technopollas', 'sans-serif'],
      },
      colors: {
        dark: {
          bg: '#121212',
          card: '#1E1E1E',
          text: '#FFFFFF',
          accent: {
            green: '#4CAF50',
            red: '#F44336',
            orange: '#FF9800',
            yellow: '#FFEB3B',
          },
        },
      },
      borderRadius: {
        'lg': '1rem',
      },
    }
  },
  plugins: [],
}

