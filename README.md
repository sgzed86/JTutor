# Jtutor

Local Japanese tutor for **Irodori: Japanese for Life in Japan** — **Starter (A1)** and **Elementary 1 (A2)**. Electron + FastAPI app that walks the book in order, grades spoken answers, and unlocks lessons via can-do checks—not a free-form chat bot.

## What it does

- **Book flow** — Activities in CD order: listen & repeat, picture-based “choose & say,” and role-play (partner vs learner lines, then role swap). Lesson 1 uses book-faithful modes; other lessons default to listen → repeat until extended in the curriculum builder.
- **Voice** — Official Irodori MP3s in-app; tutor lines via **VOICEVOX**; your answers via **Whisper** (push-to-talk).
- **Can-do gates** — Spoken role-play quizzes at the end of each lesson; pass counts unlock the next lesson.
- **Ask Yuki** — Mid-lesson questions (English or Japanese) without advancing the exercise; **Ollama** answers with lesson context.
- **FSRS** — Spaced repetition cards from vocab and quiz gaps.
- **Progress** — Dashboard and lesson map; optional jump to Can-do quiz for testing.

Tutor UI uses an animated **Yuki** avatar (speech bubble + clear “say this” card for the phrase you need).

## Prerequisites

**Python 3.11+**, **Node.js LTS**, **[Ollama](https://ollama.com/)** (e.g. `ollama pull qwen2.5:7b`), **[VOICEVOX](https://voicevox.hiroshiba.jp/)** on `http://127.0.0.1:50021`, and your own Irodori Starter PDFs/MP3s under `assets/` (gitignored—do not redistribute).

Full install details: **[docs/SETUP.md](docs/SETUP.md)**.

## Quick start (Windows)

1. Install dependencies (once):

   ```powershell
   pip install -r backend\requirements.txt
   npm install
   npm install --prefix apps\desktop
   ```

2. Start Ollama and VOICEVOX, then double-click **`start_jtutor.bat`** (API + Vite, opens http://127.0.0.1:5173).

   - Electron window: **`start_jtutor_electron.bat`**
   - Stop stray dev servers: **`stop_jtutor.bat`**

Or from the repo root:

```powershell
npm run dev
```

Runs API (`127.0.0.1:8765`) and UI (`5173`) together.

Manual split terminal commands are in [docs/SETUP.md](docs/SETUP.md).

## Content & curriculum

- Generated YAML: `content/starter/` (**L00–L18**) and `content/elementary1/` (**EL01–EL18**).
- Switch books in the app sidebar (Starter ↔ Elementary 1).
- Rebuild from local PDFs/audio:

  ```powershell
  # Starter
  python scripts/run_scrape.py

  # Elementary 1 (after placing Elementary1.pdf, Grammar_Elementary_1.pdf, and Y_*.mp3 under assets/)
  python scripts/run_scrape_elementary1.py
  ```

  Elementary 1 phrases are taken from the textbook dialog scripts (not Whisper).

  Optional fields and migration notes: [docs/CURRICULUM_SCHEMA.md](docs/CURRICULUM_SCHEMA.md).

- L01 phrase sanity check: `python scripts/verify_l01_phrases.py`

Keep Japan Foundation materials in **`assets/`** only on your machine.

## Debugging

While the API runs, events append to **`data/jtutor.log`**. In the app: **Setup → Session log**, or `GET http://127.0.0.1:8765/log/tail?lines=200`.

## Project layout

| Path | Role |
|------|------|
| `backend/app/` | FastAPI, tutor state machine, voice clients |
| `apps/desktop/` | React UI + Electron |
| `content/starter/` | Lesson YAML (generated) |
| `assets/` | Your Irodori PDFs/MP3s (local, gitignored) |
| `scripts/` | Scrape & curriculum build |

## API (local only)

Backend binds **`127.0.0.1:8765`**. Main routes:

| Area | Examples |
|------|----------|
| Health | `GET /health` |
| Curriculum | `GET /curriculum`, `GET /curriculum/{id}` |
| Progress | `GET /progress` |
| Tutor | `POST /tutor/{id}/start`, `/advance`, `/message`, `/ask`, `/reset`, `/jump-can-do` |
| Media | `GET /media/audio`, `GET /media/pdf` |
| Voice | `POST /voice/speak`, `POST /voice/transcribe` |
| SRS | `GET /srs/due`, `POST /srs/{id}/review` |
| Log | `GET /log/tail`, `POST /log/client` |

## Packaging (send to someone)

**Recommended — portable zip (no Node needed for the recipient):**

```powershell
npm run release
```

Creates `dist-release/Jtutor-portable-win.zip`. Send that zip.

Recipient:
1. Unzip
2. Run `INSTALL.bat` (needs Python 3.11+)
3. Put Irodori PDFs/MP3s in `assets\` (see `assets\README.txt`)
4. Start Ollama + VOICEVOX
5. Run `START.bat`

**Do not** put Japan Foundation PDFs/MP3s inside the zip you send.

Optional Electron NSIS installer (still needs Python on the PC):

```powershell
npm run dist
```

## License & materials

App code is for personal/local use with legally obtained Irodori materials. Do not redistribute Japan Foundation PDFs or audio.
