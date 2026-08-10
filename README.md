# Jtutor

Local Japanese tutor for **Irodori: Japanese for Life in Japan** — **Starter (A1)** and **Elementary 1 (A2)**. Electron + FastAPI desktop app that walks the book in order, grades spoken answers, and unlocks lessons via can-do checks — not a free-form chat bot.

## Quick start (from this repo)

### 1. Prerequisites

| Tool | Version | Why |
|------|---------|-----|
| **Python** | 3.11+ | Backend (FastAPI, Whisper, curriculum) |
| **Node.js** | LTS (18+) | Electron UI and packaging |

Optional (app runs without them; you lose that feature):

| Service | Install | Gives you |
|---------|---------|-----------|
| **[VOICEVOX](https://voicevox.hiroshiba.jp/)** | Engine on `http://127.0.0.1:50021` | Yuki speaks aloud |
| **[Ollama](https://ollama.com/)** | Then `ollama pull qwen2.5:7b` | Ask Yuki answers |
| **Irodori PDFs + CD MP3s** | Your own legal copies (not in git) | Book pages + audio |

### 2. Clone and install

```bash
git clone https://github.com/<you>/Jtutor.git
cd Jtutor

# Python deps (use a venv if you prefer)
pip install -r backend/requirements.txt

# Node deps (root + desktop app)
npm install
npm install --prefix apps/desktop
```

**Windows tip:** If `python` is not on PATH, use `py -3 -m pip install -r backend/requirements.txt`.

### 3. Add Irodori materials (strongly recommended)

Jtutor does **not** ship Japan Foundation PDFs or audio. Put your copies here:

```text
assets/
  irodori_starter.pdf
  Grammar_Worksheets_X.pdf          # optional
  Elementary1.pdf                   # optional
  Grammar_Elementary_1.pdf          # optional
  audio/
    X_*.mp3                         # Starter CD tracks
    Y_*.mp3                         # Elementary 1 CD tracks
```

Official downloads: [irodori.jpf.go.jp](https://www.irodori.jpf.go.jp/).  
Filenames look like `X_[01-01]_kiku.mp3` / `Y_[01-01]_kaiwa1.mp3`.

### 4. Run the app

**Developers (hot reload, console):**

```bash
npm run dev
```

That starts:

1. FastAPI on `127.0.0.1:8765`
2. Vite on `5173`
3. Electron once both are up  

Close the Electron window to stop everything.

**Windows desktop shortcut (no console):**

```text
Double-click start_jtutor.bat
```

(or `npm run app`) — rebuilds the UI if needed, then opens Electron with the supervised backend.

### 5. First-launch checklist

1. Status dot in the title bar → **All services ready** (or open Setup and install what’s missing).
2. **Settings → Audio** → pick a microphone → Test.
3. Left rail → pick **Irodori Starter** or **Elementary 1** → open a lesson.
4. Hold / tap speak on graded steps; on a miss you’ll get **Hear the recording / Hear Yuki / Try again**.

Progress is stored locally (Electron: under your user AppData / Application Support).

---

## What it does

- **Book flow** — Listen & repeat, listen & choose, fill-in blanks, vocab, pronunciation, culture notes, kanji words (漢字のことば), dialog role-play.
- **Voice** — Official Irodori MP3s when present; tutor TTS via **VOICEVOX**; answers via **Whisper**.
- **Can-do gates** — Spoken quizzes unlock the next lesson.
- **Ask Yuki** — Mid-lesson help (does not advance the lesson); **Ollama** when available.
- **FSRS** — Spaced review from vocab and quiz gaps.

## Installer builds (end users)

Packaged builds bundle a frozen Python backend — the end user does **not** need Python:

```bash
npm run dist         # current platform
npm run dist:win     # Windows NSIS
```

See **[docs/DISTRIBUTE.md](docs/DISTRIBUTE.md)** and **[release/README.md](release/README.md)**.

## Docs

| Doc | Audience |
|-----|----------|
| **[docs/SETUP.md](docs/SETUP.md)** | Full developer setup, env vars, startup internals |
| **[release/README.md](release/README.md)** | Packaged installer users |
| **[docs/CURRICULUM_SCHEMA.md](docs/CURRICULUM_SCHEMA.md)** | Lesson YAML schema |
| **[docs/AUDIT.md](docs/AUDIT.md)** | Technical audit / roadmap |

## Tests

```bash
npm test             # vitest + pytest
npm run lint
npm run typecheck
```

## Content

- Generated YAML: `content/starter/` (**L00–L18**) and `content/elementary1/` (**EL01–EL18**).
- Switch books in the left rail.
- Rebuild helpers live under `scripts/` (scrapers, exercise upgrades, kanji/fill extractors).

Keep Japan Foundation materials in your own `assets/` folder only — never commit them.

## License & materials

App code is for personal/local use with legally obtained Irodori materials. Do not redistribute Japan Foundation PDFs or audio.
