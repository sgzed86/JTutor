# Jtutor — getting started

Jtutor is a **local Japanese tutor** for the Irodori textbooks: **Starter (A1)**
and **Elementary 1 (A2)**. Everything — lessons, audio, grading and your
progress — stays on your own computer.

---

## Install

1. Run the Jtutor installer.
2. Launch **Jtutor** from the Start menu (Windows), Applications (macOS) or your
   app launcher (Linux).

That's it. There is nothing to start or stop by hand: Jtutor runs its own engine
while the window is open and shuts it down when you close it.

You do **not** need Python. It is bundled.

---

## Optional extras

Jtutor works without any of these — you just lose the feature each one provides.
The app's **Setup guide** (click the status dot in the title bar) shows what is
running and links to each download.

| What | What you get without it | Download |
|------|------------------------|----------|
| **VOICEVOX** | Yuki's lines are shown as text but not spoken | https://voicevox.hiroshiba.jp/ |
| **Ollama** | Ask Yuki falls back to showing the phrase you need | https://ollama.com |
| **Your Irodori PDFs + MP3s** | The book audio can't play | https://www.irodori.jpf.go.jp/ |
| **A microphone** | You can't be graded on speaking; use *Skip step* to move on | — |

For Ollama, also pull a model once: `ollama pull qwen2.5:7b`.

### Where to put the Irodori files

Open **Settings → Advanced** to see your data folder. Put the PDFs and the
`audio/` MP3 folder in the `assets` folder next to it. Jtutor never ships Japan
Foundation material — use your own legally obtained copies.

---

## Using Jtutor

- The **left rail** is your lesson map and progress.
- The **middle** is the lesson: Yuki, the phrase you need, and how you did.
- The **right panel** has Ask Yuki, grammar notes, the dialog script and the
  vocabulary for the current step.
- The **bar along the bottom** always holds the next action. Hold the big button
  (or hold `Space`) to speak. **Skip step** moves on without answering.

Pass each lesson's Can-do checks to unlock the next lesson.

---

## If something goes wrong

- **Jtutor won't start** — the error dialog has an *Open log* button; the log
  says what failed.
- **Yuki is silent** — VOICEVOX isn't running. Start it, then click *Check
  again* in the status popover.
- **"No microphone was found"** — pick a device in **Settings → Audio** and use
  *Test* to confirm it works.
- **Book audio doesn't play** — the MP3s aren't in your assets folder.
