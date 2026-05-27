/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        "bias-left": "#3b82f6",
        "bias-lean-left": "#93c5fd",
        "bias-center": "#6b7280",
        "bias-lean-right": "#fca5a5",
        "bias-right": "#ef4444",
        "bias-far-left": "#1d4ed8",
        "bias-far-right": "#b91c1c",
      },
    },
  },
  plugins: [],
};
