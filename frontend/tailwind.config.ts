import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: '#1c3c3c',
        'user-message': '#076699',
        'user-message-bg': '#e8f4f8',
        'avatar-bg': '#e8ebeb',
        secondary: '#1c3c3c',
        success: '#10b981',
        warning: '#f59e0b',
        error: '#ef4444',
        background: '#f9f9f9',
        'subagent-hover': '#bbc4c4',
        surface: '#f9fafb',
        border: '#e5e7eb',
        'border-light': '#f3f4f6',
        'text-primary': '#111827',
        'text-secondary': '#6b7280',
        'text-tertiary': '#9ca3af',
      },
    },
  },
  plugins: [],
};

export default config;
