# 05 — Prioritized roadmap and actionable tasks

Three delivery waves, then a numbered backlog split by area.

**On sizing:** each item is scoped by *what it touches, how invasive it is, and
what it depends on* rather than by calendar estimate. Wall-clock time depends
entirely on who is working and how much of it is parallel, and a day/week number
here would be noise. Waves are ordered by value-per-unit-risk, not duration.

---

## Wave 1 — Make it correct and unblock everything else

Everything here is either a user-visible blocker or a prerequisite that later
work depends on. Nothing in this wave changes lesson semantics.

### 1.1 Safety net first

| Item | Scope |
|------|-------|
| Golden transcripts for all 37 lessons | New `tests/` package; touches nothing in `backend/app`. Prerequisite for every refactor in Waves 2–3 |
| Grading table tests pinning `phrase_grade` behaviour | Single new test module |
| Content schema validation over all 37 YAML files | New `schema.py` + test; must pass unchanged on day one |
| CI: `ruff`, `tsc --noEmit`, `pytest` | New `.github/workflows/ci.yml`; no product code |

### 1.2 Startup that does not crash

| Item | Scope |
|------|-------|
| `BackendSupervisor` (free port, token, spawn, log tee, health, restart, orphan sweep, graceful stop) | New `electron/backend.cjs`; rewrite of `electron/main.cjs`; small `preload.cjs` and `api.ts` changes |
| Splash window + startup failure dialog + `did-fail-load` page | Two new HTML files, wired in `main.cjs` |
| Single-instance lock | Three lines in `main.cjs` |
| Delete `start_jtutor_electron.bat`, `stop_jtutor.bat`, `scripts/*.bat`; rewrite the quick start | Docs + file removal |

Depends on nothing. Removes audit pain points 1, 2 and the `stop_jtutor.bat`
reason entirely.

### 1.3 Stop the backend blocking itself

| Item | Scope |
|------|-------|
| `TranscriptionService` with a single-worker thread pool, warmed from `lifespan` | `whisper_service.py` → `speech/stt.py`; one route change |
| `GET /voice/model-status` + UI "preparing speech recognition" state | New route, one component |
| TTS disk cache + one shared text normalization | `voicevox_client.py` → `speech/tts.py`; delete `speakableText` from the client |
| Replace `@app.on_event("startup")` with `lifespan` | `main.py` |

### 1.4 Honest, non-contradictory tutor state

| Item | Scope |
|------|-------|
| `TutorPhase` union + `useTutorMachine`; one status string, one avatar mood, one primary action | New hooks; `Tutor.tsx` and `TutorStage.tsx` |
| Self-describing step payload (`substeps`, `substep_index`, `auto_advance`, `expects_speech`, `graded`) | `lesson_flow.py` step dicts (additive); client deletes its hardcoded list |
| Fix Ask Yuki advancing the lesson: mark help payloads `kind: "help"`; client ignores `auto_advance`/`play_audio` on them | Payload flag + one branch in the phase machine. A correctness bug, not polish |
| Error taxonomy: severity, retry action, auto-clear on next success | `ErrorToast` component; backend problem envelope |
| Fixed transport bar with a stable primary action | New `transport/` components; layout change only |

### 1.5 Recording feedback

| Item | Scope |
|------|-------|
| `useRecorder` with `AnalyserNode`, canvas waveform, elapsed timer | New hook + component; replaces both recorder implementations |
| VAD auto-stop, noise-floor calibration, "I didn't hear anything" state | Same hook |
| Explicit `getUserMedia` constraints (16 kHz mono, AGC, NS) | Same hook |
| Mic pre-flight check | New settings section + onboarding step |

---

## Wave 2 — Make it feel like a product

Layout, settings, avatar and the packaging that removes the Python prerequisite.

### 2.1 The three-pane shell

| Item | Scope |
|------|-------|
| `AppShell` grid, title bar, collapsible context panel, responsive drawers | New `shell/`; `App.tsx` rewritten; `styles.css` split |
| Left rail: Today card, grouped lesson list, review card | New `rail/`; replaces `Dashboard` and `ProgressMap` as the primary surface |
| Context panel with Ask Yuki / Notes / Script / Words tabs | New `context/`; all four data sources already ship |
| Center stage recomposition: `StepHeader`, `Instruction`, `FocusCard`, `GradeResult` | Consolidates `say-target-card`, `shadow-card`, `ModeCard`, `tutor-picture-hint` |

### 2.2 Design system

| Item | Scope |
|------|-------|
| Token set, CSS Modules, delete 50 inline styles | Every component, mechanical |
| Light theme + system preference | `themes.css`; depends on tokens |
| Self-host the fonts, drop the Google Fonts link | `index.html` + `public/fonts/` |
| Motion system with `prefers-reduced-motion` | `tokens.css` + component transitions |

