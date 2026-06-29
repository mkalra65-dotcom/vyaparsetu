import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        ink: "#17202A",
        saffron: "#E86F28",
        leaf: "#247A50",
        mist: "#EEF5F1",
      },
      boxShadow: {
        soft: "0 12px 30px rgba(23, 32, 42, 0.08)",
      },
    },
  },
  plugins: [],
};

export default config;
