import { Component } from "react";
import type { ErrorInfo, ReactNode } from "react";

type State = { error: Error | null };

/** One bad payload should not white-screen the whole app. */
export class ErrorBoundary extends Component<{ children: ReactNode }, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    // eslint-disable-next-line no-console
    console.error("Jtutor UI error", error, info.componentStack);
  }

  render() {
    const { error } = this.state;
    if (!error) return this.props.children;
    return (
      <div className="page">
        <div className="panel empty-state">
          <h2>Something went wrong on this screen</h2>
          <p>The lesson itself is safe — your progress is stored by the backend.</p>
          <p className="muted" style={{ fontSize: "var(--fs-xs)" }}>
            {error.message}
          </p>
          <button type="button" className="btn btn--primary" onClick={() => this.setState({ error: null })}>
            Try again
          </button>
        </div>
      </div>
    );
  }
}
