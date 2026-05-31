import type { Config } from "tailwindcss";

// shadcn/ui-compatible token mapping. Concrete values live as CSS variables in globals.css.
export default {
  darkMode: ["class"],
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        border: "hsl(var(--border))",
        card: { DEFAULT: "hsl(var(--card))", foreground: "hsl(var(--card-foreground))" },
        primary: { DEFAULT: "hsl(var(--primary))", foreground: "hsl(var(--primary-foreground))" },
        muted: { DEFAULT: "hsl(var(--muted))", foreground: "hsl(var(--muted-foreground))" },
        // Trust-first semantic tokens.
        trust: "hsl(var(--trust))",
        warning: "hsl(var(--warning))",
        danger: "hsl(var(--danger))",
      },
      borderRadius: { lg: "var(--radius)", md: "calc(var(--radius) - 2px)" },
    },
  },
  plugins: [],
} satisfies Config;
