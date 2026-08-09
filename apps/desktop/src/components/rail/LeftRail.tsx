import { useMemo } from "react";
import type { LessonSummary, ProgressSnapshot } from "../../api/types";
import { ProgressRing } from "./ProgressRing";

type Props = {
  lessons: LessonSummary[];
  currentLessonId: string;
  lessonProgress: ProgressSnapshot | null;
  srs: { due: number; total: number };
  books: { id: string; title: string; available: boolean }[];
  activeBook: string;
  onSelectLesson: (lessonId: string) => void;
  onSelectBook: (bookId: string) => void;
  onReview: () => void;
};

type Group = { topic: string; lessons: LessonSummary[] };

function groupByTopic(lessons: LessonSummary[]): Group[] {
  const groups: Group[] = [];
  for (const lesson of lessons) {
    const topic = lesson.topic_en || "Lessons";
    const last = groups[groups.length - 1];
    if (last && last.topic === topic) last.lessons.push(lesson);
    else groups.push({ topic, lessons: [lesson] });
  }
  return groups;
}

export function LeftRail({
  lessons,
  currentLessonId,
  lessonProgress,
  srs,
  books,
  activeBook,
  onSelectLesson,
  onSelectBook,
  onReview,
}: Props) {
  const groups = useMemo(() => groupByTopic(lessons), [lessons]);
  const current = lessons.find((l) => l.lesson_id === currentLessonId);
  const mastered = current ? (current.can_dos ?? []).filter((c) => c.mastered).length : 0;
  const totalCanDos = current ? (current.can_dos ?? []).length : 0;

  return (
    <aside className="rail" aria-label="Lessons and progress">
      <section className="panel today">
        <p className="rail__section-title">Today</p>
        <div className="today__head">
          <div className="today__ring">
            <ProgressRing percent={lessonProgress?.percent ?? 0} />
          </div>
          <div>
            <p className="today__title">
              {current ? `${current.lesson_id} · ${current.title_en ?? ""}` : "Pick a lesson"}
            </p>
            <p className="today__meta">{lessonProgress?.label ?? "Not started"}</p>
            {totalCanDos > 0 && (
              <p className="today__meta">
                {mastered}/{totalCanDos} can-dos mastered
              </p>
            )}
          </div>
        </div>
      </section>

      <section>
        <label className="rail__section-title" htmlFor="book-select">
          Book
        </label>
        <select
          id="book-select"
          className="select"
          value={activeBook}
          onChange={(e) => onSelectBook(e.target.value)}
        >
          {books.map((b) => (
            <option key={b.id} value={b.id} disabled={!b.available}>
              {b.title}
              {b.available ? "" : " (not built)"}
            </option>
          ))}
        </select>
      </section>

      <nav aria-label="Lesson map">
        <p className="rail__section-title">Lessons</p>
        {groups.map((group) => (
          <div className="lesson-group" key={`${group.topic}-${group.lessons[0]?.lesson_id}`}>
            <p className="lesson-group__label">{group.topic}</p>
            {group.lessons.map((lesson) => {
              const done = (lesson.can_dos ?? []).filter((c) => c.mastered).length;
              const total = (lesson.can_dos ?? []).length;
              const isCurrent = lesson.lesson_id === currentLessonId;
              return (
                <button
                  key={lesson.lesson_id}
                  type="button"
                  className="lesson-row"
                  aria-current={isCurrent}
                  disabled={!lesson.unlocked}
                  title={
                    lesson.unlocked
                      ? lesson.title_en ?? lesson.lesson_id
                      : "Finish the Can-do checks in the previous lesson to unlock this"
                  }
                  onClick={() => onSelectLesson(lesson.lesson_id)}
                >
                  <span className="lesson-row__id">{lesson.lesson_id}</span>
                  <span className="lesson-row__title">{lesson.title_en ?? ""}</span>
                  {lesson.unlocked ? (
                    <span className="lesson-row__state" aria-label={`${done} of ${total} can-dos`}>
                      {total === 0 ? (
                        <span className="lesson-row__lock">intro</span>
                      ) : (
                        Array.from({ length: total }).map((_, i) => (
                          <span key={i} className="lesson-row__dot" data-done={i < done} />
                        ))
                      )}
                    </span>
                  ) : (
                    <span className="lesson-row__lock" aria-hidden>
                      🔒
                    </span>
                  )}
                </button>
              );
            })}
          </div>
        ))}
      </nav>

      {srs.total > 0 && (
        <section className="panel">
          <p className="rail__section-title">Review</p>
          <p className="today__meta">
            {srs.due} due · {srs.total} cards
          </p>
          <button type="button" className="btn btn--block" onClick={onReview} disabled={srs.due === 0}>
            {srs.due > 0 ? "Review now" : "Nothing due"}
          </button>
        </section>
      )}
    </aside>
  );
}
