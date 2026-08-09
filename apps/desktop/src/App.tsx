import { useCallback, useEffect, useMemo, useState } from "react";
import { Navigate, Route, Routes, useLocation, useNavigate } from "react-router-dom";
import { api } from "./api/client";
import { LeftRail } from "./components/rail/LeftRail";
import { ServiceIndicator } from "./components/shell/ServiceIndicator";
import { SettingsDialog } from "./components/settings/SettingsDialog";
import { SetupWizard } from "./components/onboarding/SetupWizard";
import { ProgressPage } from "./pages/ProgressPage";
import { SrsPage } from "./pages/SrsPage";
import { TutorPage } from "./pages/TutorPage";
import { useHealth } from "./state/useHealth";
import { useProgress } from "./state/useProgress";
import type { BookInfo, ProgressSnapshot } from "./api/types";

export default function App() {
  const navigate = useNavigate();
  const location = useLocation();
  const { lessons, current, refresh } = useProgress();
  const { health, reachable, backendState, refresh: refreshHealth } = useHealth();

  const [settingsOpen, setSettingsOpen] = useState(false);
  const [setupOpen, setSetupOpen] = useState(false);
  const [contextOpen, setContextOpen] = useState(true);
  const [railOpen, setRailOpen] = useState(true);
  const [activeLesson, setActiveLesson] = useState<string>("L01");
  const [lessonProgress] = useState<ProgressSnapshot | null>(null);
  const [books, setBooks] = useState<BookInfo[]>([]);
  const [activeBook, setActiveBook] = useState("starter");
  const [bookTitle, setBookTitle] = useState("Irodori");
  const [srs, setSrs] = useState({ due: 0, total: 0 });

  useEffect(() => {
    api
      .books()
      .then((data) => {
        setBooks(data.books);
        setActiveBook(data.active);
        setBookTitle(data.books.find((b) => b.id === data.active)?.title ?? "Irodori");
      })
      .catch(() => undefined);
    api.srsStats().then(setSrs).catch(() => undefined);
  }, []);

  useEffect(() => {
    const bridge = window.jtutor;
    if (!bridge?.onOpenSettings) return;
    return bridge.onOpenSettings(() => setSettingsOpen(true));
  }, []);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === ",") {
        e.preventDefault();
        setSettingsOpen(true);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const onProgressChanged = useCallback(() => {
    void refresh();
    api.srsStats().then(setSrs).catch(() => undefined);
  }, [refresh]);

  const selectBook = useCallback(
    async (bookId: string) => {
      await api.setBook(bookId).catch(() => undefined);
      setActiveBook(bookId);
      setBookTitle(books.find((b) => b.id === bookId)?.title ?? "Irodori");
      const overview = await api.progress().catch(() => null);
      const first = overview?.lessons.find((l) => l.unlocked);
      await refresh();
      if (first) navigate(`/tutor/${first.lesson_id}`);
    },
    [books, navigate, refresh],
  );

  const defaultLesson = current?.lesson_id ?? "L01";
  const currentSummary = useMemo(
    () => lessons.find((l) => l.lesson_id === activeLesson) ?? current,
    [activeLesson, current, lessons],
  );

  const railProgress: ProgressSnapshot | null = useMemo(() => {
    if (lessonProgress) return lessonProgress;
    if (!currentSummary) return null;
    const total = (currentSummary.can_dos ?? []).length;
    const done = (currentSummary.can_dos ?? []).filter((c) => c.mastered).length;
    return {
      fraction: total ? done / total : 0,
      percent: total ? Math.round((done / total) * 100) : 0,
      phase: currentSummary.mastered ? "lesson_complete" : "book",
      label: currentSummary.mastered ? "Lesson complete" : total ? `${done}/${total} can-dos` : "In progress",
    };
  }, [currentSummary, lessonProgress]);

  const showTransport = location.pathname.startsWith("/tutor");

  return (
    <div
      className="shell"
      data-context={contextOpen && showTransport ? "open" : "closed"}
      data-rail={railOpen ? "open" : "closed"}
      data-transport={showTransport ? "visible" : "hidden"}
    >
      <header className="titlebar">
        <button
          type="button"
          className="btn btn--ghost btn--icon"
          onClick={() => setRailOpen((v) => !v)}
          aria-label={railOpen ? "Hide lesson list" : "Show lesson list"}
        >
          ☰
        </button>
        <span className="titlebar__brand">
          J<span>tutor</span>
        </span>
        <span className="titlebar__lesson">
          {currentSummary ? `${currentSummary.lesson_id} · ${currentSummary.title_en ?? ""}` : bookTitle}
        </span>
        <span className="titlebar__spacer" />
        <button type="button" className="btn btn--ghost btn--icon" onClick={() => navigate("/progress")}>
          Progress
        </button>
        <button type="button" className="btn btn--ghost btn--icon" onClick={() => navigate("/srs")}>
          Review{srs.due ? ` (${srs.due})` : ""}
        </button>
        <ServiceIndicator
          health={health}
          reachable={reachable}
          backendState={backendState}
          onRefresh={refreshHealth}
          onOpenSetup={() => setSetupOpen(true)}
        />
        <button
          type="button"
          className="btn btn--ghost btn--icon"
          onClick={() => setSettingsOpen(true)}
          aria-label="Settings"
          title="Settings (Ctrl+,)"
        >
          ⚙
        </button>
      </header>

      <LeftRail
        lessons={lessons}
        currentLessonId={activeLesson}
        lessonProgress={railProgress}
        srs={srs}
        books={books}
        activeBook={activeBook}
        onSelectLesson={(id) => navigate(`/tutor/${id}`)}
        onSelectBook={(id) => void selectBook(id)}
        onReview={() => navigate("/srs")}
      />

      <Routes>
        <Route path="/" element={<Navigate to={`/tutor/${defaultLesson}`} replace />} />
        <Route
          path="/tutor/:lessonId"
          element={
            <TutorPage
              onLessonChange={setActiveLesson}
              onProgressChanged={onProgressChanged}
              contextOpen={contextOpen}
              onToggleContext={() => setContextOpen((v) => !v)}
            />
          }
        />
        <Route path="/srs" element={<SrsPage />} />
        <Route path="/progress" element={<ProgressPage lessons={lessons} bookTitle={bookTitle} />} />
        <Route path="*" element={<Navigate to={`/tutor/${defaultLesson}`} replace />} />
      </Routes>

      <SettingsDialog open={settingsOpen} onClose={() => setSettingsOpen(false)} health={health} />
      <SetupWizard
        open={setupOpen}
        health={health}
        onClose={() => setSetupOpen(false)}
        onRefresh={refreshHealth}
      />
    </div>
  );
}
