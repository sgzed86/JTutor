const { contextBridge, ipcRenderer } = require("electron");

/**
 * The renderer no longer hardcodes a port. The supervisor picks a free one at
 * launch and hands it over with a per-run token.
 */
contextBridge.exposeInMainWorld("jtutor", {
  // Resolved asynchronously; api.ts awaits this before its first request.
  info: () => ipcRenderer.invoke("jtutor:info"),
  openLogs: () => ipcRenderer.invoke("jtutor:open-logs"),
  openPath: (target) => ipcRenderer.invoke("jtutor:open-path", target),
  restartBackend: () => ipcRenderer.invoke("jtutor:restart-backend"),
  diagnostics: () => ipcRenderer.invoke("jtutor:diagnostics"),
  onBackendState: (handler) => {
    const listener = (_event, payload) => handler(payload);
    ipcRenderer.on("jtutor:backend-state", listener);
    return () => ipcRenderer.removeListener("jtutor:backend-state", listener);
  },
  onOpenSettings: (handler) => {
    const listener = () => handler();
    ipcRenderer.on("jtutor:open-settings", listener);
    return () => ipcRenderer.removeListener("jtutor:open-settings", listener);
  },
});
