/**
 * Yuki — layered inline SVG.
 *
 * Replaces three 427x640 PNGs (1.07 MB) that were swapped wholesale every
 * 180 ms. Here the body is static and only a mouth/eye `<g>` changes class, so
 * a frame costs one attribute write instead of an image decode. The mouth is
 * driven by the real output level from the audio pipeline, so it stops when the
 * audio stops instead of flapping on a timer.
 */

import { useEffect, useMemo, useState } from "react";
import type { AvatarMood } from "../../state/tutorPhase";

type Props = {
  mood: AvatarMood;
  /** 0..1 output level from the audio pipeline; drives the visemes. */
  level?: number;
  reduceMotion?: boolean;
};

type Eyes = "open" | "half" | "closed" | "happy";
type Mouth = "closed" | "smile" | "small" | "open";
type Brows = "neutral" | "raised" | "concerned";

const MOOD_CAPTION: Record<AvatarMood, string> = {
  idle: "Here with you",
  speaking: "Speaking",
  listening: "Listening",
  thinking: "Thinking",
  celebrating: "Nice work!",
  encouraging: "Keep going",
};

const MOUTH_PATHS: Record<Mouth, string> = {
  closed: "M86 132 Q100 136 114 132",
  smile: "M84 130 Q100 141 116 130",
  small: "M92 130 Q100 138 108 130 Q100 136 92 130 Z",
  open: "M88 128 Q100 148 112 128 Q100 140 88 128 Z",
};

function visemeFor(level: number): Mouth {
  if (level < 0.06) return "closed";
  if (level < 0.16) return "small";
  return "open";
}

