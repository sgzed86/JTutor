import { ApiError, toApiError } from "./errors";
import type {
  BookInfo,
  DeepPartial,
  Health,
  ProgressOverview,
  SrsCard,
  Transcript,
  TutorPayload,
  UserSettings,
  VoiceSpeakerOption,
} from "./types";

type Bridge = {
  info: () => Promise<{
    apiBase: string | null;
    token: string | null;
    platform: string;
    version: string;
    isPackaged: boolean;
    logPath: string | null;
    dataDir: string | null;
  }>;
  openLogs: () => Promise<boolean>;
  openPath: (target: string) => Promise<string>;
  restartBackend: () => Promise<string | false>;
  diagnostics: () => Promise<unknown>;
  onBackendState: (handler: (payload: { state: string; detail: unknown }) => void) => () => void;
  onOpenSettings: (handler: () => void) => () => void;
};

declare global {
  interface Window {
    jtutor?: Bridge;
  }
}

/**
 * The API base and token come from the Electron supervisor, which picks a free
 * port at launch. In a plain browser (Vite dev) we fall back to the dev port and
 * the backend runs without token auth.
 */
let resolved: { base: string; token: string | null } | null = null;
let resolving: Promise<{ base: string; token: string | null }> | null = null;

function fallbackBase(): string {
  if (typeof window !== "undefined" && window.location?.port && window.location.port !== "5173") {
    return window.location.origin;
  }
  return "http://127.0.0.1:8765";
}

export function resolveConnection(): Promise<{ base: string; token: string | null }> {
  if (resolved) return Promise.resolve(resolved);
  if (resolving) return resolving;
  resolving = (async () => {
    const bridge = typeof window !== "undefined" ? window.jtutor : undefined;
    if (bridge?.info) {
      try {
        const info = await bridge.info();
        if (info?.apiBase) {
          resolved = { base: info.apiBase, token: info.token };
          return resolved;
        }
      } catch {
        /* fall through to the dev default */
      }
    }
    resolved = { base: fallbackBase(), token: null };
    return resolved;
  })();
  return resolving;
}

/** Synchronous best guess, for building media URLs before the bridge resolves. */
export function apiBaseSync(): string {
  return resolved?.base ?? fallbackBase();
}

type RequestOptions = {
  method?: string;
  body?: unknown;
  signal?: AbortSignal;
  timeoutMs?: number;
  raw?: boolean;
};

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { base, token } = await resolveConnection();
  const { method = "GET", body, signal, timeoutMs = 30000, raw = false } = options;

  const controller = new AbortController();
  const onAbort = () => controller.abort();
  signal?.addEventListener("abort", onAbort, { once: true });
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  const headers: Record<string, string> = {};
  if (token) headers["x-jtutor-token"] = token;
  let payload: BodyInit | undefined;
  if (body instanceof FormData) {
    payload = body;
  } else if (body !== undefined) {
    headers["Content-Type"] = "application/json";
    payload = JSON.stringify(body);
  }

  let response: Response;
  try {
    response = await fetch(`${base}${path}`, { method, headers, body: payload, signal: controller.signal });
  } catch (err) {
    throw toApiError(err);
  } finally {
    clearTimeout(timer);
    signal?.removeEventListener("abort", onAbort);
  }

  if (!response.ok) {
    let parsed: { error?: { code?: string; message?: string; hint?: string; retryable?: boolean; detail?: string } } | null =
      null;
    try {
      parsed = await response.json();
    } catch {
      parsed = null;
    }
    const envelope = parsed?.error;
    throw new ApiError({
      code: (envelope?.code as ApiError["code"]) || "internal_error",
      message: envelope?.message || `${response.status} ${response.statusText}`,
      hint: envelope?.hint ?? null,
      retryable: envelope?.retryable ?? response.status >= 500,
      status: response.status,
      detail: envelope?.detail ?? null,
    });
  }

  if (raw) return response as unknown as T;
  const contentType = response.headers.get("content-type") || "";
  if (contentType.includes("application/json")) return (await response.json()) as T;
  return undefined as T;
}

