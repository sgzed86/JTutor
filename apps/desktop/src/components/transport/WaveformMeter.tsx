import { useEffect, useRef } from "react";

/**
 * Live input level while recording. Drawn to a canvas rather than 48 React nodes
 * so it costs nothing per frame.
 */
export function WaveformMeter({ waveform, active }: { waveform: Float32Array; active: boolean }) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const rafRef = useRef<number | null>(null);

  useEffect(() => {
    if (!active) {
      if (rafRef.current !== null) cancelAnimationFrame(rafRef.current);
      rafRef.current = null;
      const canvas = canvasRef.current;
      const ctx = canvas?.getContext("2d");
      if (canvas && ctx) ctx.clearRect(0, 0, canvas.width, canvas.height);
      return;
    }

    const draw = () => {
      const canvas = canvasRef.current;
      const ctx = canvas?.getContext("2d");
      if (!canvas || !ctx) return;
      const dpr = window.devicePixelRatio || 1;
      const width = canvas.clientWidth * dpr;
      const height = canvas.clientHeight * dpr;
      if (canvas.width !== width || canvas.height !== height) {
        canvas.width = width;
        canvas.height = height;
      }
      ctx.clearRect(0, 0, width, height);

      const styles = getComputedStyle(document.documentElement);
      const accent = styles.getPropertyValue("--accent").trim() || "#e0a45a";
      const muted = styles.getPropertyValue("--border-strong").trim() || "rgba(255,255,255,.24)";

      const bars = waveform.length;
      const gap = 2 * dpr;
      const barWidth = Math.max(1, width / bars - gap);
      for (let i = 0; i < bars; i += 1) {
        const value = waveform[i] || 0;
        const h = Math.max(2 * dpr, value * height);
        const x = i * (barWidth + gap);
        const y = (height - h) / 2;
        ctx.fillStyle = value > 0.04 ? accent : muted;
        ctx.beginPath();
        const r = Math.min(barWidth / 2, 2 * dpr);
        ctx.roundRect(x, y, barWidth, h, r);
        ctx.fill();
      }
      rafRef.current = requestAnimationFrame(draw);
    };
    rafRef.current = requestAnimationFrame(draw);
    return () => {
      if (rafRef.current !== null) cancelAnimationFrame(rafRef.current);
      rafRef.current = null;
    };
  }, [active, waveform]);

  return <canvas ref={canvasRef} className="waveform" aria-hidden />;
}
