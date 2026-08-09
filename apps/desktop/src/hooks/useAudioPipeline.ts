import { useCallback, useRef } from "react";
import { api } from "../api";
import { speakTutor, stopSpeaking } from "../speech";

/** Unified book + TTS playback (Tier 3.4). Recording stays in Tutor for now. */
export function useAudioPipeline() {
  const bookAudioRef = useRef<HTMLAudioElement | null>(null);

  const stopAll = useCallback(() => {
    stopSpeaking();
    if (bookAudioRef.current) {
      bookAudioRef.current.pause();
      bookAudioRef.current = null;
    }
  }, []);

  const playBookTracks = useCallback(async (paths: string[]) => {
    for (const rel of paths) {
      const audio = new Audio(api.audioUrl(rel));
      bookAudioRef.current = audio;
      await new Promise<void>((resolve, reject) => {
        audio.onended = () => resolve();
        audio.onerror = () => reject(new Error("Book audio failed"));
        audio.play().catch(reject);
      });
      if (bookAudioRef.current === audio) bookAudioRef.current = null;
    }
  }, []);

  const speak = useCallback(async (text: string) => {
    await speakTutor(text, api.speak);
  }, []);

  return { playBookTracks, speak, stopAll };
}
