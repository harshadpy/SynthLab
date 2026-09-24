/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        "background": "#0B0E14",
        "surface": "#0E131D",
        "surface-container-lowest": "#080B10",
        "surface-container-low": "#121722",
        "surface-container": "#171C28",
        "surface-container-high": "#1E2535",
        "surface-container-highest": "#283042",
        "surface-bright": "#323C50",
        "primary": "#3CDDC7",
        "primary-container": "#143D37",
        "on-primary": "#00201C",
        "secondary": "#F9BC45",
        "secondary-container": "#3F2E05",
        "outline": "#4B5568",
        "outline-variant": "#232B3A",
        "on-surface": "#F1F5F9",
        "on-surface-variant": "#94A3B8",
        "tertiary-muted": "#64748B",
        "error": "#FFB4AB"
      },
      fontFamily: {
        "sans": ["Inter", "sans-serif"],
        "mono": ["JetBrains Mono", "monospace"]
      }
    }
  },
  plugins: [],
}
