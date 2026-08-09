import { useEffect, useRef, useState } from "react";
import type { PhasePresentation, TutorPhase } from "../../state/tutorPhase";
import { WaveformMeter } from "./WaveformMeter";

type Props = {
  phase: TutorPhase;
  presentation: PhasePresentation;
  micMode: "hold" | "toggle";
  recording: boolean;
  waveform: Float32Array;
  pendingAdvance: { startedAt: number; delayMs: number } | null;
  developerTools: boolean;
  canReplay: boolean;
  canSkip: boolean;
  onSkip: () => void;
  onPrimary: () => void;
  onPressStart: () => void;
  onPressEnd: () => void;
  onReplayTutor: () => void;
  onReplayBook: () => void;
  onCancelPendingAdvance: () => void;
  onRestart: () => void;
  onJumpCanDo: (reset: boolean) => void;
  onToggleContext: () => void;
};

function elapsed(startedAt: number | null): string {
  if (!startedAt) return "0:00";
  const s = Math.floor((Date.now() - startedAt) / 1000);
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
}

/**
 * The primary action lives here and only here, so it never moves between steps
 * and never scrolls off screen. Destructive and developer tools sit behind the
 * overflow menu.
 */
export function TransportBar(props: Props) {
  const {
    phase,
    presentation,
    micMode,
    recording,
    waveform,
    pendingAdvance,
    developerTools,
    canReplay,
    canSkip,
    onSkip,
    onPrimary,
    onPressStart,
    onPressEnd,
    onReplayTutor,
    onReplayBook,
    onCancelPendingAdvance,
    onRestart,
    onJumpCanDo,
    onToggleContext,
  } = props;

  const [menuOpen, setMenuOpen] = useState(false);
  const [, forceTick] = useState(0);
  const menuRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!recording) return;
    const id = setInterval(() => forceTick((n) => n + 1), 250);
    return () => clearInterval(id);
  }, [recording]);

  useEffect(() => {
    if (!menuOpen) return;
    const onClick = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) setMenuOpen(false);
    };
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setMenuOpen(false);
    document.addEventListener("mousedown", onClick);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onClick);
      document.removeEventListener("keydown", onKey);
    };
  }, [menuOpen]);

  const isRecordAction = presentation.primary.id === "record";
  const holdToTalk = isRecordAction && micMode === "hold";
  const startedAt = phase.kind === "recording" ? phase.startedAt : null;

  return (
    <div className="transport">
      <div className="transport__inner">
        <div className="transport__left">
          <button type="button" className="btn btn--ghost btn--icon" onClick={onReplayTutor} disabled={!canReplay}>
            <span aria-hidden>↺</span> Tutor
          </button>
          <button type="button" className="btn btn--ghost btn--icon" onClick={onReplayBook} disabled={!canReplay}>
            <span aria-hidden>💿</span> CD
          </button>
          {recording && <WaveformMeter waveform={waveform} active={recording} />}
        </div>

        <div className="transport__center">
          <p className="transport__status" role="status" aria-live="polite">
            {presentation.showSpinner && <span className="spinner" aria-hidden />}
            <span>{presentation.status}</span>
            {startedAt && <span className="transport__timer">{elapsed(startedAt)}</span>}
          </p>
          <button
            type="button"
            className={`btn btn--primary btn--lg mic-btn${isRecordAction ? "" : ""}`}
            data-recording={recording}
            disabled={presentation.busy && presentation.primary.id !== "cancel"}
            onClick={holdToTalk ? undefined : onPrimary}
            onPointerDown={holdToTalk ? onPressStart : undefined}
            onPointerUp={holdToTalk ? onPressEnd : undefined}
            onPointerLeave={holdToTalk && recording ? onPressEnd : undefined}
          >
            {pendingAdvance && (
              <span
                className="countdown"
                style={{ animationDuration: `${pendingAdvance.delayMs}ms` }}
                aria-hidden
              />
            )}
            {pendingAdvance ? "Continuing…" : presentation.primary.label}
          </button>
        </div>

        <div className="transport__right">
          {pendingAdvance && (
            <button type="button" className="btn btn--ghost" onClick={onCancelPendingAdvance}>
              Wait
            </button>
          )}
          {/* Always reachable: a learner with no microphone, or one who is stuck
              on a graded step, must still be able to move on. */}
          <button
            type="button"
            className="btn btn--ghost"
            onClick={onSkip}
            disabled={!canSkip}
            title="Move to the next step without answering"
          >
            Skip step
          </button>
          <button type="button" className="btn btn--ghost btn--icon" onClick={onToggleContext} title="Toggle side panel">
            <span aria-hidden>◨</span>
          </button>
          <div className="overflow-menu" ref={menuRef}>
            <button
              type="button"
              className="btn btn--ghost btn--icon"
              aria-haspopup="menu"
              aria-expanded={menuOpen}
              onClick={() => setMenuOpen((v) => !v)}
            >
              <span aria-hidden>⋯</span>
              <span className="visually-hidden">More lesson actions</span>
            </button>
            {menuOpen && (
              <div className="overflow-menu__list" role="menu">
                <button
                  type="button"
                  role="menuitem"
                  className="overflow-menu__item"
                  onClick={() => {
                    setMenuOpen(false);
                    onReplayBook();
                  }}
                >
                  Replay book audio
                </button>
                <div className="overflow-menu__sep" />
                <button
                  type="button"
                  role="menuitem"
                  className="overflow-menu__item"
                  data-danger="true"
                  onClick={() => {
                    setMenuOpen(false);
                    if (window.confirm("Start this lesson over? Your Can-do progress is kept.")) onRestart();
                  }}
                >
                  Start lesson over…
                </button>
                {developerTools && (
                  <>
                    <div className="overflow-menu__sep" />
                    <button
                      type="button"
                      role="menuitem"
                      className="overflow-menu__item"
                      onClick={() => {
                        setMenuOpen(false);
                        onJumpCanDo(false);
                      }}
                    >
                      Jump to Can-do check
                    </button>
                    <button
                      type="button"
                      role="menuitem"
                      className="overflow-menu__item"
                      data-danger="true"
                      onClick={() => {
                        setMenuOpen(false);
                        onJumpCanDo(true);
                      }}
                    >
                      Can-do check (reset passes)
                    </button>
                  </>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
