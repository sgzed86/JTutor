# Jtutor setup (development)

End users install Jtutor from an installer and need nothing else — see
[release/README.md](../release/README.md). This page is for working on the code.

## Prerequisites

1. **Python 3.11+**
2. **Node.js LTS**
3. Optional at runtime: **[Ollama](https://ollama.com/)** (`ollama pull qwen2.5:7b`),
   **[VOICEVOX](https://voicevox.hiroshiba.jp/)** on `http://127.0.0.1:50021`,
   and your Irodori PDFs/MP3s under `assets/`.

The app runs without the optional three; you lose Ask Yuki answers, the tutor
voice and the book audio respectively.

## Install

```bash
pip install -r backend/requirements.txt
npm install
npm install --prefix apps/desktop
```

## Run

```bash
npm run dev
```

Starts the API (`127.0.0.1:8765`), Vite (`5173`) and the Electron window once
both are listening. Closing the window stops the whole tree.

Individually:

```bash
npm run dev:backend    # uvicorn with --reload
npm run dev:ui         # vite
npm run dev:electron   # electron against the dev servers
```

There are no `.bat` launchers any more. In development Electron talks to the
Vite dev server; in a packaged build it starts the frozen backend itself and
loads the UI the backend serves.

## How startup works

`apps/desktop/electron/backend.cjs` supervises the backend:

1. Sweeps an orphaned backend from a previous run (verified through a pid file
   plus a `/health` identity check, so it can never kill an unrelated process).
2. Picks a free loopback port and mints a per-run token.
3. Resolves the backend command: `JTUTOR_BACKEND_EXE` → the bundled
   `backend-dist/jtutor-backend` → `JTUTOR_PYTHON` → a probed `python3`/`python`/`py -3`
   that reports 3.11+.
4. Spawns it with stdout/stderr teed to `<userData>/logs/backend.log`.
5. Polls `/health` behind a splash window, then opens the main window. On
   failure it shows a dialog with the log tail and Retry / Open log / Quit.
6. Restarts the backend up to three times with backoff if it exits unexpectedly.
7. On quit: `POST /internal/shutdown` → `SIGTERM` → force kill, gated on
   `before-quit` so the app cannot exit ahead of its backend.

## Environment variables

| Variable | Default | Meaning |
|----------|---------|---------|
| `JTUTOR_ROOT` | repo root | Folder holding `content/` and `ui/` |
| `JTUTOR_DATA_DIR` | `<root>/data` | Database, logs, TTS cache (the app points this at per-user app data) |
| `JTUTOR_ASSETS_DIR` | `<root>/assets` | Irodori PDFs and MP3s |
| `JTUTOR_TOKEN` | unset | When set, API routes require `x-jtutor-token` |
| `JTUTOR_PYTHON` | — | Interpreter the supervisor should prefer |
| `OLLAMA_MODEL` | `qwen2.5:7b` | Ask Yuki model |
| `OLLAMA_URL` | `http://127.0.0.1:11434` | Ollama API |
| `VOICEVOX_URL` | `http://127.0.0.1:50021` | VOICEVOX engine |
| `SELECTED_SPEAKER_ID` | `2` | Default VOICEVOX style id |
| `WHISPER_MODEL` / `WHISPER_DEVICE` | `small` / `cpu` | faster-whisper size and device |
| `GRADING_STRICTNESS` | `standard` | `lenient` / `standard` / `strict` default |
| `LOG_LEVEL` | `INFO` | `DEBUG` for more detail |

Anything the user changes in **Settings** is stored in the database and
overrides these defaults at runtime.

## Tests

```bash
npm test          # vitest (UI) + pytest (backend)
npm run lint      # eslint + ruff
npm run typecheck # tsc --noEmit
```

The backend suite includes `tests/golden/`: a recorded transcript per lesson
covering every state, activity, sub-step and scripted line. A flow change that
alters progression fails these. Regenerate deliberately with
`JTUTOR_REGEN_GOLDENS=1 pytest tests/test_flow_golden.py` and review the diff.

## Debug log

The backend writes to `<data dir>/jtutor.log`; the supervisor additionally tees
the child's output to `<userData>/logs/backend.log`. **Settings → Advanced →
Open log folder** reveals it, or `GET /log/tail?lines=200`.

## API

The backend binds `127.0.0.1` on a port chosen at launch (`8765` in
development). API routes require `x-jtutor-token` when `JTUTOR_TOKEN` is set;
`/health`, `/` and `/assets/*` stay open so the window can load, and media URLs
accept `?token=` because `<audio src>` cannot send headers.

- `GET /health` — services, instance id, pid
- `GET /curriculum`, `GET /curriculum/{id}`
- `POST /tutor/{id}/start|advance|message|ask|self-check|reset|jump-can-do`
- `GET /settings`, `PATCH /settings`, `POST /settings/reset`
- `GET /media/audio?path=assets/audio/...`, `GET /media/pdf`
- `POST /voice/speak`, `POST /voice/transcribe`, `GET /voice/model-status`
- `GET /voice/speakers`, `POST /voice/set-speaker`
- `GET /srs/due`, `POST /srs/{id}/review`
- `POST /internal/shutdown` — used by the supervisor
