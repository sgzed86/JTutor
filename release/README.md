# Jtutor — Setup Guide

Jtutor is a **local Japanese tutor** for the Irodori textbooks:

- **Starter (A1)**
- **Elementary 1 (A2)**

It runs on your computer. Lessons, audio, and progress stay on your PC.

---

## Before you start

You need these installed (free):

| What | Why | Download |
|------|-----|----------|
| **Python 3.11 or newer** | Runs the tutor | https://www.python.org/downloads/ |
| **Ollama** | Powers Ask Yuki / chat help | https://ollama.com |
| **VOICEVOX** | Tutor speech voice | https://voicevox.hiroshiba.jp/ |
| **Irodori book files** | Official PDFs + MP3s | https://www.irodori.jpf.go.jp/ |

**Python tip:** During install, check the box **“Add python.exe to PATH”**.

This zip does **not** include the Irodori PDFs or audio (copyright). You must add your own copies.

---

## Step 1 — Unzip

1. Unzip `Jtutor-portable-win.zip` somewhere easy to find, for example:

   `Desktop\Jtutor`

2. Open that folder. You should see:

   - `INSTALL.bat`
   - `START.bat`
   - `STOP.bat`
   - `assets\`
   - `README.md` (this file)

---

## Step 2 — Install Jtutor (once)

1. Double-click **`INSTALL.bat`**
2. Wait until it finishes  
   - First time can take **several minutes** (it downloads speech recognition packages)
3. When you see **“Setup complete”**, press any key to close the window

If it says Python was not found:

1. Install Python 3.11+ from the link above  
2. Restart your PC (or open a new terminal)  
3. Run `INSTALL.bat` again  

---

## Step 3 — Add your Irodori materials

Open the **`assets`** folder inside Jtutor and add your files like this:

```
assets\
  irodori_starter.pdf
  Grammar_Worksheets_X.pdf
  Elementary1.pdf                 (optional — for book 2)
  Grammar_Elementary_1.pdf        (optional — for book 2)
  audio\
    X_[01-01]_kiku.mp3            (Starter audio files)
    X_[01-02]_kiku1.mp3
    ...
    Y_[01-01]_kaiwa1.mp3          (Elementary 1 audio files)
    ...
```

### Starter (required for book 1)

- Textbook PDF → `assets\irodori_starter.pdf`
- Grammar PDF → `assets\Grammar_Worksheets_X.pdf`
- All Starter MP3s → `assets\audio\` (names start with `X_`)

### Elementary 1 (required for book 2)

- Textbook PDF → `assets\Elementary1.pdf`
- Grammar PDF → `assets\Grammar_Elementary_1.pdf`
- All Elementary 1 MP3s → `assets\audio\` (names start with `Y_`)

You can also read `assets\README.txt` for a short checklist.

---

## Step 4 — Start Ollama and VOICEVOX

Do this every time you study (or set them to start with Windows).

### Ollama

1. Open the **Ollama** app  
2. Open PowerShell or Command Prompt and run:

```text
ollama pull qwen2.5:7b
```

(Only needed once. After that, just leave Ollama running.)

### VOICEVOX

1. Open **VOICEVOX**  
2. Leave it running in the background  

The tutor talks through VOICEVOX at `http://127.0.0.1:50021`.

---

## Step 5 — Start Jtutor

1. Double-click **`START.bat`**
2. Your browser should open to:

   **http://127.0.0.1:8765**

3. If it does not open, go to that address yourself  

Keep the Jtutor window available while you study (it may be minimized).

---

## Using the app

1. On the left, pick your book: **Starter** or **Elementary 1**
2. Open a lesson (EL01 / L01, etc.)
3. Follow Yuki through listen / speak / role-play
4. Use the mic when it asks you to speak
5. Your progress is saved automatically in the `data` folder

---

## Stop Jtutor

Double-click **`STOP.bat`**

Or close the Jtutor process/window that was started by `START.bat`.

---

## Troubleshooting

### “Python not found”
Install Python 3.11+, enable **Add to PATH**, then run `INSTALL.bat` again.

### Browser opens but page fails / APIs error
1. Run `STOP.bat`
2. Run `START.bat` again
3. Confirm you are opening **http://127.0.0.1:8765** (not a random other port)

### No tutor voice
- Make sure **VOICEVOX** is running
- In the app, check **Settings → Tutor Voice**

### Mic / speaking not recognized
- Allow microphone access in your browser
- First spoken answer may be slower while Whisper loads

### No lesson audio
- Confirm MP3s are in `assets\audio\`
- Filenames must look like `X_[01-01]_....mp3` or `Y_[01-01]_....mp3`

### Ask Yuki does not answer
- Make sure **Ollama** is running
- Confirm you pulled the model: `ollama pull qwen2.5:7b`

### Still stuck
Open `data\jtutor.log` and share the last 50 lines with whoever sent you this app.

---

## Privacy

- Jtutor listens only on your computer (`127.0.0.1`)
- Lesson files and progress stay local
- You need internet only to install Python packages / Ollama models the first time

---

## Quick checklist

- [ ] Python 3.11+ installed  
- [ ] `INSTALL.bat` finished successfully  
- [ ] Irodori PDFs + MP3s copied into `assets\`  
- [ ] Ollama running + `qwen2.5:7b` pulled  
- [ ] VOICEVOX running  
- [ ] `START.bat` → http://127.0.0.1:8765  
