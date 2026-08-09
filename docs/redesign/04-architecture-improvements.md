# 04 — Architecture improvements

Refactors that make the redesign in [02](02-ui-redesign-plan.md) implementable
without destabilising deterministic lesson progression.

The governing rule for everything below: **the orchestrator remains the only
component that decides what step comes next.** Refactors change *where code
lives*, not *who decides*.

---

## 1. Backend

### 1.1 The orchestrator is a 998-line `if/elif` machine written three times

`backend/app/orchestrator.py` branches on `session.state` in three separate
places that must be kept in agreement:

| Function | Branches on `state` | Purpose |
|----------|--------------------|---------|
| `advance()` | `lesson_intro`, `intro_chat`, `book`, `grammar`, `self_check`, `can_do_quiz` | Skip / next |
| `user_message()` | the same six, in a different order, with different fallthrough | Grade an utterance |
| `_lesson_step_snapshot()` / `_resolve_step()` | the same six again | Rebuild the current step |

Adding a mode means editing three ladders and hoping they agree. `_resolve_step`
and `_lesson_step_snapshot` are near-duplicates of each other; the difference
(one takes a `db`, one does not) is not documented.

**Refactor — a `LessonPhase` protocol and a registry.**

```python
class LessonPhase(Protocol):
    name: str
    def enter(self, ctx: FlowContext) -> Step: ...
    def current_step(self, ctx: FlowContext) -> Step: ...
    def advance(self, ctx: FlowContext) -> Transition: ...
    def on_user_text(self, ctx: FlowContext, text: str, *, spoken: bool) -> Transition: ...
```

`Transition` is a small dataclass: `next_phase | None`, `messages_to_append`,
`grade | None`, `side_effects` (SRS enqueue, can-do result). `FlowContext`
carries `db`, `session`, `lesson`, `messages` and the settings snapshot.

Six implementations — `IntroPhase`, `IntroChatPhase`, `BookPhase`,
`GrammarPhase`, `CanDoQuizPhase`, `SelfCheckPhase`, `CompletePhase` — replace
the three ladders. `orchestrator.py` becomes a thin dispatcher:

```python
PHASES: dict[str, LessonPhase] = {p.name: p for p in (...)}

async def advance(db, lesson_id):
    ctx = FlowContext.load(db, lesson_id)
    return apply(ctx, PHASES[ctx.session.state].advance(ctx))
```

Determinism is *improved*, not risked: every transition becomes an explicit,
testable value rather than an implicit sequence of mutations spread across a
function.

### 1.2 A shared base class for the book sub-step modes

`lesson_flow.book_step()` is a 150-line function with one `if sub == …` block per
sub-step, mixing script text, audio selection, step-dict construction and UI
hints. `book_modes.FLOW_BY_MODE` already declares the sequences cleanly; the
per-sub-step behaviour should live next to it.

```python
@dataclass(frozen=True)
class SubStepSpec:
    name: str                    # "listen" | "shadow" | "repeat" | ...
    expects_speech: bool
    auto_advances: bool
    plays_audio: bool
    graded: bool

class BookSubStep(Protocol):
    spec: SubStepSpec
    def render(self, activity: dict, lesson: dict, index: int) -> RenderedStep: ...
    def expected_phrases(self, activity: dict, index: int) -> list[str]: ...
```

`RenderedStep` bundles `(jp, en, step_dict)`, which the code already passes
around as a bare tuple.

