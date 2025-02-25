/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        primary: {
          light: '#6366f1',
          dark: '#818cf8',
        },
        background: {
          light: '#ffffff',
          dark: '#121212',
        },
        surface: {
          light: '#f3f4f6',
          dark: '#1e1e1e',
        },
        text: {
          light: '#1f2937',
          dark: '#e5e7eb',
        },
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
    },
  },
  plugins: [],
}; 