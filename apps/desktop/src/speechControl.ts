/** Shared TTS playback control (barge-in). */
let activeAudio: HTMLAudioElement | null = null;
let speakGeneration = 0;

export function stopSpeaking(): void {
  speakGeneration += 1;
  if (activeAudio) {
    activeAudio.pause();
    activeAudio = null;
  }
  if ("speechSynthesis" in window) {
    window.speechSynthesis.cancel();
  }
}

export function speakGenerationId(): number {
  return speakGeneration;
}

export function setActiveAudio(audio: HTMLAudioElement | null): void {
  activeAudio = audio;
}

export function isSpeakingActive(): boolean {
  return activeAudio !== null;
}
