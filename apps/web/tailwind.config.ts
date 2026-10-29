import type { Config } from "tailwindcss";

/**
 * Dark "trading terminal" palette. Semantic names keep component classes clean
 * (bg-surface, text-muted, text-pos/neg) and make a future re-theme one place.
 */
const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "#0a0e17",
        surface: "#111726",
        "surface-2": "#161d2e",
        border: "#232c40",
        fg: "#e5e9f0",
        muted: "#7d8aa0",
        accent: "#4c8dff",
        pos: "#2ebd85",
        neg: "#f6465d",
      },
      fontFamily: {
        mono: ["ui-monospace", "SFMono-Regular", "Menlo", "Consolas", "monospace"],
      },
    },
  },
  plugins: [],
};

export default config;
