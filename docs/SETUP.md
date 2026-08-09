# Jtutor setup

Local-first Japanese tutor for **Irodori Starter (A1)** using Ollama, VOICEVOX, Whisper, and official lesson audio.

## Prerequisites

1. **Python 3.11+**
2. **Node.js LTS**
3. **[Ollama](https://ollama.com/)** — e.g. `ollama pull qwen2.5:7b`
4. **[VOICEVOX](https://voicevox.hiroshiba.jp/)** — engine listening on `http://127.0.0.1:50021`
5. Irodori materials in `assets/` (PDF + `assets/audio/*.mp3`) — already moved if you followed the project layout

## Install

```powershell
cd C:\Users\Zach\Desktop\Jtutor
pip install -r backend\requirements.txt
npm install
npm install --prefix apps\desktop
```

Optional: rebuild curriculum from PDFs/audio:

```powershell
python scripts\run_scrape.py
```

## Run (development)

**Easiest:** double-click `start_jtutor.bat` in the project folder (starts API + Vite and opens http://127.0.0.1:5173). For the Electron window instead, use `start_jtutor_electron.bat`.

If Vite says **port 5173 is already in use**, a previous dev server is still running — double-click `stop_jtutor.bat` or close the old **Jtutor UI** terminal window, then start again.

Or manually:

```powershell
$env:PYTHONPATH = (Get-Location).Path
$env:PYTHONIOENCODING = "utf-8"
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8765
```

Terminal 2 — UI:

```powershell
npm run dev --prefix apps\desktop
```

Open `http://127.0.0.1:5173`.

Or from Electron (spawns backend):

```powershell
npm run dev --prefix apps\desktop
# separate terminal:
npx electron .
```

## Environment variables

| Variable | Default | Meaning |
|----------|---------|---------|
| `OLLAMA_MODEL` | `qwen2.5:7b` | Chat / grading model |
| `OLLAMA_URL` | `http://127.0.0.1:11434` | Ollama API |
| `VOICEVOX_URL` | `http://127.0.0.1:50021` | VOICEVOX engine |
| `SELECTED_SPEAKER_ID` | `2` | Default VoiceVox style id (also set in Settings → Tutor Voice) |
| `VOICEVOX_SPEAKER` | `2` | Legacy alias for the default speaker id |
| `WHISPER_MODEL` | `small` | faster-whisper size |
| `WHISPER_DEVICE` | `cpu` | `cpu` or `cuda` |
| `LOG_LEVEL` | `INFO` | Set to `DEBUG` for more detail |

## Debug log

While the API runs, events are appended to **`data/jtutor.log`** (rotating, under the project folder). Includes tutor state changes, speech/transcribe, HTTP calls to `/tutor` and `/voice`, and UI pipeline steps.

- In the app: **Setup → Session log → Refresh log**
- Or open the file directly, or `GET http://127.0.0.1:8765/log/tail?lines=200`

Share the tail of this file when reporting tutor bugs.

## Packaging (Windows)

```powershell
npm run dist
```

Builds an NSIS installer via electron-builder. **Do not** redistribute `assets/` (Japan Foundation copyright). Point users at the official Irodori download and keep materials local.

## API

Backend binds **127.0.0.1:8765** only.

- `GET /health`
- `GET /curriculum`, `GET /curriculum/{id}`
- `POST /tutor/{id}/start|advance|message|ask|self-check|reset|jump-can-do`
- `GET /media/audio?path=assets/audio/...`
- `POST /voice/speak`, `POST /voice/transcribe`
- `GET /voice/speakers`, `POST /voice/set-speaker`, `GET /voice/settings`
- `GET /srs/due`, `POST /srs/{id}/review`
