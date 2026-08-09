# Curriculum YAML — optional fields (backward compatible)

Existing lesson files under `content/starter/` keep working without regeneration. New fields are **optional**; the tutor defaults to `listen_repeat` when `book_mode` is absent.

## Lesson-level fields

| Field | Type | Purpose |
|-------|------|---------|
| `intro_questions` | list | Warm-up Qs: `{jp, en}` or strings. Empty/missing → skip `intro_chat` |

## Activity fields

| Field | Type | Purpose |
|-------|------|---------|
| `book_mode` | `listen_repeat` \| `listen_repeat_all` \| `listen_select` \| `dialog` \| `shadow_dialog` | Sub-step flow (see `backend/app/book_modes.py`) |
| `book_skip` | bool | Omit from tutor track list |
| `picture_hint_en` | string | English hint for choose-and-say steps |
| `picture_has_image` | bool | UI: show “use book illustration” (generated for L02+) |
| `dialog_script` | list | `{speaker: partner\|learner, jp: "..."}` |
| `dialog_listen_audio` | list | MP3 paths for dialog listen / shadow |
| `book_section_jp` / `book_section_en` | string | Section intro before activity |
| `phrase_meta` | list | `{jp, tags: [short\|long, polite\|casual]}` — metadata only |

### Mode substeps

| Mode | Flow |
|------|------|
| `listen_repeat` | listen → repeat |
| `listen_repeat_all` | listen → repeat × each `key_phrases` item (e.g. numbers 0–10) |
| `listen_select` | listen → select |
| `dialog` | listen → **shadow** → partner → learner → swap_learner → swap_partner |
| `shadow_dialog` | shadow only |

## Lesson flow (session `state`)

`lesson_intro` → `intro_chat` (if questions) → `book` → `grammar` → `can_do_quiz` → `self_check` → next Can-do / `lesson_complete`

## Regenerating

```powershell
# Optional: refresh Whisper transcripts (once, or when MP3s change)
python scripts/build_audio_transcripts.py tiny

python scripts/build_curriculum.py
```

- **L01** — Hand-tuned `apply_l01_book_flow` + curated `intro_questions`.
- **L02** — Hand-tuned phrases/CD fixes + `listen_repeat_all` for numbers.
- **L03–L18** — `key_phrases` and dialog lines from `content/starter/audio_transcripts.json` (Whisper), then book modes + quiz enrichment.
- **quiz_scenarios** — Curated L01/L02 plus auto-enriched dialog scenarios.

## Tutor API

- `POST /tutor/{id}/message` — may include `grade`, `progress`, `self_check` (pending)
- `POST /tutor/{id}/self-check` — `{can_do_id, stars, comment}` soft rating (no unlock effect)
- Ask Yuki (`POST /tutor/{id}/ask`) never changes `state`, `activity_id`, or `quiz_index`
