/**
 * Silent desktop launch for Windows shortcuts.
 * Ensures the Vite UI build is current, then starts Electron (no console).
 */
const { spawn, spawnSync } = require("child_process");
const fs = require("fs");
const path = require("path");

const root = path.resolve(__dirname, "..");
const uiIndex = path.join(root, "apps", "desktop", "dist", "index.html");
const srcDir = path.join(root, "apps", "desktop", "src");
const electronExe = path.join(root, "node_modules", "electron", "dist", "electron.exe");
const electronBin = process.platform === "win32" ? electronExe : require("electron");

function newestMtime(dir) {
  let newest = 0;
  if (!fs.existsSync(dir)) return newest;
  const stack = [dir];
  while (stack.length) {
    const cur = stack.pop();
    for (const name of fs.readdirSync(cur)) {
      const full = path.join(cur, name);
      let st;
      try {
        st = fs.statSync(full);
      } catch {
        continue;
      }
      if (st.isDirectory()) stack.push(full);
      else if (st.mtimeMs > newest) newest = st.mtimeMs;
    }
  }
  return newest;
}

function uiNeedsBuild() {
  if (!fs.existsSync(uiIndex)) return true;
  const builtAt = fs.statSync(uiIndex).mtimeMs;
  return newestMtime(srcDir) > builtAt + 1000;
}

function fail(message) {
  if (process.platform === "win32") {
    spawnSync(
      "powershell",
      ["-NoProfile", "-Command", `Add-Type -AssemblyName PresentationFramework; [System.Windows.MessageBox]::Show(${JSON.stringify(message)}, 'Jtutor')`],
      { windowsHide: true },
    );
  } else {
    console.error(message);
  }
  process.exit(1);
}

if (!fs.existsSync(electronBin)) {
  fail("Electron is missing.\n\nIn the Jtutor folder run:\n  npm install");
}

if (uiNeedsBuild()) {
  const build = spawnSync(process.platform === "win32" ? "npm.cmd" : "npm", ["run", "build:ui"], {
    cwd: root,
    stdio: "ignore",
    windowsHide: true,
    shell: process.platform === "win32",
  });
  if (build.status !== 0 || !fs.existsSync(uiIndex)) {
    fail("Jtutor could not build its UI.\n\nInstall Node.js LTS, then in the Jtutor folder run:\n  npm install\n  npm run build:ui");
  }
}

const child = spawn(electronBin, [root], {
  cwd: root,
  detached: true,
  stdio: "ignore",
  windowsHide: true,
  env: { ...process.env, ELECTRON_NO_ATTACH_CONSOLE: "1" },
});
child.unref();