This directly removes the duplication that
[01 §4.3](01-ux-audit.md#4-inconsistencies) documents: `expects_speech` and
`auto_advances` become properties of the sub-step, so `speech_substeps()` and
`auto_advance_substeps()` are derived from one table rather than being three
independent hardcoded sets (backend module-level, `lesson_flow` per-branch, and
the client's inline list).

**Constraint check:** the six `FLOW_BY_MODE` sequences and the strings they
contain do not change. `substep_at()` keeps returning the same names for the
same `quiz_index`. Sessions persisted before the refactor resume identically —
which the golden-transcript tests in §3 will assert.

### 1.3 The step payload should be self-describing

The client currently guesses. Add to every step dict:

```jsonc
{
  "substep": "repeat",
  "substep_index": 2,
  "substeps": ["listen", "repeat", "repeat", "repeat"],
  "auto_advance": false,
  "expects_speech": true,
  "graded": true,
  "audio": [{ "path": "...", "duration_s": 3.4, "transcript": "おはよう" }],
  "segment": { "index": 1, "total": 4, "can_do_id": "CD_L01_01",
               "title_en": "Greetings when you meet someone" }
}
```

Consequences:

- The client deletes its hardcoded auto-advance list.
- The per-activity segmented progress bar ([02 §3.5](02-ui-redesign-plan.md))
  becomes drawable.
- The context panel's Script tab gets its transcript without a second request
  (`content/<book>/audio_transcripts.json` already exists).
- `segment` powers the session structure in [02 §3.6](02-ui-redesign-plan.md)
  with no orchestrator change — it is computed from `can_do_id` runs.

Keep the current keys alongside the new ones for one release so nothing breaks
mid-migration.

### 1.4 Stabilise the response envelope

`_payload()` conditionally includes `self_checks` only when a `db` is passed, and
five of the eight call sites do not pass one. Make the envelope fixed and typed:

```python
class TutorPayload(BaseModel):
    session_id: int
    lesson_id: str
    state: str
    activity: Activity | None
    step: Step | None
    messages: list[Message]
    can_dos: list[CanDo]
    self_checks: list[SelfCheckSummary]      # always present
    progress: ProgressSnapshot
    grade: Grade | None
    next_lesson_id: str | None
```

Pydantic response models also give FastAPI a real OpenAPI schema, from which the
TypeScript client types in §2.1 can be generated instead of hand-written.

### 1.5 One grading module with one configuration

Today: `DEFAULT_PASS_THRESHOLD = 58`, `SOFT_PASS_THRESHOLD = 48`,
`settings.mastery_min_score = 80` (used only by the LLM refiner), a `quiz_grade`
floor that rewrites failing scores to 40, and `hybrid_grade` as a redundant alias.

```python
@dataclass(frozen=True)
class GradingPolicy:
    pass_threshold: float          # from grading_strictness: 48 / 58 / 70
    soft_pass_threshold: float
    spoken_soft_pass: bool
    can_do_min_score: int          # 80 — NOT user-adjustable

def grade(text: str, expected: Sequence[str], *, spoken: bool,
          policy: GradingPolicy) -> Grade: ...
```

Delete `hybrid_grade`. Keep `grade_phrases`' Japanese normalization untouched —
the kana/kanji variants, katakana folding and n-gram blend are good work and the
golden tests in §3 must pin their current behaviour before anything moves.

The user-facing **Grading strictness** setting from
[02 §6.4](02-ui-redesign-plan.md) maps to `pass_threshold` only. Can-do unlock
thresholds stay fixed so progression cannot be gamed by a settings change.

### 1.6 Ask Yuki: keep the isolation, fix the ergonomics

`answer_question()` already does the important thing — snapshot
`state`/`activity_id`/`quiz_index`, mark the reply `help: true`, restore the
snapshot. Preserve that exactly and additionally:

- **Make it a documented, tested invariant.** A test that asserts the tuple is
  unchanged across `answer_question` for every phase.
- **Close the client-side hole.** The server keeps its promise; the client breaks
  it ([01 §2.12](01-ux-audit.md#212-asking-a-question-can-silently-advance-the-lesson)).
  Mark the response so the client cannot mistake a help reply for a step
  transition: add `"kind": "help"` at the payload level and `"replay": false`
  on the echoed step, and have `useTutorMachine` ignore `auto_advance` and
  `play_audio` on any payload whose `kind` is `help`. A contract test should
  assert that `POST /ask` never yields a payload the client would act on as a
  transition.
- **Stream the answer.** `POST /tutor/{id}/ask` becomes an SSE or chunked
  endpoint using Ollama's `stream: true`, so the panel fills in progressively
  instead of freezing for tens of seconds.
- **Make it cancellable.** Honour client disconnect and pass a
  `httpx.Timeout(connect=5, read=60)` instead of a flat 120 s.
- **Separate the channel.** Help replies currently land in the same `messages`
  array as lesson turns, distinguished only by `kind: "question"` and
  `step.help`. Give them their own `help_messages` list so the context panel and
  the lesson transcript stop competing for one array.
- **Pre-flight.** If `/health` reports Ollama down, answer instantly from the
  existing `_ollama_lesson_help` fallback and label it, instead of waiting for a
  timeout.
- **Cache** identical `(lesson_id, step signature, question)` answers — learners
  ask "what do I say here?" repeatedly.

### 1.7 Whisper: centralize and stop blocking the event loop

Two problems, both in `backend/app/routes/voice.py`:

```python
@router.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    ...
    result = transcribe_file(tmp_path, language="ja")   # blocking, CPU-bound
```

`transcribe_file` runs `faster-whisper` synchronously inside an `async def`
handler, so **the entire FastAPI event loop is blocked for the duration** — every
other route, including `/health`, stalls. On the first call it also blocks while
the model downloads and loads.

```python
class TranscriptionService:
    def __init__(self, model: str, device: str) -> None:
        self._pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="whisper")
        self._ready = asyncio.Event()

    async def warm(self) -> None:                     # called from lifespan
        await asyncio.get_running_loop().run_in_executor(self._pool, self._load)
        self._ready.set()

    async def transcribe(self, path: Path, *, language: str = "ja") -> Transcript:
        await self._ready.wait()
        return await asyncio.get_running_loop().run_in_executor(
            self._pool, self._transcribe_sync, path, language)

    def status(self) -> dict: ...                     # loading | ready | error | downloading
```

Points:

- A **single worker** serialises GPU/CPU use and bounds memory.
- **Warm at startup** from the `lifespan` handler so the first recording does not
  pay the load cost.
- **Expose the state** via `GET /voice/model-status` so the UI can show
  "Preparing speech recognition…" instead of appearing hung.
- Accept a `language` parameter — `intro_chat` explicitly invites answers in the
  learner's own language, yet transcription is hardcoded to `ja`.
- Keep the raw segments; `avg_logprob` and `no_speech_prob` are useful signals
  for "I didn't hear that" versus "you said something wrong".

The same treatment applies to the sync SQLAlchemy calls in async handlers. They
are individually fast, but the pattern is the same; either use
`run_in_executor` or make the routes `def` instead of `async def` so Starlette
runs them in its threadpool.

### 1.8 Unified audio / TTS pipeline

Server side:

```python
class SpeechService:
    async def synthesize(self, text: str, *, speaker: int,
                         speed: float = 1.0, pitch: float = 0.0) -> bytes
```

with:

- **A disk cache** keyed by `sha1(normalized_text | speaker | speed | pitch)`
  under `<data_dir>/tts-cache/`, bounded by an LRU sweep. Fixed tutor lines —
  `よくできました。`, `もういちど いってください。`, every scripted prompt — are
  currently re-synthesised on every occurrence, two HTTP round-trips each.
- **One normalization**, shared. `speech.ts::speakableText` and
  `voicevox_client.prepare_for_voicevox` must not both exist; the server owns it
  and the client sends raw text.
- **Explicit `speedScale`/`pitchScale`** passed into the VOICEVOX `audio_query`,
  wiring [02 §6.1](02-ui-redesign-plan.md).
- **A pre-warm pass** that synthesises the next step's tutor line while the
  current one plays.
- **Honest degradation**: when VOICEVOX is unreachable, return
  `503` with a machine-readable `reason` so the client can switch to the system
  voice *and say so*, rather than inferring it from a thrown exception.

### 1.9 Error handling

- Replace `raise HTTPException(503, f"VoiceVox error: {e}")` string interpolation
  with a typed problem envelope: `{ "error": { "code": "voicevox_unavailable",
  "message": "...", "hint": "Start VOICEVOX and try again", "retryable": true } }`.
  The UI in [02 §7.5](02-ui-redesign-plan.md) depends on `code` and `retryable`.
- Fix the 15 `B904` findings (`raise … from e`) so tracebacks keep their cause.
- Replace the four silent `except Exception: pass` blocks
  (`voicevox_client.get_selected_speaker_id`,
  `voicevox_client.set_selected_speaker_id`, the `db.init_db` migration and
  `curriculum_loader._active_book_id`) with logged warnings.
- Delete the dead code listed in [01 §4.8](01-ux-audit.md#4-inconsistencies) and
  the 11 unused imports; add `ruff` to CI so they cannot come back.

### 1.10 Configuration and security

- `allow_origins=["*"]` with `allow_credentials=True` is both invalid per the
  CORS spec and unnecessary for a loopback API. Restrict to the app origin and
  add the per-run token from [03 §5](03-startup-modernization.md).
- `media.get_audio` correctly refuses `..` and enforces the `assets/audio/`
  prefix; keep that check and add the same discipline to `get_pdf`, which builds
  a filename from a book record but should still resolve and verify containment.
- Replace the deprecated `@app.on_event("startup")` with `lifespan`, which is
  also where Whisper warming and cache setup belong.
- Resolve `_UI_DIR` lazily inside the route rather than at import time, so a UI
  built after the server starts is still served.

---

## 2. Frontend

### 2.1 Types

54 `any` occurrences, 20 of them in `Tutor.tsx`; `session` is `any` end to end.
Generate the client types from the FastAPI OpenAPI schema (`openapi-typescript`)
once §1.4 lands, and turn on `noImplicitAny` plus `strict` in
`apps/desktop/tsconfig.json`. Everything the tutor screen does is driven by the
shape of `session`; typing it is what makes the rest of the refactor safe.

### 2.2 Break up `Tutor.tsx`

586 lines holding: routing, data fetching, TTS orchestration, book-audio
playback, two independent `MediaRecorder` flows, the auto-advance rules, error
state, ask state, self-check state and the whole layout. Split as in
[02 §2](02-ui-redesign-plan.md):

- `useTutorSession` — all API calls, `AbortController` per request, typed result.
- `useTutorMachine` — the `TutorPhase` union, derived from payload + I/O state.
- `useAudioPipeline` — one `AudioContext`, queue, prefetch, cancel, level.
- `useRecorder` — one recorder, analyser, VAD, device selection.

The two near-duplicate recorder implementations (`startListening` and
`askByVoice`, ~70 lines each, differing only in what they do with the transcript)
collapse into one hook with a `purpose: "answer" | "question"` argument. The
`recordingModeRef` guard that exists to stop them interfering disappears with
them.

### 2.3 Remove the client's copy of the state machine

Delete the hardcoded auto-advance list and the two label maps; consume
`step.auto_advance`, `step.substeps` and `step.substep_index` from §1.3, and
move the display strings into one `stepLabels.ts` that both `tutorDisplay.ts` and
`ModeCard` import. `lib/tutorDisplay.ts` shrinks to formatting; the
mode/sub-step vocabulary has exactly one definition on each side of the wire.

### 2.4 Styling

Adopt CSS Modules per component and the token set from
[02 §7.1](02-ui-redesign-plan.md); delete the 50 inline style objects. Add
`stylelint` to CI to keep raw hex values out of components.

### 2.5 Client resilience

- Every fetch gets an `AbortController` and a timeout.
- A `useHealth()` hook polling `/health` on a slow interval drives the service
  indicator and the degraded-mode banners.
- A React error boundary around the stage so one bad payload does not white-screen
  the app.
- Retry with backoff on transient network failures, surfaced as a "Reconnecting…"
  chip rather than an error banner.

---

## 3. Testing — the prerequisite for all of the above

There are currently no tests and no CI. Given the constraint "do not break
deterministic lesson progression", tests are not a nice-to-have; they are the
mechanism by which that constraint is enforced. **Write them before the
refactors, against the current behaviour.**

### 3.1 Golden transcripts (highest value)

A harness that drives a lesson through the orchestrator with a scripted set of
learner utterances and records every `(state, activity_id, quiz_index, substep,
expect_speech, play_audio)` tuple to a snapshot file:

```python
def test_l01_golden(tmp_db):
    trace = run_lesson("L01", answers=SCRIPTED_ANSWERS_L01)
    assert trace == load_golden("L01.jsonl")
```

Generate goldens for all 37 lessons **now**, from the current code. Any refactor
that changes a single tuple fails loudly. This is the single highest-leverage
piece of work in this document.

### 3.2 Unit tests

- `phrase_grade`: a table of (utterance, expected, verdict) covering the
  kanji/kana variants, katakana folding, the soft-pass path and the containment
  shortcuts.
- `book_modes.flow_substeps` for each mode, including `listen_repeat_all` with
  0, 1 and N phrases.
- `lesson_unlock` / `check_lesson_mastery` across book boundaries (`L18` → no
  next, `EL01` numbering).
- `lesson_progress_snapshot` monotonicity: the fraction never decreases as a
  session advances.
- `free_response.intro_questions` normalization for strings and dicts.

### 3.3 Content validation

A `pytest` that loads all 37 YAML files against a Pydantic schema and asserts:
every `activity.can_do_id` resolves to a declared can-do; every `audio` path is
well-formed; `dialog` activities have a `dialog_script` with both speakers;
`book_mode` is a known value. Run in CI so a curriculum rebuild cannot silently
ship a broken lesson. Today 19 activities have no `book_mode` and nothing warns.

### 3.4 API contract tests

`httpx.AsyncClient` against the app: start → advance → message → self-check →
complete for one lesson, asserting the response envelope shape (§1.4) and that
`POST /ask` leaves `state`, `activity_id` and `quiz_index` untouched.

### 3.5 Frontend

- Vitest for `tutorDisplay`, the phase reducer and the VAD logic.
- React Testing Library for `TutorStage` across every `TutorPhase`, asserting
  that exactly one status string and one primary action render.
- A Playwright smoke test against a stubbed backend covering the golden path.

### 3.6 CI

`.github/workflows/ci.yml`: `ruff`, `mypy` (backend), `tsc --noEmit`, `eslint`,
`vitest`, `pytest`, content validation, then `build:ui` and `build:backend` on
tags.

---

## 4. Consistent YAML schema

The content is already close to consistent; the gaps are documented in
[01 §5](01-ux-audit.md#5-content-level-findings). Make it explicit and validated
rather than reformatting it.

### 4.1 Formalise the current shape

Write `backend/app/schema.py` with Pydantic models mirroring
`docs/CURRICULUM_SCHEMA.md`, and load lessons through it. All existing files must
validate unchanged — the model encodes what is already true, with defaults for
the optional fields (`book_mode: "listen_repeat"`, `picture_has_image: false`,
`dialog_script: []`, …).

### 4.2 Additive fields, each with a default

| Field | Level | Default | Why |
|-------|-------|---------|-----|
| `schema_version` | lesson | `1` | Lets future loaders migrate deliberately |
| `book_mode` | activity | `listen_repeat` | Make the existing implicit default explicit; fill in the 19 missing ones |
| `segment_title_en` | activity | derived from `can_do_id` | Session structure ([02 §3.6](02-ui-redesign-plan.md)) |
| `estimated_seconds` | activity | derived from audio duration | "About 12 minutes left" |
| `notes_en` | activity | `null` | Context-panel Notes tab |
| `readings` | `phrase_meta` entry | `null` | Optional furigana |

### 4.3 Keep the two books symmetric

`book_id` is present in the 18 Elementary 1 files and absent from the 19 Starter
files (it is defaulted at load time). Write it explicitly during the next
curriculum rebuild so the on-disk files are self-describing.

### 4.4 Generator alignment

`scripts/build_curriculum.py` and `build_curriculum_elementary1.py` currently
diverge in which optional fields they emit. Give both a shared writer that emits
the full schema with defaults, so `book_section_*` stops appearing on 4 of 791
activities by accident.

---

## 5. How each refactor protects deterministic progression

| Refactor | Risk | Guard |
|----------|------|-------|
| `LessonPhase` registry | Reordered or dropped transitions | Golden transcripts for all 37 lessons, generated before the change |
| `BookSubStep` base class | Different sub-step sequence | `flow_substeps()` unit tests per mode; goldens |
| Grading policy consolidation | Different pass/fail verdicts | Grading table tests pinned to current outputs; `can_do_min_score` stays fixed and non-configurable |
| Whisper thread pool | Reordered concurrent transcriptions | Single worker, so ordering is preserved; sessions are per-lesson and serialised anyway |
| Streaming Ask Yuki | Accidental state mutation | Existing snapshot/restore kept; add an explicit invariant test |
| Self-describing step payload | Client and server disagreeing | Old keys retained for one release; contract test asserts both |
| YAML schema models | A currently-valid file failing to load | Validation test over all 37 files runs in CI from day one |
| Frontend phase machine | Client advancing on its own | The phase union has no transition that calls `advance()` implicitly; auto-advance still fires only when the **server** sets `auto_advance` |

---

## 6. Suggested module layout after the refactors

```
backend/app/
  main.py                 # app factory, lifespan, routers
  config.py
  schema.py               # NEW  Pydantic curriculum models
  flow/
    __init__.py
    context.py            # FlowContext, Transition
    phases/
      intro.py  intro_chat.py  book.py  grammar.py  can_do.py  self_check.py
    substeps/
      base.py             # SubStepSpec, BookSubStep
      listen.py  shadow.py  repeat.py  select.py  dialog.py
    registry.py           # FLOW_BY_MODE + phase registry (single source of truth)
  grading/
    policy.py  japanese.py  llm_refine.py
  speech/
    tts.py                # SpeechService + cache
    stt.py                # TranscriptionService + worker pool
    text.py               # THE normalization, used by both
  services/
    progress.py  srs.py  self_check.py  books.py  curriculum.py
  routes/                 # thin; no business logic
tests/
  golden/                 # L00.jsonl … EL18.jsonl
  test_flow_golden.py  test_grading.py  test_content_schema.py  test_api_contract.py
```

```
apps/desktop/src/
  api/            client.ts  types.gen.ts  errors.ts
  state/          useTutorSession.ts  useTutorMachine.ts  useSettings.ts  useHealth.ts
  audio/          useAudioPipeline.ts  useRecorder.ts  vad.ts  waveform.ts
  components/     shell/  rail/  stage/  transport/  context/  settings/  onboarding/  feedback/
  styles/         tokens.css  themes.css  reset.css
```
