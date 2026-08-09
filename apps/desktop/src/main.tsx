import React from "react";
import ReactDOM from "react-dom/client";
import { HashRouter } from "react-router-dom";
import App from "./App";
import { ErrorBoundary } from "./components/feedback/ErrorBoundary";
import { SettingsProvider } from "./state/SettingsProvider";
import "./styles/tokens.css";
import "./styles/themes.css";
import "./styles/base.css";
import "./styles/components.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ErrorBoundary>
      <SettingsProvider>
        <HashRouter>
          <App />
        </HashRouter>
      </SettingsProvider>
    </ErrorBoundary>
  </React.StrictMode>,
);
