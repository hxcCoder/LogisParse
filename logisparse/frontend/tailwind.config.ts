import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        ink: "#18202a",
        line: "#d7dee8",
        salmon: "#e35d54",
        sea: "#0f8b8d",
        kelp: "#2e6f40",
        amber: "#d99a21"
      }
    }
  },
  plugins: []
};

export default config;
