# 02 — UI/UX redesign plan

Target: a calm, single-purpose desktop app where a learner opens Jtutor, sees
where they are, presses one obvious control, and gets unambiguous feedback.

Every mode, state and grading rule described in
[01 §7](01-ux-audit.md#7-what-is-already-good-and-must-be-kept) is preserved.
This plan changes presentation and adds client affordances; it does not move
sequencing decisions off the server.

---

## 1. Layout

### 1.1 Application shell

Replace the flat six-item sidebar with a two-zone shell.

```
┌────────────────────────────────────────────────────────────────────────┐
│  Title bar:  Jtutor   [Irodori Starter ▾]        ● Services   ⚙︎        │
├──────────────┬───────────────────────────────────┬─────────────────────┤
│              │                                   │                     │
│  LEFT RAIL   │        CENTER STAGE               │   CONTEXT PANEL     │
│  280px       │        fluid, min 560px           │   340px, collapsible│
│              │                                   │                     │
│  Lesson map  │   Avatar + phrase card + mic      │   Ask Yuki          │
│  Progress    │   Step chrome                     │   Grammar notes     │
│  Review (SRS)│                                   │   Audio script      │
│              │                                   │   Vocabulary        │
│              │                                   │                     │
├──────────────┴───────────────────────────────────┴─────────────────────┤
│  Transport bar (fixed): ◀ replay │ ⏸ pause │ status │ ▶ next  │ ⋯      │
└────────────────────────────────────────────────────────────────────────┘
```

Rules:

- **The center stage never scrolls.** It is a fixed-height flex column. If
  content does not fit, the phrase card shrinks its type scale, it does not push
  the mic off-screen.
- **The transport bar is fixed to the bottom of the window.** The primary action
  is always in the same pixel position, in every step, in every mode. This is the
  single highest-value change in this document.
- **The context panel is collapsible** and remembers its state. Collapsing it
  gives the stage the full width for role-play.
- **The left rail is scrollable and independent.** Changing lesson never
  re-renders the stage layout, only its contents.

Grid implementation:

```css
.app-shell {
  display: grid;
  grid-template-columns: var(--rail-w) minmax(560px, 1fr) var(--ctx-w);
  grid-template-rows: var(--titlebar-h) 1fr var(--transport-h);
  grid-template-areas:
    "titlebar titlebar titlebar"
    "rail     stage    context"
    "transport transport transport";
  height: 100vh;
}
@media (max-width: 1180px) { /* context panel becomes an overlay drawer */ }
@media (max-width: 900px)  { /* left rail becomes an overlay drawer */ }
```

### 1.2 Left rail — lesson map + progress

Three stacked sections, all driven by the existing `GET /progress` payload:

1. **Today** — one card: current lesson, the `lesson_progress_snapshot` label
   ("Book · activity 7/28"), a ring showing `percent`, and how many can-dos are
   mastered. A single primary button, *Continue* or *Start*.
2. **Lessons** — a vertical list grouped by `topic_en` (the field already repeats
   across lesson pairs, e.g. "Food" covers L05–L06). Each row: lesson id, title,
   a 3-dot can-do indicator, and a state chip.
   - `locked` — lock glyph, dimmed **and** non-interactive with a tooltip naming
     the blocking lesson. Never opacity alone.
   - `available`, `in progress` (shows the fraction), `mastered` (check).
   - The current lesson gets a left accent bar and is scrolled into view on mount.
3. **Review** — SRS due count and a *Review* button. Hidden entirely when both
   `due` and `total` are 0, instead of showing an enabled button over an empty
   deck.

The standalone `/progress` route stays as a full-page view of the same data for
users who want the overview, but it is no longer required to navigate.

### 1.3 Center stage — tutor interaction

Fixed vertical rhythm, top to bottom:

| Band | Content | Height |
|------|---------|--------|
| Step header | `Activity 7 of 28` · mode chip · sub-step chip | 40 px |
| Instruction | **One** sentence. The single owner of "what do I do now" | 2 lines max |
| Presence | Avatar (200 px) beside the tutor's line, JP over EN | 240 px |
| Focus card | The say-this card, the shadow card, or the picture prompt | flex |
| Feedback | Grade result, inline, reserved space so nothing jumps | 72 px reserved |

The three cards in the focus band are mutually exclusive and share one
`<FocusCard>` component with a `variant` prop, replacing the current pair of
near-duplicate `say-target-card` / `shadow-card` blocks.

### 1.4 Right context panel

Tabs, not stacked panels, so height is predictable:

- **Ask Yuki** — the conversation with Yuki *about* the lesson. Question history
  is kept here and visually separated from the lesson transcript.
- **Notes** — grammar points for the lesson (`lesson.grammar`, already loaded)
  filtered to the current activity's `can_do_id` where possible.
- **Script** — for role-play steps, `activity.dialog_script` with the partner and
  learner lines colour-coded to match the book's yellow/orange. For other tracks,
  fall back to `content/<book>/audio_transcripts.json`, with two caveats: that
  file is Whisper output and visibly noisy (`"一あお久しぶりです…"`), and it is
  currently excluded from packaged builds by the `!**/audio_transcripts.json`
  filter in `package.json` and by `make_release.ps1`. Either clean it and ship
  it, or show the dialog script only and hide the tab for non-dialog tracks.
- **Words** — `activity.key_phrases` and `lesson.vocab` for the current activity,
  each with a speaker button.

Three of these four sources (grammar, dialog script, key phrases and vocab) are
already in the lesson YAML that every build ships; only the audio transcript
needs a packaging decision.

### 1.5 Transport bar

Left to right: **Replay tutor line**, **Replay book audio**, **Pause**, a status
region, the **primary action**, and an overflow `⋯` menu.

The primary action is a single button whose label and behaviour come from one
derived value:

| Tutor state | Button | Behaviour |
|-------------|--------|-----------|
| `speaking` | *Skip line* | Stops TTS, moves to the audio/step that follows |
| `playing_audio` | *Skip audio* | Stops playback, continues the step |
| `awaiting_speech` | *Hold to speak* / *Stop* | Starts/stops recording |
| `transcribing` / `grading` / `thinking` | *Cancel* | Aborts the in-flight request |
| `idle_can_continue` | *Next* | `POST /tutor/{id}/advance` |
| `lesson_complete` | *Start L02* | Navigates |

The destructive and developer tools — *Restart lesson*, *Jump to Can-do quiz*,
*Can-do (reset progress)* — move into the `⋯` menu. *Restart lesson* gets a
confirmation. The two can-do jump items move behind a **Developer tools** toggle
in Settings, off by default.

---

## 2. Component inventory

New or reshaped components. Paths are proposals under
`apps/desktop/src/components/`.

| Component | Replaces / adds | Responsibility |
|-----------|-----------------|----------------|
| `shell/AppShell` | `App.tsx` layout | Grid, drawers, responsive breakpoints |
| `shell/TitleBar` | sidebar brand + `BookSwitcher` | Book switch, service indicator, settings entry |
| `shell/ServiceIndicator` | the four pills | One dot + popover listing each service, its purpose, and a fix action |
| `rail/TodayCard` | dashboard "Current lesson" | Continue CTA + ring progress |
| `rail/LessonList` + `LessonRow` | `ProgressMap` tiles | Grouped, chipped, keyboard navigable |
| `rail/ReviewCard` | dashboard SRS card | Hidden when empty |
| `stage/TutorStage` | existing `TutorStage` | Layout only — no business logic |
| `stage/StepHeader` | `tutor-stage-header` + `ModeCard` | Activity position, mode chip, sub-step chip |
| `stage/Instruction` | `tutor-instruction` | The one instruction string |
| `stage/Avatar` | `TutorMascot` | See §4 |
| `stage/SpeechBubble` | `tutor-speech-bubble` | JP line, EN gloss, replay button |
| `stage/FocusCard` | `say-target-card` + `shadow-card` + `tutor-picture-hint` | `variant: "say" \| "shadow" \| "picture" \| "listen-preview"` |
| `stage/GradeResult` | `PronunciationFeedback` | Adds per-token diff, attempt history |
| `transport/TransportBar` | the 4-button row | Fixed primary action + overflow |
| `transport/MicButton` | inline button | Press-and-hold or toggle, keyboard `Space` |
| `transport/WaveformMeter` | *new* | See §5 |
| `transport/StatusPill` | `status` + `presenceHint` | Single source, `aria-live="polite"` |
| `context/ContextPanel` | *new* | Tab host |
| `context/AskYukiTab` | `tutor-ask-panel` | Non-blocking, cancellable, history |
| `context/NotesTab` | *new* | Grammar points |
| `context/ScriptTab` | *new* | Audio transcript + dialog script |
| `context/WordsTab` | *new* | Key phrases + vocab with TTS |
| `settings/SettingsDialog` | `pages/Settings.tsx` | See §6 |
| `onboarding/SetupWizard` | `pages/Setup.tsx` | See §7.4 |
| `feedback/ErrorToast` | the red banner | Auto-dismiss, retry action, severity |

### Shared hooks

| Hook | Replaces | Notes |
|------|----------|-------|
| `useTutorSession(lessonId)` | ~200 lines of `Tutor.tsx` | Owns fetch/advance/message/ask, exposes a typed session |
| `useTutorMachine(session)` | scattered booleans | Derives the single `TutorPhase` (§3.1) |
| `useAudioPipeline()` | `speech.ts` + inline `new Audio()` | See §5 |
| `useRecorder(deviceId)` | `startListening`/`askByVoice` | One recorder, analyser node, VAD |
| `useSettings()` | *new* | Persisted UI preferences |

`Tutor.tsx` shrinks from 586 lines to a composition root of roughly 80.

---

## 3. Interaction flow

### 3.1 One state machine, one source of truth

Today "what is happening" is spread over `busy`, `recording`, `speaking`,
`asking`, `status`, `speakingRef`, `handlingRef`, `recordingModeRef` and
`session.step.expect_speech` — nine values that can disagree, which is exactly
how the screen ends up saying "Listening to you…" with no microphone.

Replace with one discriminated union in the client:

```ts
export type TutorPhase =
  | { kind: "loading" }
  | { kind: "speaking";       line: string }
  | { kind: "playing_audio";  track: string; index: number; total: number }
  | { kind: "awaiting_speech"; target: string | null; deadlineMs: number }
  | { kind: "recording";      startedAt: number; level: number }
  | { kind: "transcribing" }
  | { kind: "grading" }
  | { kind: "thinking" }               // Ask Yuki
  | { kind: "idle_can_continue" }
  | { kind: "self_check";     canDoId: string }
  | { kind: "lesson_complete"; nextLessonId: string | null }
  | { kind: "blocked";        reason: BlockedReason; recoverable: boolean };
```

`BlockedReason` covers `mic_unavailable`, `mic_denied`, `tts_unavailable`,
`stt_unavailable`, `llm_unavailable`, `audio_missing`, `backend_unreachable`.
Every phase maps to exactly one avatar mood, one status string, one transport
button and one focus-card variant, defined in a single table. Contradictory
combinations become unrepresentable.

Note the direction of the dependency: `TutorPhase` is derived **from** the
server payload plus local I/O state. It never decides what the next lesson step
is. Sequencing still comes from `POST /tutor/{id}/advance` and
`POST /tutor/{id}/message`.

### 3.2 Transitions

```
loading ──▶ speaking ──▶ playing_audio ──┬──▶ awaiting_speech ──▶ recording
                                          │            ▲              │
                                          │            └── retry ─────┤
                                          └──▶ idle_can_continue      ▼
                                                                transcribing
                                                                      │
                                                                      ▼
                                                                   grading
                                                                      │
                                             pass ◀──────────────────┴──▶ fail
                                              │                            │
                                              ▼                            ▼
                                        (server advances)          awaiting_speech
```

`thinking` is orthogonal: Ask Yuki can be entered from any phase and returns to
the phase it interrupted, mirroring the backend guarantee that
`answer_question` restores `state`/`activity_id`/`quiz_index`.

### 3.3 Smooth transitions

- Every phase change animates through a shared 180 ms cross-fade on the focus
  card and a 120 ms slide on the step header. Both respect
  `prefers-reduced-motion`.
- **Reserve space.** The feedback band, the focus card and the status region all
  have min-heights so a grade result appearing never reflows the stage.
- **No layout thrash between steps.** The step header, instruction, avatar and
  transport are permanent; only their text changes.
- **Auto-advance gets a visible, interruptible countdown.** Instead of the
  current silent jump, show a 1.2 s progress ring on the *Next* button with the
  text "Continuing…" and let a click or `Escape` cancel it. This preserves the
  deterministic flow while making it feel intentional.

### 3.4 Clear Listening / Recording / Thinking states

| Phase | Avatar | Status text | Transport | Extra |
|-------|--------|-------------|-----------|-------|
| `speaking` | mouth animated, ring pulses warm | "Yuki is speaking" | *Skip line* | Bubble text highlights per chunk |
| `playing_audio` | idle, headphone glyph on ring | "Book audio 1 of 2" | *Skip audio* | Determinate bar from `audio.duration` |
| `awaiting_speech` | attentive, ring is a dashed outline | "Your turn" | *Hold to speak* | Focus card shows the target |
| `recording` | attentive, ring reacts to input level | "Listening… 0:03" | *Stop* | Live waveform + timer |
| `transcribing` | thinking, ring indeterminate | "Hearing you…" | *Cancel* | Skeleton in the feedback band |
| `grading` | thinking | "Checking…" | *Cancel* | Same skeleton |
| `thinking` | thinking, only in the context panel | "Yuki is thinking…" | unchanged | **Stage stays interactive** |

The critical rule: **`thinking` must not disable the stage.** Ask Yuki gets its
own inline spinner in the context panel while replay, mic and next remain live.

### 3.5 Progress at three scales

1. **Whole lesson** — the existing `lesson_progress_snapshot.percent`, in the
   left rail ring, not a full-width bar at the top of the stage.
2. **Current activity** — a segmented bar in the step header, one segment per
   entry in `flow_substeps(activity)`, with the current one filled. This needs
   the backend to send `substeps` and `substep_index` (see
   [04 §1.3](04-architecture-improvements.md)); today the client cannot draw it
   because it never learns how many sub-steps the activity has.
3. **Current operation** — determinate where possible (audio playback position,
   recording elapsed), indeterminate otherwise (transcription, LLM).

### 3.6 Session structure for 75-step lessons

Introduce a purely presentational **segment** concept — it changes nothing in the
orchestrator:

- Group consecutive activities that share a `can_do_id` into a segment. The YAML
  already carries `can_do_id` on 100% of activities.
- Show "Part 2 of 4 · Greetings when you meet someone" in the step header.
- At each segment boundary, offer a *Pause here* affordance: "Nice work — 3 of 4
  parts done. Continue, or stop here and pick up later." Continuing is the
  default and requires no click if the user just keeps going.
- The left rail shows the segment breakdown so the size of the commitment is
  visible before starting.

Because the session is already persisted in `chat_sessions` and
`start_or_resume` resumes it, "stop here" needs no new backend behaviour — only
honest labelling. Rename *Restart lesson* to *Start over* and move it to the
overflow menu with a confirm, so it stops reading like the resume button.

---

## 4. Avatar system

### 4.1 Problems being solved

1.07 MB of near-identical PNGs; a hard `src` swap every 180 ms; animation not
tied to actual audio; only three states; no way to add expressions without
adding another ~350 KB file.

### 4.2 Target: layered SVG with a small sprite for the mouth

```
components/stage/Avatar/
  Avatar.tsx          — mood → layer state, respects prefers-reduced-motion
  layers/base.svg     — body, hair, clothes  (static)
  layers/eyes.svg     — open / half / closed (3 paths, CSS-switched)
  layers/brows.svg    — neutral / raised / concerned
  layers/mouth.svg    — 5 visemes: closed, A, I, U, smile
  Avatar.css          — keyframes, ring states
```

Why this shape:

- One HTTP request, a few KB, no decode cost per frame.
- Switching a mouth viseme is a CSS class change on a `<g>`, not an image load.
- Expressions become combinations (`eyes:half` + `brows:concerned` + `mouth:closed`
  = "listening carefully") instead of new binary assets.
- The existing illustration stays the design reference — this is a re-authoring
  of the same character, not a new one.

If re-authoring as SVG is not desirable, the fallback is a **single sprite
sheet**: one WebP atlas with the head region cut into mouth/eye tiles, positioned
with `background-position`. Same benefits, keeps the painted look, roughly
120 KB instead of 1.07 MB.

### 4.3 States

| Mood | Eyes | Brows | Mouth | Ring | Motion |
|------|------|-------|-------|------|--------|
| `idle` | open, blink every 4–7 s | neutral | closed, faint smile | still, soft | 5.5 s breathe |
| `speaking` | open, blink | neutral | viseme cycle | warm pulse in time with audio | 3.2 s breathe |
| `listening` | open wide | slightly raised | closed | dashed, reacts to input level | 4.5 s breathe |
| `thinking` | half, looking up-left | one raised | closed | indeterminate sweep | slow |
| `celebrating` | closed happy arcs | raised | open smile | green flash | one-shot bounce |
| `encouraging` | open | concerned | small smile | amber | one-shot nod |

`celebrating` fires on a can-do pass, `encouraging` on a retry — the app
currently has no visual reward at all for passing a step.

### 4.4 Lip sync driven by real audio

Replace the fixed 180 ms `setInterval` with an amplitude envelope from the audio
that is actually playing:

```ts
// useAudioPipeline exposes a shared AudioContext + AnalyserNode
const level = analyser.getByteTimeDomainData(...);   // rAF loop
const viseme = level < 0.06 ? "closed"
             : level < 0.18 ? "A_small"
             : "A_open";
```

Result: the mouth stops when the audio stops, pauses at commas, and never flaps
during a failed synthesis. Under `prefers-reduced-motion` the mouth holds a
single open frame and only the ring animates.

### 4.5 Performance budget

| Metric | Today | Target |
|--------|-------|--------|
| Avatar bytes | 1 075 KB | < 150 KB |
| DOM work per frame | full `<img>` src swap | one class toggle |
| Animation driver | `setInterval(180ms)` | `requestAnimationFrame`, paused when hidden |
| Frames dropped while speaking | measurable | none |

---

## 5. Audio feedback and the recording experience

### 5.1 One audio pipeline

Today: `speech.ts` creates a fresh `new Audio()` per TTS chunk, `Tutor.tsx`
creates another per book track, `VoiceSettings` calls `speakTutor` directly, and
nothing can be paused, cancelled, prefetched or metered.

Introduce `useAudioPipeline()` — a single module owning one `AudioContext`, one
gain node, one analyser and a queue:

```ts
type AudioJob =
  | { kind: "tts";  text: string }
  | { kind: "book"; path: string };

interface AudioPipeline {
  enqueue(jobs: AudioJob[]): Promise<void>;
  cancel(): void;                       // abort fetch + stop playback
  pause(): void; resume(): void;
  replayLast(): Promise<void>;
  readonly position: { index: number; total: number; seconds: number; duration: number };
  readonly level: number;               // 0..1 output level, drives the avatar
  setOutputDevice(deviceId: string): Promise<void>;  // HTMLMediaElement.setSinkId
  setRate(rate: number): void;          // 0.75 / 1.0 / 1.25 for book audio
}
```

Immediate wins: replay works, skip works, pause works, the avatar can lip-sync,
output device selection becomes possible, and the tutor voice can be ducked
while book audio plays.

### 5.2 Prefetch

The next step's audio is knowable as soon as a payload arrives: `step.play_audio`
lists the book tracks and the tutor line is in `messages`. Prefetch both while
the current step is still playing. This removes the silent gap between "Yuki
finishes speaking" and "CD starts" that currently reads as a hang.

TTS also gets a **server-side cache** (see
[04 §2.3](04-architecture-improvements.md)) — tutor lines such as
`よくできました。` are synthesised on nearly every graded step today.

### 5.3 Waveform during recording

```
┌──────────────────────────────────────────────────────────┐
│  ●  Listening   0:03        ▁▂▅▇█▇▅▃▂▁▂▄▆▇▅▃▁            │
│                             └ live, 60 fps, 48 bars      │
│  [ ████████░░░░░░░░ ] auto-stop after 1.2 s of silence   │
└──────────────────────────────────────────────────────────┘
```

Implementation:

```ts
const ctx = new AudioContext();
const src = ctx.createMediaStreamSource(stream);
const analyser = ctx.createAnalyser();
analyser.fftSize = 512;
analyser.smoothingTimeConstant = 0.6;
src.connect(analyser);
// rAF: getByteTimeDomainData -> RMS -> push into a 48-slot ring buffer -> <canvas>
```

Draw to a `<canvas>`, never to 48 React nodes. The same RMS value feeds the
avatar's listening ring and the silence detector.

### 5.4 Voice activity detection

Replace `blob.size < 800` with real signal analysis:

- **Speech onset**: RMS above a calibrated noise floor for 150 ms.
- **Auto-stop**: RMS below the floor for 1200 ms after onset (configurable, and
  disableable for learners who need longer).
- **Hard cap**: 15 s.
- **No speech at all**: if onset never occurs, do not send anything to Whisper.
  Show "I didn't hear anything — check your microphone" with a *Try again*
  button and a link to the device picker. This is a much better failure than
  today's silent 400-byte upload.

The noise floor is measured during a 400 ms calibration when the mic opens, and
re-used for the session.

### 5.5 Recording controls

- **Press-and-hold** (`Space` or mouse-down) as the default, with a toggle mode
  in Settings for users who prefer click-to-start/click-to-stop.
- A **pre-flight mic check** on first run and in Settings: pick a device, watch
  the meter, record two seconds and hear it back. Nothing about the current app
  tells a user their mic is broken until they are mid-lesson.
- **Re-record before submit**: after auto-stop, show the waveform with *Send* /
  *Re-record* for a 1.5 s grace window (skippable by setting).
- **`getUserMedia` constraints** should be explicit rather than `{ audio: true }`:
  `{ deviceId, echoCancellation: true, noiseSuppression: true, autoGainControl: true, channelCount: 1, sampleRate: 16000 }` — Whisper works at 16 kHz mono, so this
  also shrinks uploads.

### 5.6 Richer grade feedback

The grader already returns `hits`, `gaps`, `best_match`, `similarity` and
`score`; the UI shows only a rounded percentage. Show:

- the transcript as Whisper heard it, so mis-hearings are visible;
- a character-level diff against `best_match`, tinting matched runs green and
  missing runs amber (`phrase_grade.normalize_jp_for_grade` already produces the
  normalized forms both sides compare);
- attempt count for this sub-step and the best score so far;
- *Hear it again* (tutor TTS of the target) and *Hear me* (playback of the just
  recorded blob) side by side. This is the single most useful pronunciation tool
  in the app and it costs one `URL.createObjectURL`.

### 5.7 Audio settings

Input device, output device, tutor volume, book-audio volume, book-audio speed
(0.75×/1×/1.25×), and "duck tutor voice under book audio". All in the settings
panel (§6), all persisted.

---

## 6. Unified settings panel

A modal dialog reachable from the title bar `⚙︎` and `Ctrl/Cmd+,`, replacing the
`/settings` route. Five sections.

### 6.1 Voice

- **Tutor voice** — the existing VOICEVOX speaker/style picker, grouped by
  character with the style as a sub-choice instead of one flat 100-entry list,
  plus a *Preview* button (already implemented) and a searchable filter.
- **Speaking rate / pitch** — VOICEVOX `audio_query` already returns
  `speedScale`, `pitchScale` and `intonationScale`; expose speed and pitch and
  pass them through `POST /voice/speak`. This is a small backend change and a big
  comfort win for beginners.
- **Fallback behaviour** — "If VOICEVOX is not running: use the system voice /
  show text only".

### 6.2 Audio devices

- Input device (`navigator.mediaDevices.enumerateDevices()`), with a live meter.
- Output device (`HTMLMediaElement.setSinkId`).
- Tutor volume, book volume, book playback speed.
- *Test microphone* — record 2 s, show the waveform, play it back.

### 6.3 Appearance

- **Theme**: System / Light / Dark. Implemented by moving the palette from
  `:root` into `[data-theme="dark"]` / `[data-theme="light"]` blocks and adding a
  `prefers-color-scheme` listener. Every current colour is already a token in
  `:root`, so this is mostly a matter of authoring the light values and fixing
  the ~50 inline styles that bypass the tokens.
- Text size (Normal / Large) — furigana-heavy Japanese benefits from this.
- Japanese font (Mincho / Gothic) and **bundle the fonts locally** instead of
  fetching them from `fonts.googleapis.com`.
- Reduce motion (also honours the OS setting).

### 6.4 Lessons

- **Auto-advance**: Off / After tutor audio / After tutor audio and my answer.
  Default "After tutor audio", matching today's behaviour exactly. When on, the
  interruptible 1.2 s countdown from §3.3 is shown.
- **Auto-advance delay** slider, 0–3 s.
- **Auto-start recording** when a step expects speech (currently always on and
  a common source of surprise), plus **press-and-hold vs toggle**.
- **Retry limit before Yuki offers a hint**.
- **Grading strictness**: Lenient / Standard / Strict, mapping to
  `phrase_grade.DEFAULT_PASS_THRESHOLD` (e.g. 48 / 58 / 70) via a new
  `grading_strictness` setting. The can-do mastery rule
  (`mastery_min_score = 80`, one spoken pass) is deliberately **not** exposed —
  unlock semantics must stay fixed.
- **Show romaji** / **Show furigana** toggles.

### 6.5 Ask Yuki

- **Answer language**: English / Japanese / Both (today it is always both).
- **Speak the answer aloud**: on/off. Today the Japanese part of every help reply
  is pushed through the same TTS pipeline as lesson lines, with no way to turn it
  off, which is jarring when the learner only wanted a quick text answer.
- **Answer length**: Brief / Normal / Detailed → a max-tokens hint in the prompt.
- **Model**: a picker fed from `health.ollama.models` instead of requiring
  `OLLAMA_MODEL` in the environment.
- **Offline behaviour**: "If Ollama is not running, show the phrase hint" — the
  fallback `_ollama_lesson_help` already implements, now stated to the user.

### 6.6 Advanced (collapsed by default)

Whisper model size and device, backend port, data folder, *Open log folder*,
*Copy diagnostics*, and a **Developer tools** switch that reveals *Jump to
Can-do quiz* and *Can-do (reset progress)* in the transport overflow.

### 6.7 Where settings live

`GET /settings` and `PATCH /settings` backed by the existing `settings` table
(`SettingRow`), so preferences survive reinstalls and are shared between the
Electron window and any browser tab. `voicevox_client` already demonstrates the
pattern with `selected_speaker_id`. Client-only presentation values (theme, text
size) may stay in `localStorage`, but device selections and lesson behaviour
belong on the server so the backend can honour them too.

---

## 7. Visual polish

### 7.1 Design tokens

Promote the ad-hoc `:root` block into a real token set and delete the 50 inline
style objects:

```css
:root {
  /* spacing: 4px base */
  --sp-1: .25rem; --sp-2: .5rem; --sp-3: .75rem; --sp-4: 1rem;
  --sp-6: 1.5rem; --sp-8: 2rem;
  /* radii */  --r-sm: 8px; --r-md: 12px; --r-lg: 16px; --r-full: 999px;
  /* type */   --fs-xs: .78rem … --fs-3xl: 2.35rem;
  /* elevation */ --e-1 … --e-3;
  /* semantic colour — resolved per theme */
  --surface, --surface-raised, --surface-sunken,
  --text, --text-muted, --border,
  --accent, --accent-ink, --success, --warning, --danger, --info;
  /* motion */ --dur-fast: 120ms; --dur-base: 180ms; --ease: cubic-bezier(.2,.8,.2,1);
}
```

Adopt CSS Modules per component (Vite supports them with zero config) so styles
are colocated and `styles.css` becomes tokens + resets only.

### 7.2 Japanese typography

- Line height 1.7 for Japanese body text, 1.35 for the large phrase card.
- Never letter-space Japanese below 1.25 rem.
- Ship the fonts in `apps/desktop/public/fonts/` with `font-display: swap` and
  drop the Google Fonts `<link>` — an offline app must not depend on a CDN.
- Optional furigana rendering with `<ruby>` where `phrase_meta` provides readings.

### 7.3 Motion

180 ms cross-fades, 120 ms slides, one shared easing curve, and a global
`prefers-reduced-motion` guard that disables the breathe, pulse and countdown
animations while keeping state changes instant and legible.

### 7.4 First-run and empty states

- **Setup wizard** replacing the `/setup` checklist: four steps — Ollama,
  VOICEVOX, Irodori materials, microphone — each with a live status dot, a plain
  explanation of what it is for, a *Check again* button, and a *Skip for now*
  that explains exactly what degrades. Reachable later from the service
  indicator.
- **Empty SRS**: "No cards yet — finish a lesson and words you struggled with
  appear here", with no button. The *Seed L01 cards* developer action moves
  behind the Developer tools switch.
- **Missing book audio**: the app currently surfaces this as a red "Book audio
  failed" banner. It should be a per-track inline notice: "This track isn't in
  your `assets/audio` folder", with *Open folder* and *Continue without audio*.

### 7.5 Error presentation

Three severities with distinct treatments:

| Severity | Example | Treatment |
|----------|---------|-----------|
| Info | "Using system voice — VOICEVOX isn't running" | Quiet inline chip in the transport bar |
| Warning | "Book audio for this track is missing" | Dismissible inline notice on the focus card, with an action |
| Error | "Can't reach the backend" | Blocking dialog with *Retry* and *Open logs* |

Every message is written for a learner, carries a *what to do next*, and clears
itself when the next operation succeeds — the specific behaviour missing today.

---

## 8. Responsiveness and reduced UI blocking

| Cause of blocking today | Fix |
|-------------------------|-----|
| `busy` disables the whole stage during Ask Yuki | Scope busy state per region; the stage never waits on the LLM |
| `runPipeline` `await`s TTS chunk-by-chunk before showing the step | Render the step immediately; audio plays alongside |
| Whisper first-run blocks every API route | Warm the model at startup in a worker thread ([04 §2.2](04-architecture-improvements.md)) |
| No request cancellation | Every fetch gets an `AbortController`; *Cancel* is a real button |
| Full re-render of a 586-line component on each keystroke in Ask Yuki | Split components; memoize the stage |
| 1 MB of avatar PNGs decoded on mount | SVG/sprite avatar (§4) |
| No optimistic UI | Show the learner's transcript in the transcript pane the instant it returns, before grading completes |

Two concrete guarantees to hold the redesign to:

- **Input latency**: pressing the mic key starts the analyser within one frame.
- **No `await` on the render path**: a payload arriving renders in the same tick;
  all audio is a side effect.

---

## 9. What this plan deliberately does not change

- The set of tutor modes and their sub-step sequences in `FLOW_BY_MODE`.
- Server ownership of `state`, `activity_id`, `quiz_index`.
- Can-do mastery and unlock rules (`mastery_min_score`,
  `mastery_passes_required`, `mastery_spoken_required`, `is_lesson_unlocked`).
- The Ask-Yuki-never-advances guarantee.
- The YAML contract — every new field described here is additive and defaulted.
- VOICEVOX, Whisper and Ollama as the voice/STT/LLM providers.
