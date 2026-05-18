import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class", '[data-theme="cinema"]'],
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    container: { center: true, padding: "1rem", screens: { "2xl": "1440px" } },
    extend: {
      colors: {
        // Drive all colors through CSS variables defined in styles/tokens.css
        bg: {
          0: "var(--bg-0)",
          1: "var(--bg-1)",
          2: "var(--bg-2)",
          3: "var(--bg-3)",
          glass: "var(--bg-glass)",
        },
        line: {
          1: "var(--line-1)",
          2: "var(--line-2)",
          3: "var(--line-3)",
          strong: "var(--line-strong)",
        },
        fg: {
          0: "var(--fg-0)",
          1: "var(--fg-1)",
          2: "var(--fg-2)",
          3: "var(--fg-3)",
        },
        accent: {
          DEFAULT: "var(--accent)",
          soft: "var(--accent-soft)",
          line: "var(--accent-line)",
        },
        cyan: "var(--cyan)",
        violet: "var(--violet)",
        pos: "var(--pos)",
        neg: "var(--neg)",
        warn: "var(--warn)",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "monospace"],
        serif: ["Instrument Serif", "Söhne Mono", "serif"],
      },
      borderRadius: {
        lg: "12px",
        md: "10px",
        sm: "8px",
        xs: "6px",
      },
      transitionTimingFunction: {
        "out-soft": "cubic-bezier(0.2, 0.8, 0.2, 1)",
        spring: "cubic-bezier(0.34, 1.56, 0.64, 1)",
      },
      keyframes: {
        "fade-up": {
          from: { opacity: "0", transform: "translateY(8px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        "pulse-amber": {
          "0%": { boxShadow: "0 0 0 0 rgba(232,184,100,0.5)" },
          "70%": { boxShadow: "0 0 0 8px rgba(232,184,100,0)" },
          "100%": { boxShadow: "0 0 0 0 rgba(232,184,100,0)" },
        },
      },
      animation: {
        "fade-up": "fade-up 360ms cubic-bezier(0.2,0.8,0.2,1) both",
        "pulse-amber": "pulse-amber 1.4s cubic-bezier(0.2,0.8,0.2,1) infinite",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};

export default config;
