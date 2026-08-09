const { app, BrowserWindow, Menu, dialog, ipcMain, shell } = require("electron");
const fs = require("fs");
const path = require("path");

const { BackendSupervisor, BackendStartupError } = require("./backend.cjs");
const { buildMenu } = require("./menu.cjs");

let supervisor = null;
let mainWindow = null;
let splashWindow = null;
let quitting = false;

function projectRoot() {
  // extraResources land in process.resourcesPath when packaged.
  return app.isPackaged ? process.resourcesPath : path.join(__dirname, "..", "..", "..");
}

function createSplash() {
  const win = new BrowserWindow({
    width: 420,
    height: 260,
    frame: false,
    resizable: false,
    show: false,
    backgroundColor: "#141f33",
    webPreferences: { contextIsolation: true, nodeIntegration: false },
  });
  win.loadFile(path.join(__dirname, "splash.html"));
  win.once("ready-to-show", () => win.show());
  return win;
}

function setSplashStatus(text) {
  if (splashWindow && !splashWindow.isDestroyed()) {
    splashWindow.webContents.executeJavaScript(
      `window.setStatus && window.setStatus(${JSON.stringify(text)})`,
    ).catch(() => {});
  }
}

function createMainWindow(baseUrl) {
  const win = new BrowserWindow({
    width: 1360,
    height: 900,
    minWidth: 1024,
    minHeight: 680,
    title: "Jtutor",
    backgroundColor: "#141f33",
    show: false,
    webPreferences: {
      preload: path.join(__dirname, "preload.cjs"),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  const devUrl = process.env.VITE_DEV_SERVER_URL || "http://127.0.0.1:5173";
  const target = app.isPackaged ? `${baseUrl}/` : devUrl;
  win.loadURL(target);
  if (!app.isPackaged) win.webContents.openDevTools({ mode: "detach" });

  win.once("ready-to-show", () => {
    win.show();
    if (splashWindow && !splashWindow.isDestroyed()) splashWindow.close();
    splashWindow = null;
  });

  // Chromium's default error page told the user nothing.
  win.webContents.on("did-fail-load", (_e, errorCode, errorDescription, validatedURL, isMainFrame) => {
    if (!isMainFrame || errorCode === -3 /* aborted */) return;
    const params = new URLSearchParams({
      code: String(errorCode),
      message: errorDescription || "The Jtutor window could not load.",
      url: validatedURL || target,
    });
    win.loadFile(path.join(__dirname, "error.html"), { search: `?${params.toString()}` });
  });

  win.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: "deny" };
  });

  return win;
}

function showStartupFailure(err) {
  const diagnostics = supervisor ? supervisor.diagnostics() : {};
  const tail = (err.logTail && err.logTail.length ? err.logTail : diagnostics.logTail || []).slice(-12);
  const detail = [
    err.hint,
    "",
    tail.length ? "Last log lines:" : "",
    ...tail,
  ]
    .filter(Boolean)
    .join("\n");

  const choice = dialog.showMessageBoxSync({
    type: "error",
    title: "Jtutor could not start",
    message: err.message || "The Jtutor backend did not start.",
    detail,
    buttons: ["Retry", "Open log", "Quit"],
    defaultId: 0,
    cancelId: 2,
  });

  if (choice === 0) return "retry";
  if (choice === 1) {
    if (diagnostics.logPath) shell.showItemInFolder(diagnostics.logPath);
    return "quit";
  }
  return "quit";
}

function broadcastBackendState(state, detail) {
  if (mainWindow && !mainWindow.isDestroyed()) {
    mainWindow.webContents.send("jtutor:backend-state", { state, detail: detail || null });
  }
}