### 2.3 Unified settings

| Item | Scope |
|------|-------|
| `GET`/`PATCH /settings` on the existing `SettingRow` table | New route + service |
| `SettingsDialog` with Voice / Audio / Appearance / Lessons / Ask Yuki / Advanced | New `settings/`; replaces `pages/Settings.tsx` |
| Audio device selection (input + output) wired through the pipeline | Depends on 1.5 and the audio pipeline |
| Auto-advance mode + interruptible countdown | Client-only; server still decides *whether* a step may auto-advance |
| Grading strictness → `pass_threshold` (can-do thresholds stay fixed) | `grading/policy.py` + settings plumbing |
| Developer-tools switch hiding the can-do jump buttons | Transport overflow |

### 2.4 Avatar system

| Item | Scope |
|------|-------|
| Re-author as layered SVG (or one sprite atlas), 1.07 MB → <150 KB | New `stage/Avatar/`; asset work |
| Six moods including `celebrating` and `encouraging` | Same |
| Amplitude-driven lip sync from the shared `AnalyserNode` | Depends on the audio pipeline |

### 2.5 No-Python packaging

| Item | Scope |
|------|-------|
| `backend/main_frozen.py` + PyInstaller spec (one-folder) | New files; hidden-import discovery is the main unknown |
| CI build matrix (Windows first, then macOS, Linux) | Workflow + signing secrets |
| `electron-builder` config: frozen backend as `extraResources`, mac/linux targets | `package.json` |
| `JTUTOR_DATA_DIR` / `JTUTOR_ASSETS_DIR`, defaulting to Electron `userData` | `config.py` + supervisor |
| Whisper model strategy (ship `base`, download larger on demand with progress) | Route + onboarding UI |
| Retire `release/*.bat` and `make_release.ps1` | Docs + file removal |

### 2.6 Ask Yuki that does not freeze the app

| Item | Scope |
|------|-------|
| Streaming `/tutor/{id}/ask` (Ollama `stream: true`, SSE) | Route + `ollama_client` |
| Separate `help_messages` channel | Payload change; context panel consumes it |
| Cancel button, pre-flight when Ollama is down, answer cache | Route + hook |
| Scoped busy state so the stage stays interactive | `useTutorMachine` |

### 2.7 Onboarding

| Item | Scope |
|------|-------|
| Four-step setup wizard (Ollama, VOICEVOX, materials, microphone) with live checks and skip-with-consequences | New `onboarding/`; replaces `pages/Setup.tsx` |
| Service indicator popover with per-service purpose and fix action | `shell/ServiceIndicator` |

---

## Wave 3 — Deepen the learning experience

Only start these once Waves 1–2 are stable; several depend on the refactors.

| Item | Scope |
|------|-------|
| `LessonPhase` registry replacing the three `if/elif` ladders | Invasive inside `orchestrator.py`; gated entirely on the golden transcripts from 1.1 |
| `BookSubStep` base class; `speech_substeps`/`auto_advance_substeps` derived from one table | Invasive inside `lesson_flow.py`; same gate |
| Pydantic response models + generated TypeScript client types | Backend routes + a codegen step; removes 54 `any`s |
| Session segments and "pause here" boundaries | Payload `segment` field + rail/stage UI |
| Rich grade feedback: transcript, character diff, "hear me" / "hear it again", attempt history | `GradeResult` + a small payload addition |
| Per-activity segmented progress | Depends on `substeps` from 1.4 |
| Grammar and vocabulary activity types getting their own modes (202 activities currently forced through listen-and-repeat) | New sub-steps + curriculum regeneration; additive to `FLOW_BY_MODE` |
| Furigana / romaji toggles using `phrase_meta.readings` | Schema addition + renderer |
| SRS integrated into the lesson end instead of a separate destination | Rail + flow |
| Accessibility pass: focus traps, `aria-live`, keyboard shortcuts, contrast audit | Cross-cutting |
| Auto-update via `electron-updater` | Depends on 2.5 |
| Playwright end-to-end suite | Depends on the stable component tree |

---

## Actionable task backlog

Each task is independently reviewable. `→` marks dependencies.

### Backend

