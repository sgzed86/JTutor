import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../api/client";
import type { Health } from "../api/types";

export type BackendState = "starting" | "ready" | "reconnecting" | "stopping" | "failed" | "unknown";

export type HealthState = {
  health: Health | null;
  reachable: boolean;
  backendState: BackendState;
  refresh: () => void;
};

const POLL_MS = 15000;

export function useHealth(): HealthState {
  const [health, setHealth] = useState<Health | null>(null);
  const [reachable, setReachable] = useState(true);
  const [backendState, setBackendState] = useState<BackendState>("unknown");
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const refresh = useCallback(() => {
    const controller = new AbortController();
    api
      .health(controller.signal)
      .then((value) => {
        setHealth(value);
        setReachable(true);
      })
      .catch(() => setReachable(false));
  }, []);

  useEffect(() => {
    refresh();
    timerRef.current = setInterval(refresh, POLL_MS);
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [refresh]);

  // The Electron supervisor pushes its own lifecycle so a crash shows up
  // immediately rather than on the next poll.
  useEffect(() => {
    const bridge = window.jtutor;
    if (!bridge?.onBackendState) return;
    return bridge.onBackendState(({ state }) => {
      setBackendState(state as BackendState);
      if (state === "ready") refresh();
    });
  }, [refresh]);

  return { health, reachable, backendState, refresh };
}
