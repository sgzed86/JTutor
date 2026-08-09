# Jtutor — technical audit and improvement roadmap

Full-stack review of the Electron + FastAPI Irodori tutor: backend state machine, voice
pipeline, curriculum generation, React UI, and cross-cutting architecture.

Everything in this document was checked against the code at commit `3c1143c`, and the
numbers come from actually running the backend rather than from reading it. The probe
harness drove `backend.app.orchestrator` directly against a scratch SQLite database with
VOICEVOX, Whisper, and Ollama offline, which is also the degraded mode most bugs show up
in. Measurements were taken on this machine (Python 3.12, CPU only); treat the absolute
milliseconds as indicative and the ratios as the real signal.

## Contents

1. [Executive summary](#1-executive-summary)
2. [Backend audit](#2-backend-audit)
3. [Frontend audit](#3-frontend-audit)
4. [Curriculum pipeline audit](#4-curriculum-pipeline-audit)
5. [Overall architecture](#5-overall-architecture)
6. [Missing Irodori pedagogical steps](#6-missing-irodori-pedagogical-steps)
7. [Code smells and anti-patterns](#7-code-smells-and-anti-patterns)
8. [Prioritized roadmap](#8-prioritized-roadmap)
9. [Specific actionable suggestions](#9-specific-actionable-suggestions)
10. [Recommended refactors](#10-recommended-refactors)
11. [Highest-ROI work for the next cycle](#11-highest-roi-work-for-the-next-cycle)

---

## 1. Executive summary

The architecture is sound and the deterministic, book-ordered design is the right call for
this product. The state machine walks Lesson 1 end to end without a single wrong turn, the
`book_mode` → substep table is a genuinely good abstraction, and freezing lesson position
during Ask Yuki is handled deliberately and correctly.

The problems are concentrated in three places, and they are the same three places a
learner actually touches every minute.

**Grading is the most serious issue and it is not a tuning problem — it is directionally
wrong.** Pure string similarity has no notion of Japanese meaning, so it accepts answers
that mean the opposite of the target and rejects the polite/casual pairs Irodori explicitly
teaches:

| Learner said | Target | Similarity | Result |
|---|---|---|---|
| わかります | わかりません | 77.1 | **passes** (negation inverted) |
| 肉が好きです | 魚が好きです | 93.3 | **passes** (wrong noun, the entire point of the drill) |
| ビール | ビル | 100.0 | **passes** (long vowel stripped by the normalizer) |
| ありがとう | ありがとうございます | 53.3 | **fails** (correct casual form of a taught pair) |

Because `mastery_min_score` is only enforced on the Ollama path, and the Ollama path is
skipped whenever the model is unavailable, a single sloppy utterance can master a Can-do
and unlock the next lesson. Every heuristic pass is also reported to the learner as `100%`
regardless of the underlying similarity, so the feedback is not just lenient, it is untrue.

**Lesson gating does not exist on the server.** `start_or_resume` only checks the unlock
rule when a `LessonProgress` row already exists, and no row exists for a lesson the learner
has never opened. Navigating to `/tutor/L18` on a fresh install serves a full session. The
lock is a frontend `disabled` attribute on a `<select>`.

**The learner can get stuck with no way out.** Pressing "Skip / next step" through the
Can-do quiz cycles `1 → 2 → 0 → 1 → 2 → 0 …` forever, because reaching the end without
mastery silently resets `quiz_index` to 0 and re-asks Can-do 1 with no explanation. The
only escapes are passing every Can-do or "Restart lesson", which throws the session away.

Beyond correctness, the two big performance items are that lesson YAML is re-parsed from
disk on every request (~25–30 ms a parse, and `GET /progress` does 19 of them for a
**515 ms** response on a page the UI loads three times), and that the tutor payload
carries the entire transcript on every turn (**89 KB / 221 messages** by the end of L16).

Finally, the generated curriculum for L03–L18 is derived from Whisper transcripts of the
CDs and much of it is not usable as graded content — whole multi-sentence utterances with
the track number glued to the front are stored as single "key phrases", and those same
strings are seeded into SRS as flashcards.

**Verdict:** no rewrite is warranted. Roughly 80% of the user-visible value sits in
grading, the two soft-locks, a curriculum-quality pass, and caching — all of which are
contained changes inside existing modules.

---

## 2. Backend audit

### 2.1 Tutor state machine and mode architecture

**What works.** `book_modes.FLOW_BY_MODE` maps a mode name to an ordered substep list, and
`flow_substeps()` expands `listen_repeat_all` into one graded repeat per phrase. That is
the correct shape for this problem: adding a mode is a table entry plus a branch in
`lesson_flow.book_step()`, not a new state. Progression is fully deterministic —
`pick_quiz_scenario()` indexes by pass count rather than sampling randomly, so a given
learner history always produces the same scenario.

**`quiz_index` is one column with six meanings.** Depending on `state` it indexes book
substeps, intro questions, grammar points, or Can-dos:

```
lesson_intro     → unused
intro_chat       → index into lesson.intro_questions
book             → index into book_modes.flow_substeps(activity)
grammar          → index into grammar points
can_do_quiz      → index into lesson.can_dos
self_check       → index into lesson.can_dos
lesson_complete  → unused
```

This is the root cause of several other findings. It is why `_sync_book_substep()` exists
at all — that function re-derives `quiz_index` by walking backwards through the message log
looking at `step.book_flow_index`, then `step.book_substep`, then guessing from
`expect_speech`. Reconstructing authoritative state from a rendered transcript is a strong
signal the column is not trustworthy, and the fallback branch (`session.quiz_index =
max(session.quiz_index, 1)`) can silently place a resumed session on the wrong substep.

**Lesson locking is unenforced.** In `orchestrator.start_or_resume`:

```python
lp = db.get(LessonProgress, lesson_id)
if lp and not is_lesson_unlocked(db, lesson_id):
    return {"error": "Lesson locked. …", "locked": True}
```

The `lp and` guard means the check is skipped for any lesson without a progress row, which
is every lesson the learner has not already opened. Verified against L05, L18, and EL09 on
a fresh database: `is_lesson_unlocked` returns `False` and a full session is served anyway.
The same omission applies to `/tutor/{id}/advance`, `/message`, `/ask`, and `/jump-can-do`,
none of which check unlock state at all.

**The Can-do quiz can loop forever.** In `advance`, when `quiz_index` passes the last
Can-do and `check_lesson_mastery` returns `False`, the code sets `quiz_index = 0` and
re-prompts. Ten consecutive `advance` calls on L03 produced
`[1, 2, 0, 1, 2, 0, 1, 2, 0, 1]` and never reached `lesson_complete`. Gating here is
intentional and correct; the failure is that it is *silent* — no message explains which
Can-dos are still outstanding, and the progress bar visibly snaps backwards.

**Two divergent step resolvers.** `_resolve_step()` and `_lesson_step_snapshot()` both
answer "what step is the learner on", and they do not cover the same states:
`_lesson_step_snapshot` handles `can_do_quiz`, `grammar`, and `lesson_intro`;
`_resolve_step` does not, and falls through to "whatever step was attached to the last
non-help assistant message". It currently produces the right answer by luck. Any new state
will need to be added to both.

**`jump_to_can_do_quiz` destroys the transcript.** It assigns `messages: list[dict] = []`
and overwrites the session. Measured: 8 messages before the jump, 1 after. This is exposed
in the main learner UI as two always-visible buttons ("Jump to Can-do quiz" and "Can-do
(reset progress)"), so a debugging affordance is one mis-tap away from discarding a lesson.

**L00 has no content path.** `flow.book_tracks()` filters out `kind in {"classroom",
"script"}`, and every one of L00's five activities is `kind: classroom`. So `book_tracks()`
returns 0, the lesson skips straight through `grammar` to `lesson_complete` in two
`advance` calls, and the classroom-Japanese audio is never played. The lesson is listed on
the dashboard and the progress map as real content.

**Ungraded grammar step.** The `grammar` branch of `user_message` accepts anything at all:

```python
reply = flow.feedback_pass_short() if len(text.strip()) >= 2 else flow.feedback_retry([])
```

Two characters of any script earns よくできました。 The grammar phase also only reads the
`point` string aloud — no examples, no audio, no worksheet reference beyond a page number.

### 2.2 Voice pipeline (VOICEVOX + Whisper)

**Whisper blocks the event loop.** `routes/voice.py::transcribe` is `async def` and calls
the synchronous, CPU-bound `whisper_service.transcribe_file()` directly. FastAPI runs
`async def` handlers on the event loop itself, so for the entire duration of a decode —
seconds on CPU with the `small` model — no other request is served, including `/health`,
`/tutor/*`, and `/voice/speak`. A simulated 300 ms blocking call inside a handler produced
a 300 ms stall in a concurrent heartbeat task while all other iterations ran at their
scheduled 50 ms. The fix is one keyword: drop `async`, and FastAPI will run it in the
threadpool.

**No Whisper tuning at all.** `transcribe_file` passes only `language="ja"`. Everything
else is library default:

| Option | Status |
|---|---|
| `vad_filter` | not set — leading/trailing silence is decoded |
| `beam_size` | not set (default 5, ~2× slower than greedy for short utterances) |
| `condition_on_previous_text` | not set — encourages hallucinated continuations |
| `initial_prompt` | not set — no lesson vocabulary biasing |
| `no_speech_threshold` | not set |
| `without_timestamps` | not set — timestamps computed and discarded |

There is also no warm-up: the model loads lazily on the first transcription, so the
learner's first utterance of a session pays the full model-load cost, and `whisper_status()`
reports `ok: true` before anything has ever been loaded because `_import_error` is still
`None`. The UI compounds this — `Dashboard` renders `health?.whisper ? "ok" : "bad"` on a
dict that is always truthy, and `Setup` hardcodes `className="pill ok"`. **The Whisper
indicator is green even when `faster-whisper` is not installed**, so the first failure the
learner sees is a 500 from `/voice/transcribe` on their first spoken answer.

**VOICEVOX re-synthesises the same lines dozens of times.** Walking L01 to completion
produces **159 tutor utterances of which only 54 are unique** — 105 redundant synthesis
round trips in a single lesson:

```
 42x  よくできました。
 15x  えを 見て、ききましょう。CDを きいてください。
 15x  どんな あいさつ ですか。日本語で いってください。
 11x  会話を ききましょう。CDを きいてください。
 11x  シャドーイングしましょう。CDに 合わせて、小声で いってください。
```

Nothing is cached, and `synthesize()` builds a fresh `httpx.AsyncClient` per call, so each
of those 105 repeats is two new TCP connections plus a full engine synthesis.

**No speech-rate control.** `synthesize()` posts `/audio_query`, then forwards the response
to `/synthesis` untouched. VOICEVOX exposes `speedScale`, `pitchScale`, and
`intonationScale` in that query object, and a slow-speech setting is close to mandatory for
an A1 tutor. The plumbing to use them already exists and is simply not used.

**Text normalization is implemented twice, differently.** `voicevox_client.prepare_for_voicevox()`
(Python) and `speech.ts::speakableText()` (TypeScript) both strip code fences, markdown,
and Latin parentheticals before synthesis, with different rules — the Python side also
truncates to 300 characters and drops any Latin run of 3+ characters when Japanese is
present. The frontend cleans the text, then the backend cleans it again.

**TTS is fully serial.** `speakTutor()` splits into ≤80-character chunks, then for each
chunk awaits synthesis and awaits playback before starting the next. Total latency is the
sum of every synthesis plus every playback, with the engine idle during playback. Chunk
*n+1* could be synthesised while chunk *n* plays.

**Silent TTS failure can hang the UI.** If VOICEVOX errors, `speakTutor` falls back to
`browserSpeak()`. In an Electron/Chromium runtime with no Japanese system voice,
`speechSynthesis.speak()` may fire neither `onend` nor `onerror`, and the promise never
settles — `runPipeline` stays inside its `try`, `speakingRef` stays `true`, and every
control stays disabled. There is no timeout on that promise.

**Book audio has no error recovery.** `playBookTracks()` rejects on `audio.onerror`, which
propagates out of `runPipeline` into the catch-all, sets the error banner, and aborts the
turn — leaving no mic and no way forward except Skip. Given that `assets/` is supplied by
the learner and gitignored, a missing or misnamed MP3 is a likely first-run experience, and
it currently stalls the lesson rather than degrading to "read the phrase and say it".

**Microphone is re-acquired every turn.** `startListening()` calls
`navigator.mediaDevices.getUserMedia()` on each utterance instead of holding one stream for
the lesson, adding device-init latency to every single answer.

### 2.3 Curriculum loading and lesson progression

**No caching whatsoever.** `curriculum_loader.load_lesson()` reads and `yaml.safe_load`s the
file on every call:

| File | Parse cost |
|---|---|
| `L01.yaml` (21.5 KB) | 25.2 ms |
| `L16.yaml` (32.7 KB) | 29.8 ms |
| `EL13.yaml` | 28.9 ms |
| `index.yaml` | 4.5 ms |

A single `POST /tutor/{id}/advance` parses the lesson twice (once in the orchestrator, once
via `flow._grammar_for_lesson`) for **53–62 ms of pure YAML parsing per turn**. Worse,
`GET /progress` loads every lesson in the book:

```
19 lessons, 54 can-dos → 515 ms, 19 KB response
= 19 YAML parses + 73 individual DB gets per call
```

`GET /progress` is called on Dashboard mount, on Tutor mount, on the Progress map, and
again after every lesson change. Content files are static at runtime; an LRU cache keyed by
`(lesson_id, mtime)` removes essentially all of this.

**N+1 database access.** `progress_overview` issues one `db.get()` per lesson plus one per
Can-do (73 round trips above). `self_check_summary`, called on most tutor responses, adds
one `db.get(CanDoProgress, …)` per Can-do on top.

**Two sources of truth for the active book.** `curriculum_loader._active_book_id()` prefers
the `settings` DB row; `settings.content_dir` reads the mutable `settings.active_book`
attribute; `set_active_book()` writes both. A process that never calls `set_active_book`
has a stale `settings.active_book`.

### 2.4 Ask Yuki (Ollama) integration

**The freeze is correct.** `answer_question()` snapshots `state`, `activity_id`, and
`quiz_index` before the call and restores them afterwards, marks the reply `help: True` so
`_sync_book_substep` and the display model skip it, and returns the pre-existing step. This
is the right design and it is implemented defensively.

**Context assembly is unbounded and untokenized.** `_ollama_lesson_help` builds a context
dict containing `_lesson_phrase_bank(lesson)` — up to **80 phrases** — plus 12 grammar
points, the full activity `key_phrases` and `phrase_meta`, and the step. For the
Whisper-derived lessons those phrases are long multi-sentence strings, so a single help
request can push several thousand tokens of mostly-noise into a 7B model's context. There
is no token budget, no truncation by length, and no relevance filtering (the phrases are
lesson-wide, not step-local). Outputs are truncated after the fact (`jp[:500]`, `en[:800]`)
but inputs never are.

**No conversation memory.** Each question is a fresh two-message prompt. A follow-up like
"why?" has no idea what was just explained. Prior Q&A pairs are in `messages_json` and are
simply not used.

**No timeout tuning or streaming.** `ollama_client.chat` uses a flat 120-second timeout with
`stream: false`, so the UI shows "Thinking…" with no output for however long the model
takes, and a cold model load can approach the timeout. `format_json=True` is requested but
the response is only guarded by a bare `except Exception`, so a malformed reply silently
becomes the generic "try saying the first phrase" fallback with no indication to the
learner that the model failed.

**Grading prompt sends the heuristic result to the grader.** `llm_refine_grade` includes
`"heuristic": base` in the user message, which anchors the model to a score that the
findings in §2.5 show is often wrong.

### 2.5 Grading (`phrase_grade.py`)

The pass decision is `0.40 × SequenceMatcher + 0.60 × character-bigram overlap`, with a
length-similarity bonus and a "soft pass" band from 48 to 58. It has no model of Japanese
morphology, so:

- **Negation is invisible.** わかります vs わかりません scores 77.1 and passes. The
  distinguishing morpheme is exactly what the learner is being tested on.
- **Content words are invisible.** 肉が好きです vs 魚が好きです scores 93.3 and passes.
  In L05 the entire drill is which food you like.
- **Long vowels are deleted.** `normalize_jp_for_grade` runs `re.sub(r"[ー∼]+", "", s)`,
  which collapses ビール onto ビル (100.0), コーヒー onto こひ, and so on.
- **Polite/casual pairs are not equated.** ありがとう against ありがとうございます scores
  53.3 and fails, even though L01 teaches both as the same Can-do.

Two further problems compound this:

- **Reported scores are fabricated.** `score = 100.0 if passed and hits else best_score`,
  so a 48%-similarity soft pass is shown to the learner as `100%` and written to
  `CanDoProgress.best_score` as 100. `quiz_grade` additionally floors failing scores at
  `40.0`, so silence records a 40.
- **`mastery_min_score` is only enforced on the LLM path.** In `llm_refine_grade` the check
  `score >= settings.mastery_min_score` lives inside the `try`. On the `except` branch —
  which is every request when Ollama is down — `base` is returned unchecked, so the 80%
  threshold advertised in the Settings page does not apply.

### 2.6 SRS (FSRS)

**Persisted FSRS fields are incomplete.** `_apply_fsrs` writes `due`, `stability`,
`difficulty`, `state`, `last_review`, and increments `reps`. It never writes `lapses`,
`scheduled_days`, or `elapsed_days`, all of which are columns on `SrsCard`. Measured: after
rating a card **Again**, `lapses` is still 0. Lapse count feeds FSRS difficulty, so the
scheduler is being fed a systematically incomplete history.

**New cards never start as New.** `card.state = State(row.state) if row.state else State.Learning`
treats `State.New` (value 0) as falsy, so a brand-new card is presented to the scheduler as
Learning and skips the New→Learning transition entirely.

**Production cards leak the answer.** `enqueue_vocab` creates a `vocab_production` card
whose front is:

```
Say in Japanese (from lesson L01): concept related to 「おはようございます」
```

with back `おはようございます`. The Japanese answer is printed on the prompt side. These
cards cannot teach production.

**Card content is whatever `key_phrases` contains**, and for L03–L18 that is Whisper noise.
Seeding L16 produced flashcards like:

```
front: 年端え1b5円c10円d50円e100円f500円g1000円h2000円i5000円g1万円
front: 4あのー緑ませんこれいくらですかはいこれですねえっと3万4千ご100円です
front: よんいらっしゃいませチョコレートケーキとチーズケーチニコズツをお願いします…
```

**Config that does nothing.** `settings.srs_daily_new_cap` is defined and never read; there
is no new-vs-review split, no per-lesson scoping, and no audio on cards despite the
`audio_path` column existing.

### 2.7 Logging, error reporting, API structure

**Logging is good.** `log_event()` emits one greppable structured line per event with
sensible truncation, rotation is configured, and `/log/tail` plus the Setup page make it
reachable without leaving the app. The client mirrors UI events to the same file through
`/log/client`. This is better than most projects this size.

**Gaps:**

- No request/session correlation id, so interleaved turns are hard to separate.
- `read_log_tail` reads the entire (up to 2 MB) file to return 200 lines.
- Errors are surfaced to the learner as raw exception strings —
  `raise HTTPException(503, f"VoiceVox error: {e}")` renders in the UI as an httpx
  connection error rather than "VOICEVOX isn't running".
- No global exception handler; an unexpected error in the orchestrator returns a bare 500
  and the UI shows an empty banner.
- `except Exception: pass` appears in `db.init_db`, `voicevox_client.get_selected_speaker_id`,
  `set_selected_speaker_id`, and `curriculum_loader._active_book_id`. Persisting the voice
  selection can fail completely silently.

**API structure.** Routers are cleanly split by domain, `Depends(get_db)` is used
consistently, and Pydantic models cover request bodies. Response models are absent
everywhere, so the payload contract is defined only by the orchestrator's dict literals —
which is also why the frontend types everything as `any`. `CORSMiddleware` is configured
with `allow_origins=["*"]` together with `allow_credentials=True`, a combination the CORS
spec forbids and browsers reject; for a localhost-bound API the correct setting is an
explicit origin allowlist (`http://127.0.0.1:5173` plus the packaged origin). As written,
any web page the learner visits can call this API.

---

## 3. Frontend audit

### 3.1 Component structure and state management

`Tutor.tsx` is 586 lines holding 11 `useState`s, 6 `useRef`s, the recorder lifecycle, the
audio pipeline, Ask Yuki, self-check, lesson navigation, and the whole layout. `TutorStage`,
`ModeCard`, and `tutorDisplay.ts` are a clean presentation layer — the display model
computed in `buildTutorStageModel()` is a good pattern — but the orchestration around them
is monolithic. Recorder + pipeline + session state want to be `useTutorSession()` and
`useMicRecorder()` hooks so the page becomes layout.

`session` is `any`, `activity` is `any`, `lastGrade` is `any`, `lessons` is `any[]`. TypeScript
is in `strict` mode and buys nothing on the data that matters. There are no shared types
with the backend and no runtime validation, so a payload shape change fails as a blank
panel rather than a type error.

### 3.2 Tutor flow and the audio pipeline

The listen → repeat → select → dialog → quiz flow is implemented and it works. Two
concrete defects:

**Skip during recording races the answer.** `manualAdvance()` calls `stopListening()`,
which fires `MediaRecorder.onstop`. That handler checks `recordingModeRef.current !==
"practice"` — it *is* `"practice"` — so it transcribes the partial audio and `POST`s
`/tutor/{id}/message` while `manualAdvance` is concurrently `POST`ing `/advance`. Two
mutations of the same session race, and which one wins depends on Whisper latency. The
`recordingModeRef` guard exists precisely for this and simply is not cleared on the skip
path (`askByVoice` and `submitQuestion` both clear it correctly).

**Auto-advance logic is duplicated and has drifted.** The backend already publishes
`auto_advance_after_audio` on the step, and `book_modes.auto_advance_substeps()` is the
canonical Python set. `Tutor.tsx` re-implements it:

```ts
sub === "listen" || sub === "shadow" || sub === "partner" ||
sub === "swap_partner" || sub === "announce"
```

`"announce"` is not a substep any current mode emits — it is a leftover from the
`SUB_ANNOUNCE`/`SUB_PRACTICE` design. Any new auto-advancing substep must be added in two
languages or it will hang waiting for a tap.

**No barge-in.** Every control is `disabled={busy || speaking}`, so a learner who already
knows the line waits through the full TTS. `TutorStage` disables the mic button the same
way. There is no stop-speaking control.

### 3.3 Rendering efficiency

Every response carries the full transcript, and the transcript grows monotonically:

| Turn | Messages | Payload |
|---|---|---|
| 1 | 2 | 3.0 KB |
| 40 | 79 | 34.4 KB |
| 80 | 149 | 64.6 KB |
| 120 | 221 | 89.2 KB |

`setSession(s)` replaces the object, so `messages.map(...)` re-renders all 221 bubbles on
every turn, keyed by array index. `buildTutorStageModel` is correctly memoized on `session`,
but `session` is a new object every turn so the memo never hits. The transcript needs
`React.memo` per bubble with a stable key, and the API needs to return a bounded window
(with a separate endpoint for full history).

### 3.4 Avatar rendering

`TutorMascot` swaps three PNGs. The speaking animation runs `setInterval` at 180 ms, and
each tick calls `setMouthOpen` *and* `setFrame` inside the updater — a state update inside
another state updater, which is a React anti-pattern and triggers two re-renders of the
subtree every 180 ms for the whole time Yuki is talking. The mouth flap is also a fixed
timer with no relationship to the audio, so it keeps flapping through silence and stops
mid-word. Images are imported as three separate assets with no preload, so the first
`speaking` frame can flash empty. A CSS-driven two-frame animation (or a single sprite with
`background-position`) removes the interval and both re-renders.

### 3.5 Settings and preferences

`VoiceSettings` is the best-built component in the app — it lists real VOICEVOX
characters/styles, persists through `/voice/set-speaker`, and previews. What is missing:
speech rate and pitch (see §2.2), separate voices for the partner role versus the tutor
narration, and any preference that is not the voice. Selecting from the dropdown saves
immediately with no undo.

Everything else on the Settings page is read-only prose telling the learner to edit
environment variables. There is no UI for Whisper model size, Ollama model, mastery
threshold, autoplay, or TTS on/off, even though all of them exist in `Settings`.

`api.pdfUrl()` is typed `("starter" | "grammar")` and hardcodes `which=`, so **the Settings
page always opens the Starter PDF even when Elementary 1 is the active book**, despite
`/media/pdf` accepting a `book` parameter.

`BookSwitcher` calls `window.location.reload()` after changing books — a full app reload
that discards all in-memory state.

### 3.6 Electron packaging and resources

- `startBackend()` spawns Python with `stdio: "ignore"` and **no `.on("error")` handler**.
  If `python` is not on `PATH` — the single most likely failure for a recipient of the
  portable zip — Node emits an unhandled `'error'` event on the ChildProcess and the main
  process crashes with no message.
- `waitForHealth()`'s `false` return is discarded; `createWindow()` runs regardless, so a
  backend that failed to start yields a blank window in packaged mode (it loads
  `http://127.0.0.1:8765/`).
- No `app.requestSingleInstanceLock()`. A second launch spawns a second backend that fails
  to bind 8765.
- `openDevTools({ mode: "detach" })` is unconditional in dev.
- `backendProc.kill()` sends SIGTERM; on Windows uvicorn's reloader/worker children can
  survive, which is exactly why `stop_jtutor.bat` exists.
- `index.html` loads Shippori Mincho and IBM Plex Sans **from Google Fonts over the
  network**. An explicitly offline-first local app falls back to system fonts without
  internet, and leaks a request to a third party on every launch. These should be bundled.
- No `contextIsolation` complaints — the preload is minimal and correct — but
  `preload.cjs` hardcodes `apiBase` to port 8765 with no way to override.
- Vite has no route-level code splitting and no manual chunks. Minor at this size, but the
  whole app is one bundle.

---

## 4. Curriculum pipeline audit

### 4.1 The Whisper-derived content is the core problem

`build_curriculum.py` hand-curates L01 and L02 (`L01_PHRASE_BY_ACTIVITY`,
`L02_PHRASE_BY_ACTIVITY`, curated quiz scenarios, book-faithful modes) and it shows — those
two lessons are genuinely good. L03–L18 fall back to
`apply_phrases_from_transcripts()`, which runs `transcript_phrases.pick_phrases()` over
cached Whisper output and stores the result as graded targets.

Scanning all 36 lesson files (2,177 phrases in total):

| Symptom | Count |
|---|---|
| "Phrases" starting with a digit (the CD track number read aloud) | 174 |
| Phrases longer than 25 characters (whole multi-sentence utterances) | 206 |
| Phrases containing Latin runs (ASR garbage) | 8 |
| Activities with no phrases at all | 22 |

Representative examples that are currently graded targets:

```
L03 A3   3初めまして私はマルシアですブラジルからきましたよろしくお願いします
L04 A2   1土です2あねです3おとうとうです4あにです5つまです6いもおとうです7子どもです…
L05 A1   1カムラさん、魚、好きですか        ← 中村 misheard, track number prepended
L11 A20  スポーツは全然しないねwitnessesが
L15 A22  えかっこいいビ可愛いし高いビやすいいい面白いえきれいなじステキな…
```

Per-lesson concentration (starter book):

| Lesson | Phrases | >25 chars | Digit-prefixed |
|---|---|---|---|
| L01 (curated) | 29 | 0 | 0 |
| L02 (curated) | 61 | 0 | 0 |
| L13 | 77 | 18 | 19 |
| L16 | 51 | 23 | 18 |
| L10 | 58 | 11 | 21 |

The consequences are systemic: these strings are the `say_target_jp` shown on the "Say
this" card, the grading target, the `expected` list in auto-generated quiz scenarios
(`enrich_quiz_from_activities`), the Ask Yuki context (`_lesson_phrase_bank`), and the SRS
card fronts. One bad extraction propagates to five surfaces.

**There is no validation gate.** `verify_l01_phrases.py` checks one lesson and only for
emptiness. Nothing rejects a phrase for being 80 characters long, starting with a digit, or
containing Latin text.

Elementary 1 is meaningfully better because `build_curriculum_elementary1.py` reads the
printed dialog scripts from the PDF instead of the audio — `EL01`–`EL11` have 0–1 long
phrases each. `extract_scripts_elementary1.py` pulls `A：`/`B：` lines and short model
utterances, keyed to CD markers like `01-04`, and explicitly filters instructional
`〜ましょう` text. Starter has no equivalent: `extract_pdf.py` samples only the first four
pages of each lesson and keeps at most 30 quoted or `A：`-prefixed strings, which is why the
builder falls back to Whisper. Porting the Elementary 1 script extractor to Starter is the
proven fix and reuses code that already exists in this repository.

### 4.2 Extraction scripts

- `build_curriculum.py` is 1,088 lines, of which ~330 are hardcoded L01/L02 data tables
  interleaved with generic logic. The curated data should be YAML overlays under
  `content/starter/overrides/`, loaded and merged, so the builder is pure logic and content
  edits do not require touching Python.
- `pick_phrases()` splits on `。！？` only. Whisper output for these CDs often has no
  punctuation, which is exactly how a full four-speaker exercise becomes one "phrase".
- `_score_phrase()` scores by length and a handful of regexes and has no penalty for
  leading digits, Latin characters, or absurd length beyond a −0.15 nudge above 55
  characters.
- `apply_generic_book_flow()` is called at the end of `apply_phrases_from_transcripts()`
  *and* separately in the non-transcript branch, and it re-derives `listen_counter`
  independently of the caller's, so `listen_repeat` vs `listen_select` assignment depends on
  which path ran.
- `infer_dialog()` picks partner = first question-final sentence, learner = last sentence.
  On a four-line CD, partner and learner come from different exchanges.
- `build_curriculum_elementary1.py` imports `_dialog`, `apply_generic_book_flow`, and
  `attach_phrase_meta` from `build_curriculum` — a script importing another script's
  private helper, with `sys.path` manipulation in both.
- `scripts/books.py` (`BookConfig`) and `backend/app/books.py` (`BookInfo`) are two
  registries for the same two books with different field sets. `audio_prefix` and
  `toc_*_pages` exist only in the script copy; the backend copy cannot see them.
- `index_audio.py` maps `yomu → reading`; `build_curriculum_elementary1.SKILL_KIND` maps
  `reading → listening`; `build_curriculum.SKILL_KIND` has no `reading` entry at all, so
  Starter reading tracks keep `kind: "reading"` and fall through to the generic
  `listen_repeat`. The same audio label produces different behaviour per book.

### 4.3 Schema consistency

The two `index.yaml` files do not share a schema:

```
starter : book, level, title, assets      | lesson entries: lesson_id, title_en, topic_en,
                                          |   can_do_count, activity_count, audio_count
elem1   : book_id, book_title, level      | lesson entries: + book_id, lesson, title_jp
```

`routes/curriculum.py` returns `idx.get("book_title")`, which is `None` for Starter, so the
Dashboard's `p.book_title || p.book_id` renders the literal string **"starter"** instead of
"Irodori Starter". There is no schema definition and no validator; `docs/CURRICULUM_SCHEMA.md`
documents optional activity fields but not the lesson or index envelope.

`content/starter/.gitignore` excludes `pdf_extract.json` and `grammar_extract.json`, but
`content/elementary1/` commits both plus `script_extract.json` — so
`lesson_flow._grammar_for_lesson()`'s fallback to reading `grammar_extract.json` from disk
works for Elementary 1 and silently returns `[]` for Starter on a fresh clone.

### 4.4 Automation and metadata gaps

No furigana/reading, no per-phrase English gloss, no romaji, no JLPT/level tag, no audio
timing offsets (so no per-phrase playback within a track), no speaker/gender metadata, no
politeness register beyond the coarse `phrase_meta.tags`, no `picture_has_image` verified
against the PDF, and no difficulty ordering. `vocab` entries are generated with
`reading: ""` and `en: ""` always empty.

---

## 5. Overall architecture

**Layering is clean.** `routes → orchestrator → lesson_flow → book_modes`, with
`curriculum_loader`, `db`, and the three service clients as leaves. Dependencies point one
way. `backend/app/__init__.py` re-exports DB symbols nobody imports, which is harmless but
pointless.

**Duplicated logic across the boundary.** Three separate cases where the same rule exists in
both Python and TypeScript and has drifted or can drift:

| Rule | Python | TypeScript |
|---|---|---|
| Which substeps auto-advance | `book_modes.auto_advance_substeps()` | hardcoded list in `Tutor.tsx` (includes stale `"announce"`) |
| TTS text cleanup | `voicevox_client.prepare_for_voicevox()` | `speech.ts::speakableText()` |
| Mode/substep display labels | `lesson_flow.book_step()` English strings | `SUBSTEP_LABELS`/`MODE_LABELS` in `tutorDisplay.ts` **and** `MODE_LABELS` in `ModeCard.tsx` |

Note the third one is duplicated *within* the frontend as well — `tutorDisplay.ts` and
`ModeCard.tsx` each keep their own mode-label map.

**Missing abstractions.**

- No base abstraction for a tutor mode. `lesson_flow.book_step()` is a 150-line if-chain
  over substep names; `intro_step`, `self_check_step`, and `quiz_step` live in three other
  modules with three different signatures and no common contract.
- No `Step` type. The step dict is constructed ad hoc in six places with overlapping keys
  (`expect_speech`, `play_audio`, `auto_advance_after_audio`, `say_target_jp`,
  `book_substep`, `help`, …) and no schema, on either side of the wire.
- No audio abstraction. Book-MP3 playback, VOICEVOX playback, and recording are three
  unrelated inline implementations in `Tutor.tsx` and `speech.ts`.
- No repository layer. `db.get(...)` calls are scattered through the orchestrator,
  `self_check`, `srs_service`, `lesson_unlock`, and the routes.

**Dead code confirmed by reference count** (definition only, zero call sites):
`lesson_flow.book_announce`, `lesson_flow.book_practice_prompt`, `lesson_flow.quiz_intro_script`,
`lesson_flow.SUB_ANNOUNCE`, `lesson_flow.SUB_PRACTICE`, `book_modes.timed_audio_substeps`,
`free_response.intro_turn_count`, `settings.srs_daily_new_cap`.
`book_modes.auto_advance_substeps` is imported by both `orchestrator` and `lesson_flow` and
called by neither. `phrase_grade.hybrid_grade` is a pass-through alias for `grade_phrases`.

**No tests, no CI, no linter.** There is no `tests/`, no `.github/`, no `ruff.toml`,
`pyproject.toml`, `.eslintrc`, or `pytest.ini` anywhere in the repository. For a
deterministic state machine — the one thing in this app that is genuinely easy to test —
that is the largest single gap in engineering hygiene here.

**Naming.** Mostly consistent and readable. The exceptions: `quiz_index` (§2.1),
`book_activity` (an integer ordinal, not an activity), `activity_id` vs `track` vs
`book_activity` for three different identifiers of the same row, `kind` vs `book_mode` vs
`book_substep` as three parallel taxonomies, and leading-underscore "private" functions
imported across modules (`flow._grammar_for_lesson`, `flow._phrases`,
`curriculum_loader._active_book_id` are all called from other modules, including routes).

---

## 6. Missing Irodori pedagogical steps

Mapped against the Irodori Starter lesson structure:

| Irodori step | Status in Jtutor |
|---|---|
| もくひょう / Can-do goals | Present — `intro_script` + Can-do list |
| ウォーミングアップ / warm-up | Present — `intro_chat`, ungraded, correctly so |
| きいて いいましょう / listen & repeat | Present — `listen_repeat`, `listen_repeat_all` |
| ききましょう / listening comprehension | Partial — `listen_select` asks the learner to *say* the phrase; there is no comprehension check (no options, no answer key) |
| はなしましょう / speaking model | Present — `dialog` partner/learner |
| シャドーイング / shadowing | Present — `shadow` substep inside `dialog`, plus standalone `shadow_dialog` |
| ロールプレイ + 役割交代 / role-play + swap | Present — `swap_learner`, `swap_partner` |
| ことば / vocabulary | **Weak** — no vocabulary mode; `kind: vocabulary` maps to `listen_repeat`, no meanings, no gloss |
| かたち・ぶんぽう / grammar | **Weak** — reads the point name aloud, no examples, no audio, any 2 characters passes |
| はつおん / pronunciation | **Missing entirely** — no mora/pitch/rhythm step, and grading normalizes long vowels away |
| にほんごの もじ / kana | **Missing** — `kind` in `{hiragana, katakana, script}` is filtered out by `book_tracks()`; L00 is emptied the same way (§2.1) |
| よむ / reading | **Missing** — `yomu` tracks are remapped to listening or fall through inconsistently (§4.2) |
| かく / writing | **Missing** — no text-input production step anywhere |
| 生活と文化 / life and culture | **Missing** — `english_notes` is extracted into the YAML and never surfaced |
| ふりかえり / reflection | Present — `self_check` stars + comment, correctly non-gating |
| ポートフォリオ / portfolio | **Missing** — self-check comments are stored but never shown back |

The two most defensible additions, in Irodori's own terms, are a **pronunciation step**
(はつおん is a numbered section in the book and the current normalizer actively works
against it) and a **vocabulary step** with meanings (ことば underpins every later Can-do and
currently degrades to undifferentiated repetition).

---

## 7. Code smells and anti-patterns

| # | Smell | Where |
|---|---|---|
| 1 | One integer with six meanings | `ChatSession.quiz_index` |
| 2 | Reconstructing authoritative state from the rendered transcript | `orchestrator._sync_book_substep` |
| 3 | 150-line if-chain over string substep names | `lesson_flow.book_step` |
| 4 | Two functions answering the same question with different coverage | `_resolve_step` / `_lesson_step_snapshot` |
| 5 | Blocking CPU work in an `async def` handler | `routes/voice.py::transcribe` |
| 6 | `except Exception: pass` hiding persistence failures | `db.init_db`, `voicevox_client` ×2, `curriculum_loader` |
| 7 | Underscore-private functions imported across modules | `flow._grammar_for_lesson`, `flow._phrases`, `curriculum_loader._active_book_id` |
| 8 | Hardcoded content data tables inside build logic | `build_curriculum.py` L01/L02 tables, ~330 lines |
| 9 | Script importing another script's helpers via `sys.path` | `build_curriculum_elementary1.py` |
| 10 | Two registries for the same domain object | `backend/app/books.py` vs `scripts/books.py` |
| 11 | Same rule implemented in Python and TypeScript | auto-advance set, TTS cleanup, mode labels |
| 12 | Mode labels duplicated within the frontend | `tutorDisplay.ts` and `ModeCard.tsx` |
| 13 | `any` on every piece of data that crosses the wire | `Tutor.tsx`, `Dashboard.tsx`, `ProgressMap.tsx`, `SrsReview.tsx` |
| 14 | `setState` inside another `setState` updater on a 180 ms interval | `TutorMascot` |
| 15 | Full-page `window.location.reload()` as a state-reset mechanism | `BookSwitcher` |
| 16 | Debug affordances shipped in the learner UI | "Jump to Can-do quiz", "Can-do (reset progress)" |
| 17 | Reported score decoupled from measured score | `phrase_grade` `score = 100.0 if passed` |
| 18 | Threshold enforced on one code path only | `mastery_min_score` in `llm_refine_grade` |
| 19 | Dead code kept alive by unused imports | §5 list |
| 20 | Ad-hoc `ALTER TABLE` string migrations | `db._migrate_sqlite_columns` |
| 21 | Mutable global config written at runtime | `settings.active_book` |
| 22 | No response models; the API contract is a dict literal | `orchestrator._payload` |

---

## 8. Prioritized roadmap

The brief asked for calendar buckets. Estimating a Jtutor change in weeks is not something
this document can do honestly, so the tiers below are ordered by **impact per unit of
risk**, and each item states which subsystems it touches and how invasive the edit is. Tier
1 items are mostly single-file and independently shippable; Tier 3 items change contracts
that other components depend on.

All tiers respect the stated constraints: no rewrite, no tutor mode removed, progression
stays deterministic, existing YAML keeps loading, and VOICEVOX/Whisper/Ollama stay in
place.

### Tier 1 — correctness and cheap wins

Contained edits, each one file or two, no schema or contract change.

| # | Change | Touches | Invasiveness |
|---|---|---|---|
| 1.1 | Enforce unlock in `start_or_resume` — drop the `lp and` guard; add the same check to `advance`/`message`/`jump-can-do` | `orchestrator`, `lesson_unlock` | ~6 lines |
| 1.2 | Break the Can-do loop — on a failed full cycle, emit a message naming the outstanding Can-dos and offer a route back to the book instead of silently resetting to 0 | `orchestrator.advance` | one branch |
| 1.3 | Report the real score — remove `score = 100.0 if passed`, remove the `40.0` floor in `quiz_grade`, enforce `mastery_min_score` on the heuristic path too | `phrase_grade`, `orchestrator.llm_refine_grade` | ~10 lines |
| 1.4 | Stop blocking the event loop — change `async def transcribe` to `def transcribe` | `routes/voice.py` | 1 word |
| 1.5 | Cache lesson YAML — `functools.lru_cache` keyed by `(lesson_id, mtime)` | `curriculum_loader` | ~15 lines; removes ~50 ms/turn and ~500 ms from `/progress` |
| 1.6 | Cache TTS — LRU on `(text, speaker_id)` → wav bytes, plus one shared `httpx.AsyncClient` | `voicevox_client` | ~20 lines; removes ~105 synthesis calls per lesson |
| 1.7 | Whisper options — `vad_filter=True`, `beam_size=1`, `condition_on_previous_text=False`, `without_timestamps=True`; warm the model on startup | `whisper_service`, `main` | ~10 lines |
| 1.8 | Fix the skip/record race — clear `recordingModeRef` in `manualAdvance` and everywhere else that stops the recorder without wanting a submission | `Tutor.tsx` | 3 lines |
| 1.9 | Stop `jump_to_can_do_quiz` wiping the transcript; move both jump buttons behind a dev flag | `orchestrator`, `Tutor.tsx` | small |
| 1.10 | Fix FSRS persistence — write `lapses`, `scheduled_days`, `elapsed_days`; use `is not None` for `State` | `srs_service` | ~8 lines |
| 1.11 | Fix the production SRS card front (currently prints its own answer) | `srs_service.enqueue_vocab` | 2 lines |
| 1.12 | Tighten CORS to an explicit localhost allowlist | `main` | 2 lines |
| 1.13 | `.on("error")` on the Python spawn + single-instance lock + surface a health-check failure | `electron/main.cjs` | ~25 lines |
| 1.14 | Bundle the two web fonts locally | `index.html`, `apps/desktop/src` | asset move |
| 1.15 | Pass the active book to `api.pdfUrl` | `api.ts`, `Settings.tsx` | 3 lines |
| 1.16 | Emit `book_title` in the Starter `index.yaml` | `build_curriculum.py` + regenerate | 1 line |
| 1.17 | Delete confirmed dead code and unused imports | `lesson_flow`, `book_modes`, `orchestrator`, `free_response`, `config` | deletions |

### Tier 2 — pedagogy and quality

Multi-file, but additive: new modes are new table entries, and new YAML fields stay
optional.

| # | Change | Touches | Invasiveness |
|---|---|---|---|
| 2.1 | **Token-aware grading** — segment with `fugashi`/`SudachiPy`, compare content-word bags, treat negation and polarity as hard constraints, add a polite↔casual equivalence table, stop deleting long vowels | `phrase_grade` (+ one dependency) | rewrite of one module, same public signature |
| 2.2 | **Curriculum quality gate** — a validator that rejects phrases with leading digits, Latin runs, >25 characters, or duplicate-of-whole-transcript; fail the build and report per lesson | new `scripts/validate_curriculum.py` | new file + CI hook |
| 2.3 | **Move Starter L03–L18 off Whisper** onto PDF dialog scripts, as Elementary 1 already does | generalize `extract_scripts_elementary1.py` to both books, `build_curriculum.py` | reuses a proven extractor already in the repo |
| 2.4 | **Pronunciation mode** (`pronunciation`) — mora/rhythm drill; requires 2.1 first so long vowels are no longer normalized away | `book_modes`, `lesson_flow`, `tutorDisplay`, `ModeCard` | one table entry + one branch per layer |
| 2.5 | **Vocabulary mode** (`vocab_drill`) — JP↔EN with meanings; needs a `gloss_en` field on `vocab` | same four files + builder | additive YAML field |
| 2.6 | **Grammar step with substance** — examples and audio from the worksheets; grade the example rather than accepting 2 characters | `lesson_flow`, `extract_grammar*` | moderate |
| 2.7 | Kana / L00 path — stop filtering `script`/`classroom` out of `book_tracks` unconditionally; give them a real (ungraded) mode | `lesson_flow.book_tracks`, `book_modes` | small but changes track lists — needs the fixture tests from 2.10 |
| 2.8 | Bound the tutor payload — return the last *N* messages plus `GET /tutor/{id}/history`; `React.memo` the bubbles with stable keys | `orchestrator._payload`, `Tutor.tsx` | contract change, versioned |
| 2.9 | Barge-in — a stop-speaking control, and enable the mic during TTS | `Tutor.tsx`, `speech.ts`, `TutorStage` | moderate |
| 2.10 | **Fixture tests for the state machine** — snapshot the full substep sequence for L00/L01/L02/L05/EL01, assert determinism, assert unlock gating, plus a grading truth table | new `tests/` + `pytest` + ruff/eslint + a CI workflow | new infrastructure; unblocks everything in Tier 3 |
| 2.11 | Ask Yuki context budget — step-local phrases first, hard token cap, include the last 2 Q&A turns | `orchestrator._ollama_lesson_help` | one function |
| 2.12 | Speech rate / pitch in `/audio_query`, exposed in Voice settings | `voicevox_client`, `routes/voice`, `VoiceSettings` | small, high perceived value |
| 2.13 | Real error surfaces — map connection failures to "VOICEVOX isn't running" with a Setup link; global exception handler; timeout on `browserSpeak` | `routes/*`, `main`, `speech.ts` | small |

### Tier 3 — structural

Contract changes. Should land only behind the Tier 2.10 tests.

| # | Change | Touches | Invasiveness |
|---|---|---|---|
| 3.1 | **`TutorMode` base class** — `substeps()`, `render(index)`, `expected(index)`, `grade(...)`; registry keyed by `book_mode`; `book_step()` becomes dispatch | `lesson_flow`, `book_modes`, `free_response`, `self_check` | large, behaviour-preserving |
| 3.2 | **Lesson flow controller** — replace `quiz_index` with `phase` + `phase_index` (+ a one-shot migration mapping the old column), delete `_sync_book_substep` | `db`, `orchestrator`, `lesson_progress` | schema change; the payoff for smells 1, 2, 4 |
| 3.3 | **Typed `Step` contract** — Pydantic models on the backend, generated TS types on the frontend, `any` eliminated | `orchestrator`, `routes`, all of `apps/desktop/src` | wide but mechanical |
| 3.4 | **Unified audio pipeline** — one `useAudioPipeline()` owning book MP3s, TTS, and recording, with preloading, prefetch of the next TTS chunk, a persistent mic stream, and retry/degrade on missing files | `Tutor.tsx`, `speech.ts`, new hook | replaces three inline implementations |
| 3.5 | **Centralized Whisper service** — a single worker with a bounded queue, warm model, VAD trimming, batching, and a `/voice/transcribe` that returns confidence | `whisper_service`, `routes/voice` | moderate |
| 3.6 | **Canonical YAML schema** — one Pydantic model for lesson + index, validated at build and load, one `index.yaml` envelope for both books, versioned with `schema_version` and a loader shim so existing files keep working | `curriculum_loader`, both builders, `docs/CURRICULUM_SCHEMA.md` | cross-cutting; must stay backward compatible |
| 3.7 | Single book registry shared by backend and scripts | `backend/app/books.py`, `scripts/books.py` | delete one, import the other |
| 3.8 | Curated content as YAML overlays instead of Python tables | `build_curriculum.py`, new `content/*/overrides/` | removes ~330 lines from the builder |
| 3.9 | Reading / writing / culture / portfolio steps | schema, modes, UI | new pedagogy, depends on 3.1 and 3.6 |

---

## 9. Specific actionable suggestions

### 9.1 New tutor modes

Three of the modes named in the brief already exist and should be *improved*, not added:

- **Shadowing** — implemented, as the `shadow` substep inside `dialog` and the standalone
  `shadow_dialog` mode. Missing: it is only wired for dialog activities. Extend the shadow
  substep to `listen_repeat_all` drills and add a half-speed replay using the
  `speedScale` work in 2.12.
- **Intro chat** — implemented as `intro_chat`, ungraded, with `intro_questions` in YAML.
  Missing: the answers are acknowledged with a fixed string and discarded. Feed them to
  Ollama for a one-line contextual response, and keep them for the portfolio.
- **Self-check** — implemented as `self_check` with stars and a comment, correctly
  non-gating. Missing: it only fires *after a pass* (`_after_can_do_passed`), so a learner
  who never passes never reflects; and the stored comments are never shown back.

Genuinely new modes worth adding, in priority order:

1. **`pronunciation`** — target mora count and rhythm on a phrase already drilled. Depends
   on 2.1 (the current normalizer deletes the very features being taught).
2. **`vocab_drill`** — JP→EN and EN→JP over `lesson.vocab` with real glosses. Feeds SRS
   with cards that are actually reviewable.
3. **`listen_choose`** — a true comprehension check: play the CD, show 3–4 options, learner
   picks. Today's `listen_select` skips comprehension and jumps to production.
4. **`kana_trace`** — an ungraded mode so `hiragana`/`katakana` tracks and L00 stop being
   silently dropped.

Each is one entry in `FLOW_BY_MODE`, one branch in `book_step()`, one label in
`SUBSTEP_LABELS`/`MODE_LABELS`, and one card in `ModeCard`. No existing mode changes.

### 9.2 Voice selection UI and backend config

The selection UI exists and works (`/voice/speakers`, `/voice/set-speaker`,
`VoiceSettings`). What to add:

- `speedScale` / `pitchScale` / `intonationScale` on the `/audio_query` result before
  posting to `/synthesis`; expose speed as a slider (0.75× default for A1) and persist it
  in `SettingRow` next to `selected_speaker_id`.
- A second speaker id for the **partner** role in `dialog`/`quiz` steps, so the role-play
  has two distinct voices. `synthesize()` already accepts a `speaker` argument; only the
  caller and one setting are missing.
- Per-style preview inside the dropdown rather than only for the saved selection, and a
  cancel path (selection currently saves on `onChange` with no undo).
- Surface `voicevox_client.check_voicevox()` state in the component so "no speakers found"
  distinguishes "engine down" from "engine up, empty list".

### 9.3 Improved grading logic

Replace the character-similarity core, keep the function signatures:

1. **Morphological segmentation** — `fugashi` + `unidic-lite` (pure-Python install, no
   model download) to get surface + lemma + POS.
2. **Content-word comparison** — compare bags of nouns/verbs/adjectives. This alone fixes
   肉/魚 (§2.5) because the content word differs even though 93% of the characters match.
3. **Polarity as a hard constraint** — if the target's predicate is affirmative and the
   learner's is negative (or vice versa), fail regardless of similarity. Fixes
   わかります/わかりません.
4. **Politeness equivalence table** — `ありがとう ↔ ありがとうございます`,
   `すみません ↔ すいません`, `〜て ↔ 〜てください`, `だ ↔ です`, `〜る ↔ 〜ます`. Accept
   either form when the Can-do teaches both; report which register was used so the UI can
   say "correct, and here's the polite form".
5. **Particle leniency, separately configurable** — dropping が/を in speech is normal at
   A1 and should cost a few points, not fail. Fixes 魚好きです.
6. **Stop deleting long vowels** — keep ー; make it a small penalty rather than an erasure,
   so ビール ≠ ビル.
7. **Report the measured score** and let `mastery_min_score` gate mastery on both the
   heuristic and LLM paths.
8. **Keep the LLM as a tiebreaker only** — call `llm_refine_grade` in the ambiguous band
   (say 55–80) rather than on every attempt, and stop sending it the heuristic verdict to
   anchor on.

Build the truth table from §2.5 as a pytest parametrization first; it is the fastest way to
know the new implementation is better rather than differently wrong.

### 9.4 Whisper optimization

| Change | Expected effect |
|---|---|
| `def` instead of `async def` on the handler | the API stops freezing during every decode |
| `vad_filter=True` (+ `min_silence_duration_ms`) | trims leading/trailing silence; on short push-to-talk clips this is the single largest win |
| `beam_size=1` | ~2× faster decode; at utterance length the accuracy cost is negligible |
| `condition_on_previous_text=False` | removes the classic repeated-hallucination failure |
| `without_timestamps=True` | skips timestamp alignment that is computed and thrown away |
| `initial_prompt` = the step's expected phrases | biases decoding toward lesson vocabulary — the highest-accuracy change available, and the data is already on the step |
| Warm the model in `_startup` on a background thread | removes the model-load stall from the learner's first utterance |
| Client-side trim to the voiced region before upload | less audio uploaded and decoded |
| Batch: keep one worker with a bounded queue | serializes access to a model that is not thread-safe, and makes overload behaviour predictable |
| Report `no_speech_prob` back to the UI | lets the UI say "I didn't hear anything" instead of grading silence |

### 9.5 Curriculum builder enhancements

1. **Validation gate first** (2.2) — a build that emits `3初めまして私はマルシアです…` as a
   graded target should fail loudly. Cheap, and it prevents regression once content is
   fixed.
2. **Script-first extraction for Starter** (2.3) — generalize
   `extract_scripts_elementary1.py` (CD-marker-keyed `A：`/`B：` lines, instructional text
   filtered) into a book-parameterized `extract_scripts.py`. Elementary 1 already proves
   the approach on the same codebase.
3. **Whisper as alignment, not as source** — use transcripts to match an activity to a
   track and to derive per-phrase timing offsets, not to invent the phrase text.
4. **Curated overlays as YAML** (3.8) — `content/starter/overrides/L01.yaml` merged over
   generated output; content edits stop being Python edits.
5. **Metadata enrichment** — furigana (`fugashi`), `gloss_en`, romaji, register tag, mora
   count (needed by the pronunciation mode), audio start/end offsets per phrase.
6. **Deterministic + diffable builds** — stable key order, a `schema_version`, and a
   `--check` mode that fails when regeneration would change committed YAML.
7. **A coverage report per lesson** — activities with phrases, phrases passing validation,
   Can-dos with real scenarios — so content quality is a number rather than a vibe.

### 9.6 UI responsiveness improvements

- Bounded transcript in the payload; `React.memo` per bubble with a stable key (2.8).
- Extract `useTutorSession()` and `useMicRecorder()` from `Tutor.tsx`.
- Preload the next step's book audio during TTS, and prefetch TTS chunk *n+1* while *n*
  plays.
- Hold one `MediaStream` for the lesson instead of calling `getUserMedia` per turn.
- Replace the `TutorMascot` interval with a CSS animation; preload the three frames.
- Optimistic UI on Skip/advance instead of a global `busy` that greys out the whole page.
- Barge-in (2.9).
- Bundle the fonts (1.14).
- An error boundary around the tutor route, and stop swallowing `api.progress()` failures.

### 9.7 State machine refactor

Do it in this order so each step is independently verifiable:

1. Land the fixture tests (2.10) that snapshot every substep sequence — this is the safety
   net for everything below.
2. Introduce a `Step` Pydantic model. Keep emitting the same dict; just validate it.
3. Introduce the `TutorMode` protocol and move `listen_repeat` into it. Prove the fixture
   output is byte-identical, then migrate the remaining modes one at a time.
4. Split `quiz_index` into `phase` + `phase_index` with a one-shot migration derived from
   the current `_sync_book_substep` logic, then delete `_sync_book_substep`.
5. Merge `_resolve_step` and `_lesson_step_snapshot` into `current_step(session, lesson)`.
6. Move unlock enforcement into a single `require_unlocked(db, lesson_id)` dependency used
   by every tutor route.

Determinism is preserved throughout: the substep sequence is a pure function of
`(lesson yaml, mode, phase_index)`, and quiz scenario choice stays `attempt % len(scenarios)`.

---

## 10. Recommended refactors

### 10.1 Shared base class for tutor modes

```python
class TutorMode(Protocol):
    name: str
    def substeps(self, activity: Mapping) -> Sequence[str]: ...
    def render(self, ctx: StepContext, index: int) -> Step: ...
    def expected(self, ctx: StepContext, index: int) -> list[str]: ...
    def grade(self, ctx: StepContext, index: int, utterance: str) -> Grade | None: ...
```

`MODES: dict[str, TutorMode]` replaces `FLOW_BY_MODE`, and `book_step()` becomes a lookup.
`intro_chat`, `self_check`, and `can_do_quiz` become modes too, which collapses four
special-cased states into one uniform mechanism. Modes that return `None` from `grade` are
ungraded, which is how shadowing, kana, and culture steps get expressed without new states.
No existing mode is removed; each is ported behind the fixture tests.

### 10.2 Unified audio pipeline

One frontend module owning every sound the app makes:

```
useAudioPipeline()
  ├── playBookAudio(paths)   preload, retry, degrade-to-text on 404
  ├── speak(lines)           chunked, prefetch n+1 during n, interruptible
  ├── record()               one persistent MediaStream, VAD auto-stop, level meter
  └── stopAll()              barge-in
```

This replaces `playBookTracks` (inline in `Tutor.tsx`), `speakTutor`/`playBlob`/`browserSpeak`
(`speech.ts`), and the two near-duplicate `MediaRecorder` blocks in `startListening` and
`askByVoice` — which is also where the skip/record race (§3.2) lives. On the backend,
`prepare_for_voicevox` becomes the single normalizer and `speakableText` is deleted, so TTS
text cleanup exists once.

### 10.3 Centralized Whisper handling

```
whisper_service
  ├── warm()                     called from startup, background thread
  ├── transcribe(audio, *, hint) VAD-trimmed, biased by expected phrases
  └── status()                   honest: loaded / loading / failed, with the real error
```

One bounded-queue worker serializes access to a model that is not thread-safe, the route
becomes `def` so FastAPI's threadpool handles it, options live in `Settings` instead of
being hardcoded, and `whisper_status()` stops claiming `ok: true` for a model that has
never been loaded.

### 10.4 Consistent YAML schema

One Pydantic model tree (`LessonFile`, `Activity`, `CanDo`, `QuizScenario`, `IndexFile`)
used by both builders at write time and by `curriculum_loader` at read time. Add
`schema_version: 1` to new output and treat a missing version as v0 with a shim that fills
`book_title`/`book_id` and normalizes the two index envelopes — existing files keep loading
untouched, which satisfies the compatibility constraint. `docs/CURRICULUM_SCHEMA.md` becomes
generated from the models rather than hand-maintained.

### 10.5 Modular lesson flow controller

```
LessonFlowController(lesson, session)
  ├── current() -> Step
  ├── advance() -> Step                 # skip / next
  ├── submit(utterance) -> (Grade, Step)
  └── progress() -> ProgressSnapshot
```

The orchestrator becomes a thin transactional wrapper: load, delegate, persist, log. The
controller holds `(phase, phase_index)` explicitly, which lets `_sync_book_substep`,
`_resolve_step`, and `_lesson_step_snapshot` all be deleted, and makes the state machine
directly unit-testable without a database.

---

## 11. Highest-ROI work for the next cycle

Ranked by learner-visible value divided by risk. Everything here is Tier 1 or Tier 2, and
none of it touches the mode set, the determinism guarantees, or the YAML contract.

| Rank | Work | Why it is worth the most |
|---|---|---|
| 1 | **Token-aware grading + honest scores** (2.1, 1.3) | Grading is the product. Today it passes 肉が好きです for 魚が好きです and fails ありがとう for ありがとうございます, then reports both outcomes as `100%`. Nothing else improves the learning loop as much, and the truth table in §2.5 makes "better" measurable. |
| 2 | **Unstick the learner** (1.1, 1.2, 1.8, 1.9) | Three independent ways to end up stuck or to lose work — the silent Can-do loop, the skip/record race, and the transcript-wiping jump button — plus an unlock rule that does not run. Roughly 20 lines total. |
| 3 | **Caching: YAML + TTS** (1.5, 1.6) | ~50 ms per turn and ~500 ms off `/progress`, and 105 fewer VOICEVOX round trips per lesson, for two `lru_cache`s. The best effort-to-latency ratio in the codebase. |
| 4 | **Whisper: unblock and tune** (1.4, 1.7) | One keyword stops the API freezing during every decode; `vad_filter` + greedy decoding + an `initial_prompt` built from the step's expected phrases cut both latency and error rate using data the step already carries. |
| 5 | **Curriculum validation gate** (2.2) | Cheap, and it converts "the content is bad in ways we rediscover" into a build failure with a per-lesson number. Prerequisite for trusting any content fix. |
| 6 | **Fixture tests + CI** (2.10) | There is currently no test of any kind. A snapshot of every substep sequence for five lessons plus a grading truth table is a day of typing that makes every Tier 3 refactor safe instead of speculative. |
| 7 | **Move Starter L03–L18 off Whisper** (2.3) | The largest content-quality win available, and Elementary 1 already demonstrates the technique on the same codebase. |
| 8 | **Speech rate control** (2.12) | Small change, disproportionate perceived value for A1 — and it makes the existing shadowing mode genuinely usable. |

Deliberately **not** in the next cycle: the `TutorMode` base class, the `quiz_index` split,
and the typed `Step` contract. They are the right end state and they are the reason §10
exists, but each one rewrites code that currently has zero test coverage. Land item 6 first
and they become routine.

---

## 12. Implementation status

Tracked on branch `cursor/implement-audit-fixes-43e9` — [PR #3](https://github.com/sgzed86/JTutor/pull/3).

### Tier 1

| Item | Status |
|---|---|
| 1.1–1.13, 1.15–1.16 | Done |
| 1.14 Bundle fonts | Done — `@fontsource` in desktop app (no Google Fonts CDN) |
| 1.17 Dead code | Done — unused imports cleaned (`orchestrator`, `progress`) |

### Tier 2

| Item | Status |
|---|---|
| 2.1 Grading | Done — polarity, topic, equiv table, long vowels (heuristic); optional fugashi deferred |
| 2.2 Validator + CI | Done — non-strict in CI |
| 2.3 Starter scripts | Done — extractor + builder; regen YAML locally when PDF extract exists |
| 2.4 Pronunciation mode | Done — `pronunciation` book_mode |
| 2.5 Vocab drill | Done — `vocab_drill` book_mode |
| 2.6 Grammar grading | Done — grades `examples` / point text, not 2-char pass |
| 2.7 L00 / kana | Done — `kana_trace`, L00 `book_mode` |
| 2.8 Bounded payload | Done |
| 2.9 Barge-in | Done — stop speaking + mic during TTS |
| 2.10 Flow tests | Done — `test_flow_snapshots.py`, `pytest-asyncio` |
| 2.11 Ask Yuki budget | Done — capped phrases + `recent_turns` |
| 2.12 Speech rate | Done |
| 2.13 Error surfaces | Partial — global handler, VoiceVox 503 copy; Setup link in UI still minimal |

### Tier 3 (structural — foundations only)

| Item | Status |
|---|---|
| 3.1 TutorMode base | **Foundation** — `tutor_mode_protocol.py`; modes still in `lesson_flow` |
| 3.2 phase + phase_index | **Open** — needs migration |
| 3.3 Typed Step | **Open** — large TS sweep |
| 3.4 Unified audio hook | **Partial** — `speechControl.ts` barge-in; full `useAudioPipeline` not extracted |
| 3.5 Whisper worker queue | **Partial** — model lock + warm; no bounded queue API |
| 3.6 Canonical schema | **Partial** — `schema_version` shim, `docs/CURRICULUM_SCHEMA.md` |
| 3.7 Book registry | **Partial** — runtime `backend/app/books.py`; scripts keep `scripts/books.py` for builds |
| 3.8 YAML overlays | **Open** |
| 3.9 New pedagogy steps | **Open** |

**Manual:** run `python scripts/extract_scripts.py starter` + `build_curriculum.py`, then `validate_curriculum.py --strict` when content is clean.