export function Avatar({ mood, level = 0, reduceMotion = false }: Props) {
  const [blinking, setBlinking] = useState(false);

  useEffect(() => {
    if (reduceMotion || mood === "celebrating") return;
    let cancelled = false;
    let openTimer: ReturnType<typeof setTimeout> | undefined;
    let closeTimer: ReturnType<typeof setTimeout> | undefined;
    const schedule = () => {
      closeTimer = setTimeout(
        () => {
          if (cancelled) return;
          setBlinking(true);
          openTimer = setTimeout(() => {
            if (cancelled) return;
            setBlinking(false);
            schedule();
          }, 140);
        },
        4000 + Math.random() * 3000,
      );
    };
    schedule();
    return () => {
      cancelled = true;
      if (openTimer) clearTimeout(openTimer);
      if (closeTimer) clearTimeout(closeTimer);
    };
  }, [mood, reduceMotion]);

  const { eyes, brows, mouth } = useMemo(() => {
    let e: Eyes = "open";
    let b: Brows = "neutral";
    let m: Mouth = "closed";

    if (mood === "speaking") m = reduceMotion ? "open" : visemeFor(level);
    if (mood === "listening") {
      b = "raised";
      m = "closed";
    }
    if (mood === "thinking") {
      e = "half";
      b = "raised";
    }
    if (mood === "celebrating") {
      e = "happy";
      m = "open";
    }
    if (mood === "encouraging") {
      b = "concerned";
      m = "smile";
    }
    if (mood === "idle") m = "smile";
    if (blinking && e === "open") e = "closed";
    return { eyes: e, brows: b, mouth: m };
  }, [blinking, level, mood, reduceMotion]);

  const pupilShift = mood === "thinking" ? -2.5 : mood === "listening" ? 0 : 0;

  return (
    <div className="avatar" data-mood={mood}>
      <div className="avatar__caption">
        <span className="avatar__name">Yuki</span>
        <span>{MOOD_CAPTION[mood]}</span>
      </div>
      <div className="avatar__frame">
        <svg className="avatar__svg" viewBox="0 0 200 260" role="img" aria-label={`Yuki, ${MOOD_CAPTION[mood]}`}>
          <defs>
            <linearGradient id="yuki-hair" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#7d5a44" />
              <stop offset="100%" stopColor="#5d3f2e" />
            </linearGradient>
            <linearGradient id="yuki-top" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stopColor="#a9bf98" />
              <stop offset="100%" stopColor="#8aa87c" />
            </linearGradient>
            <radialGradient id="yuki-cheek" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#e8a08c" stopOpacity="0.55" />
              <stop offset="100%" stopColor="#e8a08c" stopOpacity="0" />
            </radialGradient>
          </defs>

          {/* shoulders / cardigan */}
          <path d="M28 260 Q34 196 78 178 L122 178 Q166 196 172 260 Z" fill="url(#yuki-top)" />
          <path d="M78 178 Q100 200 122 178 L122 190 Q100 210 78 190 Z" fill="#f0e6d8" />

          {/* neck */}
          <path d="M86 158 h28 v26 q-14 10 -28 0 Z" fill="#f0cdb4" />

          {/* hair back */}
          <path d="M52 106 q0 -66 48 -66 t48 66 q4 42 -6 62 q-8 -34 -12 -44 q-30 12 -60 0 q-4 10 -12 44 q-10 -20 -6 -62 Z" fill="url(#yuki-hair)" />

          {/* face */}
          <ellipse cx="100" cy="112" rx="42" ry="48" fill="#fbdcc4" />
          <ellipse cx="74" cy="128" rx="12" ry="8" fill="url(#yuki-cheek)" />
          <ellipse cx="126" cy="128" rx="12" ry="8" fill="url(#yuki-cheek)" />

          {/* fringe */}
          <path d="M58 100 q6 -50 42 -52 t42 52 q-16 -22 -42 -22 t-42 22 Z" fill="url(#yuki-hair)" />

          {/* brows */}
          <g stroke="#5d3f2e" strokeWidth="3" strokeLinecap="round" fill="none">
            {brows === "neutral" && (
              <>
                <path d="M76 92 q10 -5 20 -1" />
                <path d="M124 92 q-10 -5 -20 -1" />
              </>
            )}
            {brows === "raised" && (
              <>
                <path d="M76 87 q10 -6 20 -2" />
                <path d="M124 87 q-10 -6 -20 -2" />
              </>
            )}
            {brows === "concerned" && (
              <>
                <path d="M76 90 q10 2 20 -3" />
                <path d="M124 90 q-10 2 -20 -3" />
              </>
            )}
          </g>

          {/* eyes */}
          <g>
            {eyes === "closed" ? (
              <g stroke="#3b2a20" strokeWidth="3" strokeLinecap="round" fill="none">
                <path d="M78 108 q8 5 16 0" />
                <path d="M122 108 q-8 5 -16 0" />
              </g>
            ) : eyes === "happy" ? (
              <g stroke="#3b2a20" strokeWidth="3" strokeLinecap="round" fill="none">
                <path d="M78 110 q8 -8 16 0" />
                <path d="M122 110 q-8 -8 -16 0" />
              </g>
            ) : (
              <>
                <ellipse cx="86" cy="108" rx="7" ry={eyes === "half" ? 4 : 8} fill="#fff" />
                <ellipse cx="114" cy="108" rx="7" ry={eyes === "half" ? 4 : 8} fill="#fff" />
                <circle cx={86 + pupilShift} cy="108" r={eyes === "half" ? 3 : 4.4} fill="#4a3327" />
                <circle cx={114 + pupilShift} cy="108" r={eyes === "half" ? 3 : 4.4} fill="#4a3327" />
                <circle cx={87.6 + pupilShift} cy="106" r="1.4" fill="#fff" />
                <circle cx={115.6 + pupilShift} cy="106" r="1.4" fill="#fff" />
              </>
            )}
          </g>

          {/* nose + mouth */}
          <path d="M100 116 q3 6 -2 8" stroke="#d9a98c" strokeWidth="2" fill="none" strokeLinecap="round" />
          <path
            d={MOUTH_PATHS[mouth]}
            fill={mouth === "open" || mouth === "small" ? "#b4655f" : "none"}
            stroke="#a85a55"
            strokeWidth="2.5"
            strokeLinecap="round"
          />
        </svg>
        <span className="avatar__ring" aria-hidden />
      </div>
    </div>
  );
}
