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
  const resume = overview?.resume ?? null;
  const current =
    (resume?.lesson_id && lessons.find((l) => l.lesson_id === resume.lesson_id)) ||
    lessons.find((l) => l.unlocked && !l.mastered && (l.can_dos?.length ?? 0) > 0) ||
    lessons.find((l) => l.unlocked && !l.mastered) ||
    lessons[0];

  return { overview, lessons, current, resume, loading, refresh };
}
