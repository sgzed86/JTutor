# Jtutor setup (from source)

This page is the full **clone → install → run** guide for developers working from GitHub.

End users who installed a packaged build: see [release/README.md](../release/README.md) (Python is bundled; nothing to start by hand).

---

## Prerequisites

### Required

1. **Python 3.11+** on your PATH (`python --version` or `py -3 --version` on Windows)
2. **Node.js LTS** (`node --version`, `npm --version`)

### Optional (recommended)

| Piece | Setup | Without it |
|-------|--------|------------|
| **VOICEVOX** | Install the engine; leave it running on `http://127.0.0.1:50021` | Yuki’s lines show as text only |
| **Ollama** | Install, then `ollama pull qwen2.5:7b` | Ask Yuki falls back to phrase hints |
| **Irodori assets** | Copy PDFs + MP3s into `assets/` (see below) | No textbook pages / CD audio |
| **Microphone** | Settings → Audio → Test | Speaking steps can’t be graded; use Skip |

The app starts even when optional pieces are missing. Use the **status dot** in the title bar (Setup guide) to see what’s down.

---

## Install (one-time)

From the repo root:

```bash
git clone <this-repo-url>
cd Jtutor

# 1) Python packages
python -m pip install -r backend/requirements.txt
# Windows alternate:  py -3 -m pip install -r backend/requirements.txt

# 2) Node packages (root Electron + React app)
npm install
npm install --prefix apps/desktop
```

Confirm:

```bash
python -c "import fastapi, faster_whisper, fitz; print('python ok')"
node -e "console.log('node', process.version)"
```

---

## Irodori files (not in git)

Place your legally obtained files under `assets/` at the repo root:

```text
assets/
  irodori_starter.pdf
  Grammar_Worksheets_X.pdf          # optional
  Elementary1.pdf                   # optional
  Grammar_Elementary_1.pdf          # optional
  audio/
    X_[01-01]_kiku.mp3              # Starter
    Y_[01-01]_kaiwa1.mp3            # Elementary 1
    …
```

Official site: https://www.irodori.jpf.go.jp/

In a **packaged** install, the assets folder is next to the app data directory (Settings → Advanced → open data folder). From source, use the repo’s `assets/`.

---

## Run

### Daily development (hot reload)

```bash
npm run dev
```

Starts three processes:

| Process | Address | Role |
|---------|---------|------|
| Backend | `http://127.0.0.1:8765` | FastAPI + Whisper + curriculum |
| Vite | `http://127.0.0.1:5173` | React UI |
| Electron | — | Desktop window (waits for both ports) |

Close the Electron window to tear everything down (`concurrently -k`).

Individually, if you need to:

```bash
npm run dev:backend
npm run dev:ui
npm run dev:electron
```

### Windows “normal app” launch (no console)

```text
start_jtutor.bat
```

or:

```bash
npm run app
```

Rebuilds `apps/desktop/dist` when sources are newer, then starts Electron with the supervised backend (same path a desktop shortcut would use).

---

## First-run checklist

1. Launch with `npm run dev` (or `start_jtutor.bat`).
2. Wait until the title-bar status shows services ready (VOICEVOX / Ollama may still be optional).
3. **Settings → Audio** — select mic → Test.
4. Left rail — choose book (Starter / Elementary 1) → open a lesson.
5. Speak on a graded step. On a miss you should see **Hear the recording**, **Hear Yuki say it**, and **Try again** (no auto CD replay).

---

## How startup works

`apps/desktop/electron/backend.cjs` supervises the backend:

1. Sweeps an orphaned backend from a previous run (pid file + `/health` identity).
2. Picks a free loopback port and mints a per-run token.
3. Resolves the backend command: `JTUTOR_BACKEND_EXE` → bundled `backend-dist/jtutor-backend` → `JTUTOR_PYTHON` → probed `python3` / `python` / `py -3` (3.11+).
4. Spawns it with stdout/stderr teed to `<userData>/logs/backend.log`.
5. Polls `/health`, then opens the main window. On failure: dialog with log tail + Retry / Open log / Quit.
6. Restarts the backend up to three times with backoff if it exits unexpectedly.
7. On quit: `POST /internal/shutdown` → `SIGTERM` → force kill.

In **dev**, Electron loads Vite (`5173`) and the supervisor still starts/stops the Python API. In a **packaged** build it starts the frozen backend and serves the built UI.

---

## Environment variables

| Variable | Default | Meaning |
|----------|---------|---------|
| `JTUTOR_ROOT` | repo root | Folder holding `content/` and `ui/` |
| `JTUTOR_DATA_DIR` | `<root>/data` | Database, logs, TTS cache (Electron uses per-user app data) |
| `JTUTOR_ASSETS_DIR` | `<root>/assets` | Irodori PDFs and MP3s |
| `JTUTOR_TOKEN` | unset | When set, API routes require `x-jtutor-token` |
| `JTUTOR_PYTHON` | — | Interpreter the supervisor should prefer |
| `OLLAMA_MODEL` | `qwen2.5:7b` | Ask Yuki model |
| `OLLAMA_URL` | `http://127.0.0.1:11434` | Ollama API |
| `VOICEVOX_URL` | `http://127.0.0.1:50021` | VOICEVOX engine |
| `SELECTED_SPEAKER_ID` | `2` | Default VOICEVOX style id |
| `WHISPER_MODEL` / `WHISPER_DEVICE` | `small` / `cpu` | faster-whisper size and device |
| `GRADING_STRICTNESS` | `standard` | `lenient` / `standard` / `strict` |
| `LOG_LEVEL` | `INFO` | `DEBUG` for more detail |

Settings in the UI override these at runtime (stored in the local DB).

---

## Common problems

| Symptom | Fix |
|---------|-----|
| `npm run dev` hangs on Electron | Confirm ports 5173 and 8765 are free; check Python deps installed |
| Backend won’t start / “Python not found” | Install 3.11+, or set `JTUTOR_PYTHON` to the interpreter path |
| Yuki silent | Start VOICEVOX; status popover → Check again |
| No book audio / blank PDF | Copy files into `assets/` (see above) |
| Empty lesson list in the rail | Backend failed to load curriculum — open log folder (Settings → Advanced) |
| Mic errors | Settings → Audio → pick device → Test |
| Whisper slow first answer | First model load downloads weights; later turns are faster |

Logs: **Settings → Advanced → Open log folder**, or `data/jtutor.log` in development.

---

## Tests & quality

```bash
npm test          # vitest (UI) + pytest (backend)
npm run lint      # eslint + ruff
npm run typecheck # tsc --noEmit
```

Golden flow transcripts: `tests/golden/`. Regenerate only deliberately:

```bash
JTUTOR_REGEN_GOLDENS=1 pytest tests/test_flow_golden.py
```

---

## Build an installer

```bash
npm run dist         # current platform
npm run dist:win     # Windows NSIS
```

Details: [DISTRIBUTE.md](DISTRIBUTE.md).

---

## API (local only)

Dev backend: `http://127.0.0.1:8765`. When `JTUTOR_TOKEN` is set, send `x-jtutor-token` (media URLs also accept `?token=`).

- `GET /health`
- `GET /curriculum`, `GET /curriculum/{id}`
- `POST /tutor/{id}/start|advance|message|ask|self-check|reset|jump-can-do`
- `GET /settings`, `PATCH /settings`
- `GET /media/audio`, `GET /media/pdf`
- `POST /voice/speak`, `POST /voice/transcribe`
- `GET /srs/due`, `POST /srs/{id}/review`
