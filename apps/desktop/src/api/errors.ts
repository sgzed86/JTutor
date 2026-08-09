/** Typed problem envelope returned by the backend (backend/app/errors.py). */

export type ErrorCode =
  | "internal_error"
  | "invalid_request"
  | "unauthorized"
  | "lesson_not_found"
  | "lesson_locked"
  | "voicevox_unavailable"
  | "whisper_unavailable"
  | "ollama_unavailable"
  | "audio_missing"
  | "pdf_missing"
  | "ui_not_built"
  | "network"
  | "aborted";

export type Severity = "info" | "warning" | "error";

const SEVERITY: Partial<Record<ErrorCode, Severity>> = {
  voicevox_unavailable: "info",
  ollama_unavailable: "info",
  audio_missing: "warning",
  pdf_missing: "warning",
  whisper_unavailable: "warning",
  lesson_locked: "warning",
  network: "error",
};

export class ApiError extends Error {
  readonly code: ErrorCode;
  readonly hint: string | null;
  readonly retryable: boolean;
  readonly status: number;
  readonly detail: string | null;

  constructor(init: {
    code: ErrorCode;
    message: string;
    hint?: string | null;
    retryable?: boolean;
    status?: number;
    detail?: string | null;
  }) {
    super(init.message);
    this.name = "ApiError";
    this.code = init.code;
    this.hint = init.hint ?? null;
    this.retryable = init.retryable ?? false;
    this.status = init.status ?? 0;
    this.detail = init.detail ?? null;
  }

  get severity(): Severity {
    return SEVERITY[this.code] ?? "error";
  }

  static network(message: string): ApiError {
    return new ApiError({
      code: "network",
      message: message || "Can't reach the Jtutor backend.",
      hint: "It may still be starting. Retrying usually fixes this.",
      retryable: true,
    });
  }

  static aborted(): ApiError {
    return new ApiError({ code: "aborted", message: "Cancelled." });
  }
}

export function isAbort(err: unknown): boolean {
  return (
    (err instanceof ApiError && err.code === "aborted") ||
    (err instanceof DOMException && err.name === "AbortError") ||
    (err instanceof Error && err.name === "AbortError")
  );
}

export function toApiError(err: unknown): ApiError {
  if (err instanceof ApiError) return err;
  if (isAbort(err)) return ApiError.aborted();
  return ApiError.network(err instanceof Error ? err.message : String(err));
}
