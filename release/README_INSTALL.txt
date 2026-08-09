Jtutor — install guide (Windows)
================================

What this is
------------
A local Japanese tutor for Irodori Starter (A1) and Elementary 1 (A2).
It runs on your PC. Nothing is uploaded to the cloud for lessons.

What you need
-------------
1. Windows 10/11
2. Python 3.11 or newer  — https://www.python.org/downloads/
   (check "Add python.exe to PATH")
3. Ollama — https://ollama.com
   After install, open a terminal and run:
     ollama pull qwen2.5:7b
4. VOICEVOX — https://voicevox.hiroshiba.jp/
   Leave the engine running while you study
5. Your own Irodori PDFs + MP3s (not included — copyright)

Install
-------
1. Unzip this folder anywhere (example: Desktop\Jtutor)
2. Double-click INSTALL.bat  (first time only; can take several minutes)
3. Copy Irodori files into assets\  (see assets\README.txt)
4. Start Ollama and VOICEVOX
5. Double-click START.bat
6. Browser opens to http://127.0.0.1:8765

Use
---
- Pick Starter or Elementary 1 in the left sidebar
- Use the mic for speaking practice
- Progress is saved in the data\ folder on this PC

Stop
----
Double-click STOP.bat

Privacy
-------
API listens only on 127.0.0.1 (this computer). Lesson audio stays local.

Support tip
-----------
If something fails, open data\jtutor.log and share the last ~50 lines.
