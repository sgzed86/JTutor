import { useCallback, useEffect, useState } from "react";
import { api } from "../api/client";
import type { LessonSummary, ProgressOverview } from "../api/types";

export function useProgress() {
  const [overview, setOverview] = useState<ProgressOverview | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    try {
      setOverview(await api.progress());
    } catch {
      /* the service indicator surfaces backend problems */
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const lessons: LessonSummary[] = overview?.lessons ?? [];
  const current =
    lessons.find((l) => l.unlocked && !l.mastered && (l.can_dos?.length ?? 0) > 0) ??
    lessons.find((l) => l.unlocked && !l.mastered) ??
    lessons[0];

  return { overview, lessons, current, loading, refresh };
}
