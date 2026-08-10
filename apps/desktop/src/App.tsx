import { useCallback, useEffect, useMemo, useState } from "react";
import { Navigate, Route, Routes, useLocation, useNavigate } from "react-router-dom";
import { api } from "./api/client";
import { LeftRail } from "./components/rail/LeftRail";
import { ServiceIndicator } from "./components/shell/ServiceIndicator";
import { SettingsDialog } from "./components/settings/SettingsDialog";
import { SetupWizard } from "./components/onboarding/SetupWizard";
import { WelcomeBack } from "./components/onboarding/WelcomeBack";
import { ProgressPage } from "./pages/ProgressPage";
import { SrsPage } from "./pages/SrsPage";
import { TutorPage } from "./pages/TutorPage";
import { useHealth } from "./state/useHealth";
import { useProgress } from "./state/useProgress";
import type { BookInfo, ProgressSnapshot } from "./api/types";

const WELCOME_KEY = "jtutor.welcomeShown";

export default function App() {
  const navigate = useNavigate();
  const location = useLocation();
  const { lessons, current, resume, loading, refresh } = useProgress();
  const { health, reachable, backendState, refresh: refreshHealth } = useHealth();

  const [settingsOpen, setSettingsOpen] = useState(false);
  const [setupOpen, setSetupOpen] = useState(false);
  const [welcomeOpen, setWelcomeOpen] = useState(false);
  const [contextOpen, setContextOpen] = useState(false);
  const [railOpen, setRailOpen] = useState(true);
  const [activeLesson, setActiveLesson] = useState<string>("");
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

  // After progress loads: resume the right lesson and show welcome-back once per launch.
  useEffect(() => {
    if (loading) return;
    const resumeId = resume?.lesson_id ?? current?.lesson_id;
    if (!resumeId) return;

    if (!activeLesson) setActiveLesson(resumeId);

    const onHome = location.pathname === "/" || location.pathname === "";
    const stuckOnDefault =
      location.pathname === "/tutor/L01" &&
      resumeId !== "L01" &&
      !sessionStorage.getItem(WELCOME_KEY);

    if (onHome || stuckOnDefault) {
      navigate(`/tutor/${resumeId}`, { replace: true });
    }

    if (!sessionStorage.getItem(WELCOME_KEY) && resume) {
      sessionStorage.setItem(WELCOME_KEY, "1");
      setWelcomeOpen(true);
    }
  }, [loading, resume, current, activeLesson, location.pathname, navigate]);

  const onProgressChanged = useCallback(() => {
    void refresh();
    api.srsStats().then(setSrs).catch(() => undefined);
  }, [refresh]);

  const selectBook = useCallback(
    async (bookId: string) => {
      await api.setBook(bookId).catch(() => undefined);
      setActiveBook(bookId);
      setBookTitle(books.find((b) => b.id === bookId)?.title ?? "Irodori");
      sessionStorage.removeItem(WELCOME_KEY);
      const overview = await api.progress().catch(() => null);
      await refresh();
      const nextId =
        overview?.resume?.lesson_id ?? overview?.lessons.find((l) => l.unlocked)?.lesson_id;
      if (nextId) {
        setActiveLesson(nextId);
        navigate(`/tutor/${nextId}`);
        if (overview?.resume) setWelcomeOpen(true);
      }
    },
    [books, navigate, refresh],
  );

  const defaultLesson = resume?.lesson_id ?? current?.lesson_id ?? "L01";
  const currentSummary = useMemo(
    () => lessons.find((l) => l.lesson_id === activeLesson) ?? current,
    [activeLesson, current, lessons],
  );

  const railProgress: ProgressSnapshot | null = useMemo(() => {
    if (lessonProgress) return lessonProgress;
    if (resume && resume.lesson_id === activeLesson && resume.percent != null) {
      return {
        fraction: (resume.percent ?? 0) / 100,
        percent: resume.percent ?? 0,
        phase: resume.phase ?? "book",
        label: resume.phase_label ?? "In progress",
      };
    }
    if (!currentSummary) return null;
    const total = (currentSummary.can_dos ?? []).length;
    const done = (currentSummary.can_dos ?? []).filter((c) => c.mastered).length;
    return {
      fraction: total ? done / total : 0,
      percent: total ? Math.round((done / total) * 100) : 0,
      phase: currentSummary.mastered ? "lesson_complete" : "book",
      label: currentSummary.mastered
        ? "Lesson complete"
        : total
          ? `${done}/${total} can-dos`
          : "In progress",
    };
  }, [currentSummary, lessonProgress, resume, activeLesson]);

  const showTransport = location.pathname.startsWith("/tutor");

  const goContinue = () => {
    const id = resume?.lesson_id ?? defaultLesson;
    setWelcomeOpen(false);
    setActiveLesson(id);
    navigate(`/tutor/${id}`);
  };

  const goBrowse = () => {
    setWelcomeOpen(false);
    navigate("/progress");
  };

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
        currentLessonId={activeLesson || defaultLesson}
        lessonProgress={railProgress}
        srs={srs}
        books={books}
        activeBook={activeBook}
        onSelectLesson={(id) => {
          setActiveLesson(id);
          navigate(`/tutor/${id}`);
        }}
        onSelectBook={(id) => void selectBook(id)}
        onReview={() => navigate("/srs")}
      />

      <Routes>
        <Route
          path="/"
          element={
            loading ? (
              <div className="page-loading" aria-busy="true">
                <p className="muted">Loading your place…</p>
              </div>
            ) : (
              <Navigate to={`/tutor/${defaultLesson}`} replace />
            )
          }
        />
        <Route
          path="/tutor/:lessonId"
          element={
            <TutorPage
              onLessonChange={setActiveLesson}
              onProgressChanged={onProgressChanged}
              contextOpen={contextOpen}
              onToggleContext={() => setContextOpen((v) => !v)}
              onContextOpenChange={setContextOpen}
            />
          }
        />
        <Route path="/srs" element={<SrsPage />} />
        <Route path="/progress" element={<ProgressPage lessons={lessons} bookTitle={bookTitle} />} />
        <Route
          path="*"
          element={
            loading ? (
              <div className="page-loading" aria-busy="true">
                <p className="muted">Loading your place…</p>
              </div>
            ) : (
              <Navigate to={`/tutor/${defaultLesson}`} replace />
            )
          }
        />
      </Routes>

      <SettingsDialog open={settingsOpen} onClose={() => setSettingsOpen(false)} health={health} />
      <SetupWizard
        open={setupOpen}
        health={health}
        onClose={() => setSetupOpen(false)}
        onRefresh={refreshHealth}
      />
      {resume && (
        <WelcomeBack
          open={welcomeOpen}
          resume={resume}
          bookTitle={bookTitle}
          onContinue={goContinue}
          onBrowse={goBrowse}
        />
      )}
    </div>
  );
}
