const API =
  (typeof window !== "undefined" && (window as any).jtutor?.apiBase) ||
  "http://127.0.0.1:8765";

/** Client-side debug events (mirrored to data/jtutor.log on the API). */
export function jlog(event: string, detail: Record<string, unknown> = {}) {
  const line = `[jtutor-ui] ${event} ${JSON.stringify(detail)}`;
  if (import.meta.env.DEV) {
    console.debug(line);
  }
  void fetch(`${API}/log/client`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ source: "tutor-ui", event, detail }),
  }).catch(() => {});
}
