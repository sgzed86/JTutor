import { useEffect, useRef, useState } from "react";
import type { Health } from "../../api/types";

const DESCRIPTIONS: Record<string, { name: string; purpose: string; fix: string; url?: string }> = {
  backend: {
    name: "Jtutor engine",
    purpose: "Runs the lessons, grading and progress.",
    fix: "Restart Jtutor if this is red.",
  },
  voicevox: {
    name: "VOICEVOX",
    purpose: "Gives Yuki her voice.",
    fix: "Start VOICEVOX. Without it, lessons run silently.",
    url: "https://voicevox.hiroshiba.jp/",
  },
  ollama: {
    name: "Ollama",
    purpose: "Answers your Ask Yuki questions.",
    fix: "Start Ollama. Without it, you still get phrase hints.",
    url: "https://ollama.com/",
  },
  whisper: {
    name: "Speech recognition",
    purpose: "Turns what you say into text for grading.",
    fix: "Loads on first use; check Settings → Advanced.",
  },
};

export function ServiceIndicator({
  health,
  reachable,
  backendState,
  onRefresh,
  onOpenSetup,
}: {
  health: Health | null;
  reachable: boolean;
  backendState: string;
  onRefresh: () => void;
  onOpenSetup: () => void;
}) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!open) return;
    const onClick = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    document.addEventListener("mousedown", onClick);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onClick);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  const services = health?.services ?? {};
  const optionalDown = Object.entries(services).filter(([, v]) => !v.required && !v.ok).length;
  const state = !reachable || backendState === "failed" ? "down" : optionalDown > 0 ? "degraded" : "ok";
  const label = state === "ok" ? "All services ready" : state === "down" ? "Backend unreachable" : `${optionalDown} optional service${optionalDown === 1 ? "" : "s"} off`;

  return (
    <div className="services" ref={ref}>
      <button
        type="button"
        className="services__button"
        aria-expanded={open}
        aria-haspopup="dialog"
        onClick={() => {
          setOpen((v) => !v);
          onRefresh();
        }}
      >
        <span className="services__dot" data-state={state} aria-hidden />
        {backendState === "reconnecting" ? "Reconnecting…" : label}
      </button>

      {open && (
        <div className="services__popover" role="dialog" aria-label="Service status">
          {Object.entries(DESCRIPTIONS).map(([key, info]) => {
            const ok = key === "backend" ? reachable : Boolean(services[key]?.ok);
            return (
              <div className="service-row" key={key}>
                <span className="service-row__dot" data-ok={ok} aria-hidden />
                <div>
                  <div className="service-row__name">{info.name}</div>
                  <div className="service-row__desc">{ok ? info.purpose : `${info.purpose} ${info.fix}`}</div>
                </div>
                {!ok && info.url && (
                  <a className="btn btn--ghost btn--icon" href={info.url} target="_blank" rel="noreferrer">
                    Get it
                  </a>
                )}
              </div>
            );
          })}
          <div className="dialog__foot" style={{ padding: 0, borderTop: "none" }}>
            <button type="button" className="btn btn--ghost" onClick={onRefresh}>
              Check again
            </button>
            <button type="button" className="btn" onClick={() => { setOpen(false); onOpenSetup(); }}>
              Setup guide
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
