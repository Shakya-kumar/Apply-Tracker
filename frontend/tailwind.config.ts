import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        ink: "#17211c",
        forest: "#194b3b",
        moss: "#52765a",
        lime: "#c9e47b",
        paper: "#f5f6f0",
        muted: "#78827b",
      },
      fontFamily: {
        sans: ["Arial", "Helvetica", "sans-serif"],
      },
      boxShadow: {
        soft: "0 20px 60px rgba(25, 51, 39, .08)",
      },
    },
  },
  plugins: [],
};

export default config;
