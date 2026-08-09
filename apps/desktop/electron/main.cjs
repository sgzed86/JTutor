const { app, BrowserWindow, shell } = require("electron");
const path = require("path");
const { spawn } = require("child_process");
const http = require("http");

const API = "http://127.0.0.1:8765";
let backendProc = null;

function projectRoot() {
  if (app.isPackaged) {
    // extraResources land in process.resourcesPath
    return process.resourcesPath;
  }
  return path.join(__dirname, "..", "..", "..");
}

const gotLock = app.requestSingleInstanceLock();
if (!gotLock) {
  app.quit();
} else {
  app.on("second-instance", () => {
    const wins = BrowserWindow.getAllWindows();
    if (wins[0]) {
      if (wins[0].isMinimized()) wins[0].restore();
      wins[0].focus();
    }
  });
}

function startBackend() {
  const root = projectRoot();
  const python = process.env.JTUTOR_PYTHON || "python";
  const env = {
    ...process.env,
    JTUTOR_ROOT: root,
    PYTHONPATH: root,
    PYTHONIOENCODING: "utf-8",
  };
  backendProc = spawn(
    python,
    ["-m", "uvicorn", "backend.app.main:app", "--host", "127.0.0.1", "--port", "8765"],
    { cwd: root, env, stdio: "ignore", windowsHide: true }
  );
  backendProc.on("error", (err) => {
    console.error("Failed to start Python backend:", err.message);
  });
  backendProc.on("exit", (code) => {
    console.log("backend exited", code);
  });
}

function waitForHealth(timeoutMs = 45000) {
  const start = Date.now();
  return new Promise((resolve) => {
    const tick = () => {
      const req = http.get(`${API}/health`, (res) => {
        res.resume();
        if (res.statusCode === 200) return resolve(true);
        if (Date.now() - start > timeoutMs) return resolve(false);
        setTimeout(tick, 400);
      });
      req.on("error", () => {
        if (Date.now() - start > timeoutMs) return resolve(false);
        setTimeout(tick, 400);
      });
    };
    tick();
  });
}

function createWindow() {
  const win = new BrowserWindow({
    width: 1280,
    height: 860,
    minWidth: 960,
    minHeight: 640,
    title: "Jtutor",
    backgroundColor: "#1a2332",
    webPreferences: {
      preload: path.join(__dirname, "preload.cjs"),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  const devUrl = process.env.VITE_DEV_SERVER_URL || "http://127.0.0.1:5173";
  if (!app.isPackaged) {
    win.loadURL(devUrl);
    win.webContents.openDevTools({ mode: "detach" });
  } else {
    // Prefer API-served UI (same origin as API) so media/voice work cleanly
    win.loadURL(`${API}/`);
  }

  win.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: "deny" };
  });
}

app.whenReady().then(async () => {
  if (!gotLock) return;
  startBackend();
  const ok = await waitForHealth();
  if (!ok) {
    console.error("Backend did not respond on", API);
  }
  createWindow();
});

app.on("window-all-closed", () => {
  if (backendProc) {
    backendProc.kill();
    backendProc = null;
  }
  if (process.platform !== "darwin") app.quit();
});

app.on("before-quit", () => {
  if (backendProc) {
    backendProc.kill();
    backendProc = null;
  }
});
