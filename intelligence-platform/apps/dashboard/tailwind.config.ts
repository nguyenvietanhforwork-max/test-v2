import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        canvas: "#0a0b0e",
        glass: "rgba(255,255,255,0.04)",
        "glass-hover": "rgba(255,255,255,0.07)",
        "border-subtle": "rgba(255,255,255,0.08)",
        ink: { primary: "#f5f5f7", muted: "#9aa0a6", dim: "#5c6068" },
        accent: { gold: "#c9a86a", signal: "#7eb6ff", bullish: "#56d364", bearish: "#f85149" },
      },
      fontFamily: {
        sans: ["Inter Variable", "Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "monospace"],
        editorial: ["Fraunces", "Georgia", "serif"],
      },
      backgroundImage: {
        "gradient-aurora":
          "radial-gradient(ellipse at top, rgba(126,182,255,0.08), transparent 60%), radial-gradient(ellipse at bottom right, rgba(201,168,106,0.06), transparent 50%), #0a0b0e",
        "gradient-card":
          "linear-gradient(135deg, rgba(255,255,255,0.05), rgba(255,255,255,0.01))",
      },
      backdropBlur: { glass: "20px" },
      boxShadow: {
        glow: "0 0 40px -10px rgba(126,182,255,0.25)",
        card: "0 1px 0 rgba(255,255,255,0.04) inset, 0 30px 60px -30px rgba(0,0,0,0.6)",
      },
      borderRadius: { xl2: "1.25rem" },
      letterSpacing: { ultra: "0.25em" },
      keyframes: {
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
      },
      animation: { shimmer: "shimmer 2.4s linear infinite" },
    },
  },
  plugins: [],
};

export default config;
