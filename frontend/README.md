# PANDDA frontend

Simple web user interface displaying data in ADiCT-lite (DP³ instance).

### Configuration

Configuration utilizes environmental variables during build:

- `VITE_API_URL`: URL of DP³ API interface

You can store these variables inside `.env` files as explaned here: https://vitejs.dev/guide/env-and-mode

### Usage

1. Install dependencies: `npm install`
2. Run a development server: `npm run dev` or build for production: `npm run build` (creates files in `dist/` folder - separate HTTP server is needed).

### RPM

Frontend can be easily built and packaged for production using provided `CMakeLists.txt` file.
Created RPM package contains only static HTML, CSS, JavaScript and assets.
They are put into `/var/www` folder during installation on target system and are intended to be directly served by nginx or similar webserver.

I am aware that packaging HTML using CMake into RPM is... strange.
But it should simplify deployment and CMake/CPack is standard mean of packaging for NEMEA modules.
There's no need to install Node and `npm` on target system.

To build RPM package run:

```sh
mkdir build
cd build
cmake ..
make package
```

Package will be located in the `build` directory.
