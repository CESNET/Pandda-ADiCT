# PANDDA frontend

Simple web user interface displaying data in ADiCT-lite (DP³ instance).

### Configuration

Configuration utilizes environmental variables during build:

- `VITE_API_URL`: URL of DP³ API interface

You can store these variables inside `.env` files as explaned here: https://vitejs.dev/guide/env-and-mode

### Usage

1. Install dependencies: `npm install`
2. Run a development server: `npm run dev` or build for production: `npm run build` (creates files in `dist/` folder - separate HTTP server is needed).