export const api = {
  resolveConnection,
  base: apiBaseSync,

  health: (signal?: AbortSignal) => request<Health>("/health", { signal, timeoutMs: 8000 }),
  logTail: (lines = 200) => request<{ path: string; lines: string[] }>(`/log/tail?lines=${lines}`),

  // --- settings ---
  getSettings: (signal?: AbortSignal) => request<UserSettings>("/settings", { signal }),
  patchSettings: (changes: DeepPartial<UserSettings>) =>
    request<UserSettings>("/settings", { method: "PATCH", body: changes }),
  resetSettings: () => request<UserSettings>("/settings/reset", { method: "POST" }),

  // --- books & curriculum ---
  books: () => request<{ books: BookInfo[]; active: string }>("/books"),
  setBook: (bookId: string) =>
    request<{ ok: boolean; active: string; lesson_count: number }>("/books/active", {
      method: "POST",
      body: { book_id: bookId },
    }),
  progress: (signal?: AbortSignal) => request<ProgressOverview>("/progress", { signal }),
  lesson: (id: string) => request<Record<string, unknown>>(`/curriculum/${id}`),
  seedSrs: (id: string) => request<{ vocab_cards: number; grammar_cards: number }>(`/curriculum/${id}/seed-srs`, { method: "POST" }),

  // --- tutor ---
  startTutor: (id: string, signal?: AbortSignal) =>
    request<TutorPayload>(`/tutor/${id}/start`, { method: "POST", signal }),
  resetTutor: (id: string) => request<TutorPayload>(`/tutor/${id}/reset`, { method: "POST" }),
  advance: (id: string, signal?: AbortSignal) =>
    request<TutorPayload>(`/tutor/${id}/advance`, { method: "POST", signal }),
  jumpToCanDoQuiz: (id: string, resetCanDo = false) =>
    request<TutorPayload>(`/tutor/${id}/jump-can-do?reset_can_do=${resetCanDo ? "true" : "false"}`, {
      method: "POST",
    }),
  message: (id: string, text: string, spoken = false, signal?: AbortSignal) =>
    request<TutorPayload>(`/tutor/${id}/message`, { method: "POST", body: { text, spoken }, signal, timeoutMs: 120000 }),
  askTutor: (id: string, text: string, spoken = false, signal?: AbortSignal) =>
    request<TutorPayload>(`/tutor/${id}/ask`, { method: "POST", body: { text, spoken }, signal, timeoutMs: 120000 }),
  selfCheck: (id: string, canDoId: string, stars: number, comment = "") =>
    request<TutorPayload>(`/tutor/${id}/self-check`, {
      method: "POST",
      body: { can_do_id: canDoId, stars, comment },
    }),

  // --- srs ---
  srsDue: () => request<{ count: number; cards: SrsCard[] }>("/srs/due"),
  srsStats: () => request<{ total: number; due: number }>("/srs/stats"),
  srsReview: (cardId: number, rating: number) =>
    request<SrsCard>(`/srs/${cardId}/review`, { method: "POST", body: { rating } }),

  // --- voice ---
  voiceSpeakers: (signal?: AbortSignal) =>
    request<{ selected_speaker_id: number; options: VoiceSpeakerOption[] }>("/voice/speakers", { signal }),
  setVoiceSpeaker: (speakerId: number) =>
    request<{ ok: boolean; selected_speaker_id: number }>("/voice/set-speaker", {
      method: "POST",
      body: { speaker_id: speakerId },
    }),
  speechModelStatus: (signal?: AbortSignal) =>
    request<{ state: string; loaded: boolean; model: string; error: string | null }>("/voice/model-status", { signal }),

  speak: async (text: string, signal?: AbortSignal): Promise<Blob> => {
    const { base, token } = await resolveConnection();
    const headers: Record<string, string> = { "Content-Type": "application/json" };
    if (token) headers["x-jtutor-token"] = token;
    const r = await fetch(`${base}/voice/speak`, {
      method: "POST",
      headers,
      body: JSON.stringify({ text }),
      signal,
    });
    if (!r.ok) {
      const envelope = await r.json().catch(() => null);
      throw new ApiError({
        code: envelope?.error?.code || "voicevox_unavailable",
        message: envelope?.error?.message || "Tutor voice is unavailable.",
        hint: envelope?.error?.hint ?? null,
        retryable: true,
        status: r.status,
      });
    }
    return r.blob();
  },

  transcribe: async (
    blob: Blob,
    language = "ja",
    signal?: AbortSignal,
    hint?: string,
  ): Promise<Transcript> => {
    const form = new FormData();
    form.append("file", blob, "speech.webm");
    form.append("language", language);
    if (hint?.trim()) form.append("hint", hint.trim().slice(0, 200));
    return request<Transcript>("/voice/transcribe", {
      method: "POST",
      body: form,
      signal,
      timeoutMs: 120000,
    });
  },

  // --- media ---
  audioUrl: (relPath: string) => {
    const token = resolved?.token;
    const suffix = token ? `&token=${encodeURIComponent(token)}` : "";
    return `${apiBaseSync()}/media/audio?path=${encodeURIComponent(relPath)}${suffix}`;
  },
  pdfUrl: (
    which: "textbook" | "grammar" = "textbook",
    opts?: { bookId?: string | null; page?: number | null },
  ) => {
    const token = resolved?.token;
    const params = new URLSearchParams({ which });
    if (opts?.bookId) params.set("book", opts.bookId);
    if (token) params.set("token", token);
    const page = opts?.page && opts.page > 0 ? Math.floor(opts.page) : null;
    const hash = page ? `#page=${page}` : "";
    return `${apiBaseSync()}/media/pdf?${params.toString()}${hash}`;
  },
  pdfPageUrl: (
    which: "textbook" | "grammar" = "textbook",
    opts?: { bookId?: string | null; page?: number | null; scale?: number },
  ) => {
    const token = resolved?.token;
    const page = opts?.page && opts.page > 0 ? Math.floor(opts.page) : 1;
    const params = new URLSearchParams({
      which,
      page: String(page),
      scale: String(opts?.scale ?? 1.6),
    });
    if (opts?.bookId) params.set("book", opts.bookId);
    if (token) params.set("token", token);
    return `${apiBaseSync()}/media/pdf-page?${params.toString()}`;
  },
};

export { ApiError };
