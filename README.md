# Jtutor

Local Japanese tutor for **Irodori: Japanese for Life in Japan** — **Starter (A1)** and **Elementary 1 (A2)**. Electron + FastAPI desktop app that walks the book in order, grades spoken answers, and unlocks lessons via can-do checks—not a free-form chat bot.

## What it does

- **Book flow** — Activities in CD order: listen & repeat, picture-based “choose & say,” and role-play (partner vs learner lines, then role swap).
- **Voice** — Official Irodori MP3s in-app; tutor lines via **VOICEVOX**; your answers via **Whisper** (push-to-talk with a live waveform and silence detection).
- **Can-do gates** — Spoken role-play quizzes at the end of each lesson; pass counts unlock the next lesson.
- **Ask Yuki** — Mid-lesson questions (English or Japanese) that never move the lesson; **Ollama** answers with lesson context.
- **FSRS** — Spaced repetition cards from vocab and quiz gaps.
- **Progress** — Lesson rail with per-lesson can-do state, plus a full progress page.

The window is one screen: lesson rail on the left, Yuki and the phrase you need in the middle, Ask Yuki / grammar notes / dialog script / vocabulary on the right, and a transport bar along the bottom that always holds the next action.

## Install (end users)

Run the installer and launch Jtutor. **Python is bundled** — there is nothing to
install, start or stop by hand.

Optional local services add features; the app works without them and the
in-app **Setup guide** (click the status dot in the title bar) explains what
each one gives you:

- **[VOICEVOX](https://voicevox.hiroshiba.jp/)** — Yuki's voice
- **[Ollama](https://ollama.com/)** (`ollama pull qwen2.5:7b`) — Ask Yuki answers
- Your own Irodori PDFs/MP3s in the app's `assets` folder — book audio

See **[release/README.md](release/README.md)** for the end-user guide.

## Run from source (developers)

```bash
pip install -r backend/requirements.txt
npm install
npm install --prefix apps/desktop

npm run dev      # FastAPI + Vite + Electron together
```

`npm run dev` starts the API on `127.0.0.1:8765`, Vite on `5173`, and the
Electron window once both are up. Closing the window stops everything.

Details: **[docs/SETUP.md](docs/SETUP.md)**.

## Build an installer

```bash
npm run dist         # current platform
npm run dist:win     # Windows NSIS
```

This freezes the backend with PyInstaller (`npm run build:backend`), builds the
UI, and packages both with electron-builder. The result needs no Python on the
target machine. See **[docs/DISTRIBUTE.md](docs/DISTRIBUTE.md)**.

## Tests

```bash
npm test             # vitest + pytest
npm run lint         # eslint + ruff
npm run typecheck    # tsc --noEmit
```

`tests/golden/` holds a recorded transcript for every lesson: the exact
sequence of states, activities, sub-steps and scripted lines a learner walks
through. Any change to the tutor flow has to reproduce them, which is how
deterministic progression is protected. Regenerate deliberately, and review the
diff, with `JTUTOR_REGEN_GOLDENS=1 pytest tests/test_flow_golden.py`.

## Planned work

The UI/UX audit and the redesign, startup and architecture plans this app was
rebuilt from live in **[docs/redesign/](docs/redesign/README.md)**.

## Content & curriculum

- Generated YAML: `content/starter/` (**L00–L18**) and `content/elementary1/` (**EL01–EL18**).
- Switch books in the left rail.
- Rebuild from local PDFs/audio:

  ```bash
  python scripts/run_scrape.py                # Starter
  python scripts/run_scrape_elementary1.py    # Elementary 1
  ```

  Optional fields and migration notes: [docs/CURRICULUM_SCHEMA.md](docs/CURRICULUM_SCHEMA.md).
  Every lesson is validated against `backend/app/schema.py` in CI.

Keep Japan Foundation materials in your own `assets/` folder only.

## Debugging

Backend output goes to a rotating log in the app's data folder; **Settings →
Advanced → Open log folder** reveals it. In development the backend also logs to
`data/jtutor.log`.

## Technical audit

Full-stack review of the state machine, voice pipeline, curriculum generation, and UI, with a prioritized improvement roadmap: **[docs/AUDIT.md](docs/AUDIT.md)**.

## Project layout

| Path | Role |
|------|------|
| `backend/app/` | FastAPI, tutor state machine, speech services |
| `backend/main_frozen.py` | Entry point for the packaged backend |
| `apps/desktop/src/` | React UI |
| `apps/desktop/electron/` | Electron main process + backend supervisor |
| `packaging/` | PyInstaller spec |
| `content/` | Lesson YAML (generated) |
| `tests/` | Golden transcripts, grading, schema and API contract tests |
| `scripts/` | Scrape & curriculum build |

## API (local only)

The backend binds `127.0.0.1` on a port the app picks at launch, and requires a
per-run token on API routes. Main routes:

| Area | Examples |
|------|----------|
| Health | `GET /health` |
| Curriculum | `GET /curriculum`, `GET /curriculum/{id}` |
| Progress | `GET /progress` |
| Tutor | `POST /tutor/{id}/start`, `/advance`, `/message`, `/ask`, `/reset`, `/self-check`, `/jump-can-do` |
| Settings | `GET /settings`, `PATCH /settings` |
| Media | `GET /media/audio`, `GET /media/pdf` |
| Voice | `POST /voice/speak`, `/voice/transcribe`, `GET /voice/model-status` |
| SRS | `GET /srs/due`, `POST /srs/{id}/review` |

## License & materials

App code is for personal/local use with legally obtained Irodori materials. Do not redistribute Japan Foundation PDFs or audio.
