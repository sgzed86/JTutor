# Distributing Jtutor

## Build the portable zip

From the repo root (your machine):

```powershell
npm run release
```

Output:

- `dist-release/Jtutor/` — unpacked portable app
- `dist-release/Jtutor-portable-win.zip` — **send this**

## What is included

- Backend (Python)
- Built UI
- Lesson curriculum YAML (Starter + Elementary 1)
- `INSTALL.bat` / `START.bat` / `STOP.bat`
- Empty `assets/` with instructions

## What is NOT included (on purpose)

- Irodori PDFs / MP3s (Japan Foundation copyright)
- Python packages (recipient installs via `INSTALL.bat`)
- Ollama / VOICEVOX (recipient installs separately)

## Recipient checklist

1. Python 3.11+ on PATH  
2. Unzip → `INSTALL.bat`  
3. Copy Irodori files into `assets\` (see `assets\README.txt`)  
4. Install/start [Ollama](https://ollama.com) + `ollama pull qwen2.5:7b`  
5. Install/start [VOICEVOX](https://voicevox.hiroshiba.jp/)  
6. `START.bat` → browser at http://127.0.0.1:8765  

## Optional Electron installer

```powershell
npm run dist
```

Produces an NSIS installer under `dist-electron/`. Still requires Python, Ollama, VOICEVOX, and local Irodori assets. Prefer the portable zip for most people.
