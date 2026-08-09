/** Prefer Japanese for VoiceVox; fall back to cleaned full text. */
export function speakableText(raw: string): string {
  let t = (raw || "").trim();
  t = t.replace(/```[\s\S]*?```/g, " ");
  t = t.replace(/[*_`#]+/g, " ");
  // Drop long ASCII parenthetical glosses
  t = t.replace(/\([A-Za-z][^)]{0,80}\)/g, " ");
  const jp = (t.match(/[\u3040-\u30ff\u4e00-\u9fff\u3000-\u303f\uff00-\uffef、。！？…ー\s]+/g) || [])
    .join("")
    .replace(/\s+/g, " ")
    .trim();
  if (jp.length >= 4) return jp;
  return t.replace(/\s+/g, " ").trim();
}

export function splitUtterances(text: string, maxLen = 80): string[] {
  const parts = text
    .split(/(?<=[。！？!?…])\s*/)
    .map((p) => p.trim())
    .filter(Boolean);
  const out: string[] = [];
  for (const p of parts.length ? parts : [text]) {
    if (p.length <= maxLen) {
      out.push(p);
      continue;
    }
    for (let i = 0; i < p.length; i += maxLen) {
      out.push(p.slice(i, i + maxLen));
    }
  }
  return out.filter(Boolean);
}

function playBlob(blob: Blob): Promise<void> {
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(blob);
    const audio = new Audio(url);
    audio.onended = () => {
      URL.revokeObjectURL(url);
      resolve();
    };
    audio.onerror = () => {
      URL.revokeObjectURL(url);
      reject(new Error("Audio playback failed"));
    };
    audio.play().catch(reject);
  });
}

function browserSpeak(text: string): Promise<void> {
  return new Promise((resolve) => {
    if (!("speechSynthesis" in window)) {
      resolve();
      return;
    }
    window.speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text);
    u.lang = /[\u3040-\u30ff\u4e00-\u9fff]/.test(text) ? "ja-JP" : "en-US";
    u.onend = () => resolve();
    u.onerror = () => resolve();
    window.speechSynthesis.speak(u);
  });
}

/** Speak via VoiceVox (Japanese), with browser TTS fallback. */
export async function speakTutor(
  text: string,
  speakApi: (t: string) => Promise<Blob>
): Promise<void> {
  const cleaned = speakableText(text);
  if (!cleaned) return;
  const chunks = splitUtterances(cleaned);
  try {
    for (const chunk of chunks) {
      const blob = await speakApi(chunk);
      await playBlob(blob);
    }
  } catch {
    await browserSpeak(cleaned);
  }
}
