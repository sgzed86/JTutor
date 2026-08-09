import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api";

export default function ProgressMap() {
  const [lessons, setLessons] = useState<any[]>([]);
  const navigate = useNavigate();

  useEffect(() => {
    api.progress().then((p) => setLessons(p.lessons || []));
  }, []);

  return (
    <div className="stack">
      <div>
        <h1>Progress map</h1>
        <p className="muted">Pass each lesson’s Can-do quiz to unlock the next.</p>
      </div>
      <div className="lesson-map">
        {lessons.map((l) => {
          const unlocked = l.unlocked;
          const masteredCount = (l.can_dos || []).filter((c: any) => c.mastered).length;
          const total = (l.can_dos || []).length;
          return (
            <button
              key={l.lesson_id}
              className={`lesson-tile ${!unlocked ? "locked" : ""} ${l.mastered ? "mastered" : ""}`}
              disabled={!unlocked}
              onClick={() => navigate(`/tutor/${l.lesson_id}`)}
            >
              <div className="muted">{l.lesson_id}</div>
              <h3>{l.title_en}</h3>
              <p className="muted" style={{ fontSize: "0.8rem" }}>{l.topic_en}</p>
              {total > 0 ? (
                <p style={{ marginTop: "0.5rem" }}>
                  {masteredCount}/{total} can-dos
                </p>
              ) : (
                <p style={{ marginTop: "0.5rem" }} className="muted">Intro</p>
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}