| # | Task | Files |
|---|------|-------|
| B01 | Golden-transcript harness and fixtures for all 37 lessons | `tests/golden/`, `tests/test_flow_golden.py` |
| B02 | Grading table tests pinning current `phrase_grade` verdicts | `tests/test_grading.py` |
| B03 | Pydantic curriculum schema; validate all 37 files in CI | `backend/app/schema.py`, `tests/test_content_schema.py` |
| B04 | `TranscriptionService`: single-worker pool, warm on startup, `language` parameter, status API | `speech/stt.py`, `routes/voice.py` |
| B05 | `SpeechService`: disk-backed TTS cache, one normalization, `speed`/`pitch` passthrough | `speech/tts.py`, `speech/text.py` |
| B06 | Replace `on_event("startup")` with `lifespan`; warm Whisper and the TTS cache there | `main.py` |
| B07 | Self-describing step payload (`substeps`, `substep_index`, `auto_advance`, `expects_speech`, `graded`, `audio[].duration_s`, `audio[].transcript`, `segment`) — additive | `lesson_flow.py`, `book_modes.py` |
| B08 | Problem-envelope error responses with `code`/`hint`/`retryable`; fix all `B904` | `routes/*`, new `errors.py` |
| B09 | `GET`/`PATCH /settings` over `SettingRow`, typed | `routes/settings.py`, `services/settings.py` |
| B10 | `GradingPolicy` with strictness levels; delete `hybrid_grade`; keep can-do thresholds fixed | `grading/policy.py` → B02 |
| B11 | Streaming `/tutor/{id}/ask` with cancellation, pre-flight and answer cache | `routes/tutor.py`, `ollama_client.py` |
| B12 | Split help replies into `help_messages` | `orchestrator.py` → B07 |
| B13 | Stable `TutorPayload` response models; always include `self_checks` | `orchestrator.py`, `routes/tutor.py` |
| B14 | Token auth dependency; restrict CORS to the app origin | `main.py`, `deps.py` |
| B15 | `JTUTOR_DATA_DIR` / `JTUTOR_ASSETS_DIR`; `port = 0` means supervisor-assigned | `config.py` |
| B16 | `POST /internal/shutdown` (token-guarded) and an instance id in `/health` | `main.py`, `routes/health.py` |
| B17 | Delete dead code and unused imports; wire `ruff` into CI | `book_modes.py`, `lesson_flow.py`, `orchestrator.py`, `free_response.py` |
| B18 | Lazy `_UI_DIR` resolution | `main.py` |
| B19 | Replace the four silent `except Exception: pass` blocks with logged warnings | `voicevox_client.py`, `db.py`, `curriculum_loader.py` |
| B20 | `LessonPhase` protocol + registry replacing the three state ladders | `flow/` → B01 |
| B21 | `BookSubStep` base class; derive `speech_substeps`/`auto_advance_substeps` | `flow/substeps/` → B01, B20 |
| B22 | `GET /voice/model-status`, `POST /voice/download-model` with progress | `routes/voice.py` → B04 |
| B23 | Shared curriculum writer so both generators emit the full schema | `scripts/build_curriculum*.py` → B03 |
| B24 | Mark help payloads `kind: "help"`; contract test that `/ask` yields nothing the client can treat as a transition | `orchestrator.py`, `tests/test_api_contract.py` |

### Frontend

| # | Task | Files |
|---|------|-------|
| F01 | `strict` + `noImplicitAny`; generate types from OpenAPI | `tsconfig.json`, `api/types.gen.ts` → B13 |
| F02 | `useTutorSession` — all API calls, typed, `AbortController` per request | `state/useTutorSession.ts` |
| F03 | `useTutorMachine` — the `TutorPhase` union; one status, one mood, one action | `state/useTutorMachine.ts` → F02 |
| F04 | `useAudioPipeline` — one `AudioContext`, queue, prefetch, cancel, level, `setSinkId`, rate | `audio/useAudioPipeline.ts` |
| F05 | `useRecorder` — one recorder, analyser, VAD, calibration, device selection | `audio/useRecorder.ts` |
| F06 | Canvas waveform + elapsed timer + silence indicator | `audio/waveform.ts`, `transport/WaveformMeter.tsx` → F05 |
| F07 | `TransportBar` with a fixed primary action and an overflow menu | `transport/` → F03 |
| F08 | Delete the client's auto-advance list and second label map | `pages/Tutor.tsx`, `lib/tutorDisplay.ts`, `components/ModeCard.tsx` → B07 |
| F08b | Ignore `auto_advance` / `play_audio` on `kind: "help"` payloads so Ask Yuki cannot advance the lesson | `state/useTutorMachine.ts` → B24 |
| F09 | `ErrorToast` with severity, retry and auto-clear | `feedback/ErrorToast.tsx` → B08 |
| F10 | `AppShell` three-pane grid with responsive drawers | `shell/AppShell.tsx` |
| F11 | Left rail: `TodayCard`, grouped `LessonList`, `ReviewCard` | `rail/` |
| F12 | `ContextPanel` with Ask Yuki / Notes / Script / Words | `context/` → B12 |
| F13 | Stage recomposition: `StepHeader`, `Instruction`, `FocusCard`, `GradeResult` | `stage/` → F03 |
| F14 | Token set + CSS Modules; remove 50 inline styles | all components |
| F15 | Light theme and system preference | `styles/themes.css` → F14 |
| F16 | Self-host fonts; drop the Google Fonts link | `index.html`, `public/fonts/` |
| F17 | `SettingsDialog` with six sections | `settings/` → B09 |
| F18 | Layered-SVG avatar with six moods | `stage/Avatar/` |
| F19 | Amplitude-driven lip sync | `stage/Avatar/` → F04, F18 |
| F20 | Setup wizard replacing `pages/Setup.tsx` | `onboarding/` |
| F21 | `ServiceIndicator` popover with purpose and fix actions | `shell/` |
| F22 | Rich grade feedback: transcript, character diff, hear-me/hear-it | `stage/GradeResult.tsx` |
| F23 | Segmented per-activity progress | `stage/StepHeader.tsx` → B07 |
| F24 | Session segments and "pause here" | `rail/`, `stage/` → B07 |
| F25 | Error boundary around the stage; `useHealth` polling | `state/useHealth.ts` |
| F26 | Accessibility pass: focus traps, `aria-live`, `Space` to record, contrast | cross-cutting |
| F27 | Vitest + React Testing Library coverage for the phase table | `src/**/*.test.ts` |