async function boot() {
  splashWindow = createSplash();

  supervisor = new BackendSupervisor({
    resourcesPath: projectRoot(),
    userDataPath: app.getPath("userData"),
    isPackaged: app.isPackaged,
    onLog: (line) => {
      if (!app.isPackaged) console.log("[backend]", line);
    },
    onState: (state, detail) => broadcastBackendState(state, detail),
  });

  const slowTimer = setTimeout(
    () => setSplashStatus("Still starting — the first run prepares the speech model."),
    8000,
  );
  const slowerTimer = setTimeout(() => setSplashStatus("Almost there…"), 20000);

  try {
    setSplashStatus("Tidying up from last time…");
    await supervisor.sweepOrphans();
    setSplashStatus("Starting Jtutor…");
    const { spawnFailure } = await supervisor.start();
    await supervisor.waitForHealth(60000, { spawnFailure });
    clearTimeout(slowTimer);
    clearTimeout(slowerTimer);
    mainWindow = createMainWindow(supervisor.baseUrl);
    return true;
  } catch (err) {
    clearTimeout(slowTimer);
    clearTimeout(slowerTimer);
    if (splashWindow && !splashWindow.isDestroyed()) splashWindow.close();
    splashWindow = null;
    const failure = err instanceof BackendStartupError ? err : new BackendStartupError(String(err && err.message));
    const action = showStartupFailure(failure);
    if (action === "retry") {
      await supervisor.stop().catch(() => {});
      return boot();
    }
    return false;
  }
}

function registerIpc() {
  ipcMain.handle("jtutor:info", () => ({
    apiBase: supervisor ? supervisor.baseUrl : null,
    token: supervisor ? supervisor.token : null,
    platform: process.platform,
    version: app.getVersion(),
    isPackaged: app.isPackaged,
    logPath: supervisor ? supervisor.logPath : null,
    dataDir: supervisor ? supervisor.dataDir : null,
  }));

  ipcMain.handle("jtutor:open-logs", () => {
    if (!supervisor) return false;
    try {
      if (fs.existsSync(supervisor.logPath)) shell.showItemInFolder(supervisor.logPath);
      else shell.openPath(supervisor.logDir);
      return true;
    } catch {
      return false;
    }
  });

  ipcMain.handle("jtutor:open-path", (_e, target) => shell.openPath(String(target || "")));

  ipcMain.handle("jtutor:restart-backend", async () => {
    if (!supervisor) return false;
    supervisor.restarts = 0;
    await supervisor.stop().catch(() => {});
    const { spawnFailure } = await supervisor.start();
    await supervisor.waitForHealth(60000, { spawnFailure });
    return supervisor.baseUrl;
  });

  ipcMain.handle("jtutor:diagnostics", () => (supervisor ? supervisor.diagnostics() : null));
}

if (!app.requestSingleInstanceLock()) {
  app.quit();
} else {
  app.on("second-instance", () => {
    if (mainWindow) {
      if (mainWindow.isMinimized()) mainWindow.restore();
      mainWindow.focus();
    }
  });

  app.whenReady().then(async () => {
    registerIpc();
    Menu.setApplicationMenu(buildMenu({ onOpenSettings: () => mainWindow?.webContents.send("jtutor:open-settings") }));
    const ok = await boot();
    if (!ok) app.quit();
  });
}

app.on("activate", () => {
  if (BrowserWindow.getAllWindows().length === 0 && supervisor && supervisor.baseUrl) {
    mainWindow = createMainWindow(supervisor.baseUrl);
  }
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});

// Hold the quit open until the backend is actually reaped, so closing the window
// can never leave a stray process holding a port.
app.on("before-quit", async (event) => {
  if (quitting || !supervisor) return;
  event.preventDefault();
  quitting = true;
  try {
    await supervisor.stop();
  } catch {
    /* fall through to quit regardless */
  }
  app.exit(0);
});

for (const signal of ["SIGINT", "SIGTERM"]) {
  process.on(signal, () => {
    if (quitting) return;
    quitting = true;
    const done = supervisor ? supervisor.stop() : Promise.resolve();
    done.finally(() => app.exit(0));
  });
}

process.on("uncaughtException", (err) => {
  const message = err && err.stack ? err.stack : String(err);
  if (supervisor) supervisor.log(`main process error: ${message}`);
  dialog.showErrorBox("Jtutor hit an unexpected error", message);
});
