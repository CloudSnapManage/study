# Cognito Electron Experimental

This folder is an isolated performance and packaging experiment. It is not the canonical Cognito runtime. The production architecture remains the local FastAPI server plus browser frontend in the repository root.

## Architecture

Electron reserves a random loopback port, launches a PyInstaller-bundled copy of the canonical FastAPI app, and authenticates `/api/health` with a random per-launch API token and health nonce before opening a hardened BrowserWindow. Runtime data is written to Electron's per-user data directory, never inside the installed application.

Security defaults: context isolation on, Node integration off, renderer sandbox on, web security on, navigation restricted to the selected per-launch loopback origin, and external HTTPS checkout opened through the operating system browser.

## Develop

```bash
cd build/electron-experimental
npm install
npm run build:server
npm start
```

## Build Linux installers

```bash
npm install
npm run build:linux
```

Artifacts are written only to `build/electron-experimental/dist/`:

- `Cognito-Experimental-0.1.0-x86_64.AppImage`: portable executable
- `Cognito-Experimental-0.1.0-amd64.deb`: Debian/Ubuntu installer
- `linux-unpacked/cognito-experimental`: unpacked executable for smoke testing

The package uses Electron 45.5.0, electron-builder 26.18.0, and an explicit ASAR allowlist. The bundled server is placed under `resources/server/` as an extra resource.

## Limitations

- Experimental Linux build only in this repository state.
- Larger disk/memory footprint than launching Cognito in a browser.
- No code signing or auto-update channel.
- The current package uses Electron's default icon and does not yet set Linux desktop window-association metadata.
- The bundled Python service is independently spawned; a crash is shown as a desktop error.
- Each launch creates fresh capability and health secrets; they are not persisted in the package.
- Rebuild the wrapper whenever canonical backend/frontend code changes.
