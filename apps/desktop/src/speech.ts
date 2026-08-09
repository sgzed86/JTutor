/** Prefer Japanese for VoiceVox; fall back to cleaned full text. */
import { setActiveAudio, speakGenerationId, stopSpeaking } from "./speechControl";

export { stopSpeaking, isSpeakingActive } from "./speechControl";

export function speakableText(raw: string): string {
  let t = (raw || "").trim();
  t = t.replace(/```[\s\S]*?```/g, " ");
  t = t.replace(/[*_`#]+/g, " ");
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

function playBlob(blob: Blob, gen: number): Promise<void> {
  if (gen !== speakGenerationId()) return Promise.resolve();
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(blob);
    const audio = new Audio(url);
    setActiveAudio(audio);
    audio.onended = () => {
      URL.revokeObjectURL(url);
      setActiveAudio(null);
      resolve();
    };
    audio.onerror = () => {
      URL.revokeObjectURL(url);
      setActiveAudio(null);
      reject(new Error("Audio playback failed"));
    });
    audio.play().catch(reject);
  });
}

function browserSpeak(text: string, gen: number, timeoutMs = 8000): Promise<void> {
  if (gen !== speakGenerationId()) return Promise.resolve();
  return new Promise((resolve) => {
    if (!("speechSynthesis" in window)) {
      resolve();
      return;
    }
    const done = () => resolve();
    const timer = window.setTimeout(done, timeoutMs);
    window.speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text);
    u.lang = /[\u3040-\u30ff\u4e00-\u9fff]/.test(text) ? "ja-JP" : "en-US";
    u.onend = () => {
      window.clearTimeout(timer);
      done();
    };
    u.onerror = () => {
      window.clearTimeout(timer);
      done();
    };
    window.speechSynthesis.speak(u);
  });
}

export async function speakTutor(
  text: string,
  speakApi: (t: string) => Promise<Blob>
): Promise<void> {
  const gen = speakGenerationId();
  const cleaned = speakableText(text);
  if (!cleaned) return;
  const chunks = splitUtterances(cleaned);
  try {
    for (const chunk of chunks) {
      if (gen !== speakGenerationId()) return;
      const blob = await speakApi(chunk);
      if (gen !== speakGenerationId()) return;
      await playBlob(blob, gen);
    }
  } catch {
    if (gen !== speakGenerationId()) return;
    await browserSpeak(cleaned, gen);
  }
}