### Electron

| # | Task | Files |
|---|------|-------|
| E01 | `BackendSupervisor`: resolve command, free port, token, spawn, log tee | `electron/backend.cjs` |
| E02 | Health gating, splash window, startup failure dialog | `electron/main.cjs`, `splash.html`, `error.html` |
| E03 | Crash restart with backoff and a "Reconnecting…" signal to the renderer | `electron/backend.cjs` → E01 |
| E04 | Deterministic shutdown: `/internal/shutdown` → SIGTERM → force kill; `before-quit` gating | `electron/main.cjs` → B16 |
| E05 | Orphan sweep via a pid file with identity verification | `electron/backend.cjs` → E01 |
| E06 | `requestSingleInstanceLock` + `second-instance` focus | `electron/main.cjs` |
| E07 | Preload: dynamic `apiBase`, token, `openLogs`, `restartBackend`, `platform` | `electron/preload.cjs` → E01 |
| E08 | `did-fail-load` → bundled error page | `electron/main.cjs` |
| E09 | Explicit media-permission handler for microphone access | `electron/main.cjs` |
| E10 | Native menu, `Ctrl/Cmd+,` for settings, standard edit shortcuts | `electron/menu.cjs` |
| E11 | Remove `start_jtutor*.bat`, `stop_jtutor.bat`, `scripts/*.bat` | repo root, `scripts/` → E01–E06 |

### Packaging

| # | Task | Files |
|---|------|-------|
| P01 | `backend/main_frozen.py` argparse entry point using `uvicorn.run(app, …)` | `backend/main_frozen.py` |
| P02 | PyInstaller one-folder spec with hidden imports and data files | `packaging/jtutor-backend.spec` → P01 |
| P03 | Frozen-backend smoke test in CI (health, tutor start, transcribe fixture) | `.github/workflows/build.yml` → P02 |
| P04 | `electron-builder` config: frozen backend in `extraResources`, drop `backend/` source, add mac/linux targets | `package.json` → P02 |
| P05 | Whisper model strategy: ship `base`, download larger with progress | → B22 |
| P06 | Windows code signing; document SmartScreen behaviour | CI secrets, `docs/DISTRIBUTE.md` |
| P07 | macOS notarization | CI |
| P08 | Retire `release/*.bat` and `make_release.ps1`; rewrite `docs/DISTRIBUTE.md` | `release/`, `scripts/`, docs |
| P09 | `electron-updater` against GitHub Releases | `package.json`, `main.cjs` → P04 |
| P10 | Rewrite `README.md` and `docs/SETUP.md` around the installer, with a build-from-source section | docs → E11, P04 |

---

## Definition of done for the whole programme

- A non-technical user installs Jtutor from one installer, launches it from a
  shortcut, completes the setup wizard, and finishes lesson L01 without ever
  seeing a terminal, a batch file or a stack trace.
- Closing the window always leaves zero Jtutor processes running.
- At every moment during a lesson, the screen states exactly one thing about
  what the tutor is doing, and it is true.
- Every lesson in `content/` produces a step-for-step identical transcript to the
  pre-refactor golden files.
- `ruff`, `mypy`, `tsc --noEmit`, `pytest` and `vitest` all pass in CI on every
  pull request.
