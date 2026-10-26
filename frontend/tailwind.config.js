/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#FFFFFF",
        surface: "#F7F6F3",
        "surface-muted": "#F0EFEB",
        border: "#E9E6E0",
        "primary-orange": "#F07836",
        "primary-orange-hover": "#DE6522",
        "primary-text": "#20201E",
        "secondary-text": "#73716C",
        "status-success": "#287A52",
        "status-warning": "#B96A19",
        "status-error": "#C7463A",
      },
      fontFamily: {
        sans: ["Inter", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", "sans-serif"],
        editorial: ["Playfair Display", "Georgia", "serif"],
      },
    },
  },
  plugins: [],
}
