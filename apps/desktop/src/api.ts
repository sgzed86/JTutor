const API =
  (typeof window !== "undefined" && (window as any).jtutor?.apiBase) ||
  "http://127.0.0.1:8765";

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch(`${API}${path}`, init);
  if (!r.ok) {
    const text = await r.text();
    throw new Error(text || r.statusText);
  }
  const ct = r.headers.get("content-type") || "";
  if (ct.includes("application/json")) return r.json();
  return r as unknown as T;
}

export type VoiceSpeakerOption = {
  speaker_id: number;
  name: string;
  style_name: string;
  style_type?: string;
  label: string;
};

export const api = {
  base: API,
  health: () => req<any>("/health"),
  logTail: (lines = 200) => req<{ path: string; lines: string[] }>(`/log/tail?lines=${lines}`),
  voiceSpeakers: () =>
    req<{
      selected_speaker_id: number;
      speakers: any[];
      options: VoiceSpeakerOption[];
    }>("/voice/speakers"),
  setVoiceSpeaker: (speakerId: number) =>
    req<{ ok: boolean; selected_speaker_id: number }>("/voice/set-speaker", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ speaker_id: speakerId }),
    }),
  voiceSettings: () =>
    req<{
      selected_speaker_id: number;
      voicevox_speaker: number;
      whisper_model: string;
      whisper_device: string;
      voice_speed_scale?: number;
    }>("/voice/settings"),
  setVoiceSpeed: (speedScale: number) =>
    req<{ ok: boolean; voice_speed_scale: number }>("/voice/set-speed", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ speed_scale: speedScale }),
    }),
  books: () => req<{ books: any[]; active: string }>("/books"),
  setBook: (bookId: string) =>
    req<{ ok: boolean; active: string; lesson_count: number }>("/books/active", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ book_id: bookId }),
    }),
  curriculum: () => req<{ lessons: any[]; book_id?: string; book_title?: string }>("/curriculum"),
  lesson: (id: string) => req<any>(`/curriculum/${id}`),
  seedSrs: (id: string) =>
    req<any>(`/curriculum/${id}/seed-srs`, { method: "POST" }),
  progress: () =>
    req<{ lessons: any[]; book_id?: string; book_title?: string }>("/progress"),
  startTutor: (id: string) =>
    req<any>(`/tutor/${id}/start`, { method: "POST" }),
  tutorHistory: (id: string, offset = 0, limit = 200) =>
    req<{ messages: any[]; message_total: number; offset: number }>(
      `/tutor/${id}/history?offset=${offset}&limit=${limit}`
    ),
  resetTutor: (id: string) =>
    req<any>(`/tutor/${id}/reset`, { method: "POST" }),
  advance: (id: string) =>
    req<any>(`/tutor/${id}/advance`, { method: "POST" }),
  jumpToCanDoQuiz: (id: string, resetCanDo = false) =>
    req<any>(`/tutor/${id}/jump-can-do?reset_can_do=${resetCanDo ? "true" : "false"}`, {
      method: "POST",
    }),
  message: (id: string, text: string, spoken = false) =>
    req<any>(`/tutor/${id}/message`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, spoken }),
    }),
  askTutor: (id: string, text: string, spoken = false) =>
    req<any>(`/tutor/${id}/ask`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, spoken }),
    }),
  selfCheck: (id: string, canDoId: string, stars: number, comment = "") =>
    req<any>(`/tutor/${id}/self-check`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ can_do_id: canDoId, stars, comment }),
    }),
  srsDue: () => req<{ count: number; cards: any[] }>("/srs/due"),
  srsStats: () => req<{ total: number; due: number }>("/srs/stats"),
  srsReview: (cardId: number, rating: number) =>
    req<any>(`/srs/${cardId}/review`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ rating }),
    }),
  audioUrl: (relPath: string) =>
    `${API}/media/audio?path=${encodeURIComponent(relPath)}`,
  pdfUrl: (which: "textbook" | "grammar" = "textbook", book?: string) => {
    const q = new URLSearchParams({ which });
    if (book) q.set("book", book);
    return `${API}/media/pdf?${q.toString()}`;
  },
  speak: async (text: string) => {
    const r = await fetch(`${API}/voice/speak`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });
    if (!r.ok) throw new Error(await r.text());
    return r.blob();
  },
  transcribe: async (blob: Blob) => {
    const fd = new FormData();
    fd.append("file", blob, "speech.webm");
    const r = await fetch(`${API}/voice/transcribe`, { method: "POST", body: fd });
    if (!r.ok) throw new Error(await r.text());
    return r.json() as Promise<{ text: string }>;
  },
};
