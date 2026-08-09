# Distributing Jtutor

The app ships as a normal desktop installer. The recipient does **not** need
Python, Node, or any manual start/stop step.

## Build

```bash
npm run dist          # current platform
npm run dist:win      # Windows NSIS installer
npm run dist:mac      # macOS dmg
npm run dist:linux    # Linux AppImage
```

Each of those runs three stages:

1. `npm run build:ui` — Vite build into `apps/desktop/dist/`.
2. `npm run build:backend` — PyInstaller freezes `backend/main_frozen.py` into
   `dist-backend/jtutor-backend/` using `packaging/jtutor-backend.spec`.
3. `electron-builder` — packages the Electron shell, the frozen backend
   (`backend-dist`), the lesson content and the built UI.

Output lands in `dist-electron/`.

## What is included

- The Electron shell and its backend supervisor
- The frozen FastAPI backend, with its own Python runtime
- The built UI
- Lesson curriculum YAML (Starter + Elementary 1)
- An empty `assets/` with instructions

## What is deliberately not included

- Irodori PDFs / MP3s (Japan Foundation copyright)
- Ollama and VOICEVOX (the recipient installs those if they want the LLM and
  the tutor voice)

## Size

The frozen backend is the bulk of the installer: `faster-whisper` pulls in
`ctranslate2`, `onnxruntime` and `av`. Expect roughly 400 MB for the backend
folder and 600–700 MB unpacked in total.

Two ways to trim it:

- **Ship a smaller speech model.** Set `WHISPER_MODEL=base` as the default and
  let the app download a larger one on demand. The model itself is *not*
  bundled; it downloads on first use.
- **Lite build.** `JTUTOR_LITE_BUILD=1 npm run build:backend` excludes the
  speech stack entirely. Everything works except spoken grading, which is a
  reasonable trade for a demo build.

## Signing

Unsigned PyInstaller executables are a common SmartScreen and antivirus
false positive on Windows, and macOS requires notarization for distribution
outside the App Store. Both are configuration on `electron-builder`, and both
need credentials the repository does not carry:

- Windows: set `CSC_LINK` / `CSC_KEY_PASSWORD` in CI.
- macOS: set `APPLE_ID`, `APPLE_APP_SPECIFIC_PASSWORD`, `APPLE_TEAM_ID` and
  enable `notarize` in the `mac` block.

Until then, warn recipients about the first-run warning and publish hashes.

## Smoke-testing a build

Before shipping, on a machine with **no Python installed**:

1. Install and launch from the shortcut. A window must appear within a second
   (the splash), and the app within about ten.
2. Open **Settings → Advanced** and confirm the API port and data folder.
3. Start L01 and press **Skip step** a few times — the lesson must advance
   without VOICEVOX, Ollama, a microphone or the book MP3s.
4. Close the window. No `jtutor-backend` process may remain after five seconds.
5. Launch twice; the second launch must focus the first window, not start a
   second backend.

## Recipient checklist

1. Run the installer.
2. Launch Jtutor.
3. Follow the in-app **Setup guide** for VOICEVOX, Ollama and the Irodori files.

That is the whole list. There is no `INSTALL.bat`, `START.bat` or `STOP.bat`
any more — the app supervises its own backend and shuts it down with the
window.
