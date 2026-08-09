import { useNavigate } from "react-router-dom";
import type { LessonSummary } from "../api/types";

export function ProgressPage({ lessons, bookTitle }: { lessons: LessonSummary[]; bookTitle: string }) {
  const navigate = useNavigate();

  return (
    <main className="main">
      <div className="page">
        <div className="page__head">
          <div>
            <h1>Progress</h1>
            <p className="muted">{bookTitle} — pass each lesson's Can-do checks to unlock the next.</p>
          </div>
        </div>

        <div className="lesson-grid">
          {lessons.map((lesson) => {
            const total = (lesson.can_dos ?? []).length;
            const done = (lesson.can_dos ?? []).filter((c) => c.mastered).length;
            return (
              <button
                key={lesson.lesson_id}
                type="button"
                className="lesson-card"
                data-mastered={lesson.mastered}
                disabled={!lesson.unlocked}
                onClick={() => navigate(`/tutor/${lesson.lesson_id}`)}
                title={lesson.unlocked ? undefined : "Finish the previous lesson's Can-do checks first"}
              >
                <span className="lesson-card__head">
                  <span className="muted">{lesson.lesson_id}</span>
                  {lesson.mastered ? (
                    <span className="pill pill--ok">Mastered</span>
                  ) : lesson.unlocked ? (
                    <span className="pill">{total ? `${done}/${total}` : "Intro"}</span>
                  ) : (
                    <span className="pill" aria-label="Locked">
                      🔒 Locked
                    </span>
                  )}
                </span>
                <h3>{lesson.title_en}</h3>
                <p className="muted" style={{ fontSize: "var(--fs-xs)" }}>
                  {lesson.topic_en}
                </p>
              </button>
            );
          })}
        </div>
      </div>
    </main>
  );
}
