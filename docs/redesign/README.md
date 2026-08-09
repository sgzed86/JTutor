# Jtutor — UI/UX redesign & modernization plan

This folder holds the audit and plans for turning Jtutor from a working
developer-run prototype into a polished consumer desktop app.

| Document | Contents |
|----------|----------|
| [01 — UI/UX audit](01-ux-audit.md) | What the app does today, measured problems, missing features, inconsistencies, pain points |
| [02 — UI/UX redesign plan](02-ui-redesign-plan.md) | Three-pane layout, component inventory, interaction flow, avatar system, settings panel, audio feedback, visual polish |
| [03 — Startup modernization](03-startup-modernization.md) | Why `start_jtutor.bat` / `stop_jtutor.bat` exist, the three options, the recommendation, and a step-by-step implementation plan |
| [04 — Architecture improvements](04-architecture-improvements.md) | Frontend and backend refactors: tutor-mode base class, unified audio pipeline, centralized Whisper, lesson flow controller, YAML schema |
| [05 — Roadmap & actionable tasks](05-roadmap-and-tasks.md) | Prioritized waves plus a numbered backlog split by backend / frontend / Electron / packaging |

## Constraints these plans respect

Every recommendation below was written against the following hard constraints,
and each document restates how it stays inside them:

- **No tutor mode is removed.** `listen_repeat`, `listen_repeat_all`,
  `listen_select`, `dialog`, `shadow_dialog`, `intro_chat`, `grammar`,
  `can_do_quiz` and `self_check` all survive with identical semantics.
- **Deterministic lesson progression is preserved.** The server stays the single
  source of truth for `state`, `activity_id` and `quiz_index`. No proposal moves
  sequencing decisions into the client or into the LLM.
- **VOICEVOX, Whisper and Ollama stay.** They are wrapped, cached and made
  non-blocking, never replaced.
- **Existing YAML keeps working.** Every schema change is additive with a
  documented default, exactly as `book_mode` already is.

## How the findings were produced

The audit is not a code read alone. For this analysis the app was run end to end
on a Linux box:

- FastAPI on `127.0.0.1:8765` with the real `content/` YAML (37 lessons,
  791 activities).
- The Vite UI on `127.0.0.1:5173`, driven through a browser to capture every
  screen.
- A real `electron-builder` package produced from the committed `build` config
  and launched, to observe packaged-app startup behaviour.

VOICEVOX, Ollama and the Irodori PDFs/MP3s were deliberately absent, which is
the same state a new user is in before finishing setup. Several of the most
important findings come from that state.
