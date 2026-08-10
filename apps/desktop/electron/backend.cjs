/**
 * Supervises the FastAPI backend as a child of the Electron main process.
 *
 * Everything that made the old inline `spawn()` unreliable lives here: choosing
 * a free port, minting a per-run token, resolving an interpreter (or the frozen
 * executable), keeping the child's output, waiting for health, restarting after
 * a crash, sweeping orphans left by a previous run, and stopping deterministically.
 */

const { spawn, execFile } = require("child_process");
const crypto = require("crypto");
const fs = require("fs");
const http = require("http");
const net = require("net");
const os = require("os");
const path = require("path");

const HEALTH_POLL_MS = 300;
const STOP_GRACE_MS = 3000;
const MAX_RESTARTS = 3;
const LOG_TAIL_LINES = 60;

function freePort() {
  return new Promise((resolve, reject) => {
    const server = net.createServer();
    server.on("error", reject);
    server.listen(0, "127.0.0.1", () => {
      const { port } = server.address();
      server.close(() => resolve(port));
    });
  });
}

function httpJson(url, { timeoutMs = 2000, headers = {} } = {}) {
  return new Promise((resolve) => {
    const req = http.get(url, { headers, timeout: timeoutMs }, (res) => {
      let body = "";
      res.setEncoding("utf8");
      res.on("data", (chunk) => (body += chunk));
      res.on("end", () => {
        if (res.statusCode !== 200) return resolve(null);
        try {
          resolve(JSON.parse(body));
        } catch {
          resolve(null);
        }
      });
    });
    req.on("timeout", () => {
      req.destroy();
      resolve(null);
    });
    req.on("error", () => resolve(null));
  });
}

function httpPost(url, { timeoutMs = 2000, headers = {} } = {}) {
  return new Promise((resolve) => {
    const u = new URL(url);
    const req = http.request(
      { hostname: u.hostname, port: u.port, path: u.pathname, method: "POST", headers, timeout: timeoutMs },
      (res) => {
        res.resume();
        res.on("end", () => resolve(res.statusCode));
      },
    );
    req.on("timeout", () => {
      req.destroy();
      resolve(null);
    });
    req.on("error", () => resolve(null));
    req.end();
  });
}

function execFileAsync(file, args, opts = {}) {
  return new Promise((resolve) => {
    execFile(file, args, { timeout: 4000, windowsHide: true, ...opts }, (err, stdout, stderr) =>
      resolve({ err, stdout: String(stdout || ""), stderr: String(stderr || "") }),
    );
  });
}

class BackendStartupError extends Error {
  constructor(message, { code, hint, logTail } = {}) {
    super(message);
    this.name = "BackendStartupError";
    this.code = code || "backend_start_failed";
    this.hint = hint || null;
    this.logTail = logTail || [];
  }
}

class BackendSupervisor {
  /**
   * @param {object} options
   * @param {string} options.resourcesPath  where extraResources landed (packaged) or the repo root (dev)
   * @param {string} options.userDataPath   writable per-user folder
   * @param {boolean} options.isPackaged
   * @param {(line: string) => void} [options.onLog]
   * @param {(state: string, detail?: object) => void} [options.onState]
   */
  constructor({ resourcesPath, userDataPath, isPackaged, onLog, onState }) {
    this.resourcesPath = resourcesPath;
    this.userDataPath = userDataPath;
    this.isPackaged = isPackaged;
    this.onLog = onLog || (() => {});
    this.onState = onState || (() => {});

    this.token = crypto.randomUUID().replace(/-/g, "");
    this.port = null;
    this.child = null;
    this.command = null;
    this.state = "idle";
    this.restarts = 0;
    this.stopping = false;
    this.recentLog = [];

    this.logDir = path.join(userDataPath, "logs");
    this.logPath = path.join(this.logDir, "backend.log");
    this.pidPath = path.join(userDataPath, "backend.pid");
    fs.mkdirSync(this.logDir, { recursive: true });
    // Always use Electron userData for progress so desktop launches and
    // packaged installs share one DB (not the repo ./data copy used by plain uvicorn).
    this.dataDir = path.join(userDataPath, "data");
    fs.mkdirSync(this.dataDir, { recursive: true });
  }

  get baseUrl() {
    return this.port ? `http://127.0.0.1:${this.port}` : null;
  }

  get authHeaders() {
    return { "x-jtutor-token": this.token };
  }

  setState(state, detail) {
    this.state = state;
    this.onState(state, detail);
  }

  log(line) {
    const text = String(line).replace(/\s+$/, "");
    if (!text) return;
    this.recentLog.push(text);
    if (this.recentLog.length > LOG_TAIL_LINES * 4) {
      this.recentLog.splice(0, this.recentLog.length - LOG_TAIL_LINES * 4);
    }
    this.onLog(text);
    try {
      fs.appendFileSync(this.logPath, `${new Date().toISOString()} ${text}\n`);
    } catch {
      /* logging must never break startup */
    }
  }

  logTail(n = LOG_TAIL_LINES) {
    return this.recentLog.slice(-n);
  }

  // ---- backend resolution -------------------------------------------------

  frozenExecutable() {
    const name = process.platform === "win32" ? "jtutor-backend.exe" : "jtutor-backend";
    const candidates = [
      path.join(this.resourcesPath, "backend-dist", name),
      path.join(this.resourcesPath, "backend-dist", "jtutor-backend", name),
    ];
    return candidates.find((p) => fs.existsSync(p)) || null;
  }

  async pythonCandidates() {
    const explicit = process.env.JTUTOR_PYTHON;
    const names =
      process.platform === "win32" ? ["python", "python3", "py"] : ["python3", "python"];
    return explicit ? [explicit, ...names] : names;
  }

  async probePython(exe) {
    const args = exe === "py" ? ["-3", "-c", "import sys;print(sys.version_info[:2])"] : ["-c", "import sys;print(sys.version_info[:2])"];
    const { err, stdout } = await execFileAsync(exe, args);
    if (err) return null;
    const m = stdout.match(/\((\d+),\s*(\d+)\)/);
    if (!m) return null;
    const major = Number(m[1]);
    const minor = Number(m[2]);
    if (major < 3 || (major === 3 && minor < 11)) return null;
    return { exe, version: `${major}.${minor}` };
  }

  /** @returns {Promise<{file: string, args: string[], kind: string}>} */
  async resolveCommand(port) {
    const frozen = this.frozenExecutable();
    if (frozen) {
      return {
        kind: "frozen",
        file: frozen,
        args: ["--host", "127.0.0.1", "--port", String(port), "--root", this.resourcesPath, "--data-dir", this.dataDir],
      };
    }

    for (const exe of await this.pythonCandidates()) {
      const found = await this.probePython(exe);
      if (!found) continue;
      const prefix = exe === "py" ? ["-3"] : [];
      return {
        kind: `python:${found.version}`,
        file: exe,
        args: [
          ...prefix,
          "-m",
          "uvicorn",
          "backend.app.main:app",
          "--host",
          "127.0.0.1",
          "--port",
          String(port),
        ],
      };
    }

    throw new BackendStartupError("Jtutor could not find its backend.", {
      code: "backend_not_found",
      hint:
        "This build expects a bundled backend. If you are running from source, install Python 3.11+ " +
        "and `pip install -r backend/requirements.txt`, or set JTUTOR_PYTHON to an interpreter.",
    });
  }

  // ---- orphan handling ----------------------------------------------------

  async sweepOrphans() {
    let record;
    try {
      record = JSON.parse(fs.readFileSync(this.pidPath, "utf8"));
    } catch {
      return false;
    }
    if (!record || !record.pid || !record.port) {
      this.clearPidFile();
      return false;
    }

    // Only kill something that answers as a Jtutor backend on the recorded port.
    const health = await httpJson(`http://127.0.0.1:${record.port}/health`, { timeoutMs: 800 });
    const isOurs = health && health.app === "jtutor" && health.pid === record.pid;
    if (!isOurs) {
      this.clearPidFile();
      return false;
    }

    this.log(`sweeping orphaned backend pid=${record.pid} port=${record.port}`);
    await httpPost(`http://127.0.0.1:${record.port}/internal/shutdown`, {
      headers: record.token ? { "x-jtutor-token": record.token } : {},
      timeoutMs: 1500,
    });
    await new Promise((r) => setTimeout(r, 600));
    try {
      process.kill(record.pid, 0);
      await this.forceKill(record.pid);
    } catch {
      /* already gone */
    }
    this.clearPidFile();
    return true;
  }

  writePidFile() {
    try {
      fs.writeFileSync(
        this.pidPath,
        JSON.stringify({ pid: this.child.pid, port: this.port, token: this.token, startedAt: Date.now() }),
      );
    } catch {
      /* non-fatal */
    }
  }

  clearPidFile() {
    try {
      fs.unlinkSync(this.pidPath);
    } catch {
      /* non-fatal */
    }
  }

  async forceKill(pid) {
    if (process.platform === "win32") {
      await execFileAsync("taskkill", ["/pid", String(pid), "/T", "/F"]);
      return;
    }
    try {
      process.kill(pid, "SIGKILL");
    } catch {
      /* already gone */
    }
  }

  // ---- lifecycle ----------------------------------------------------------

  async start() {
    this.stopping = false;
    this.setState("starting");
    this.port = await freePort();
    this.command = await this.resolveCommand(this.port);
    this.log(`starting backend via ${this.command.kind}: ${this.command.file}`);

    const env = {
      ...process.env,
      JTUTOR_ROOT: this.resourcesPath,
      JTUTOR_DATA_DIR: this.dataDir,
      JTUTOR_TOKEN: this.token,
      PYTHONPATH: this.resourcesPath,
      PYTHONIOENCODING: "utf-8",
      PYTHONUNBUFFERED: "1",
    };

    let child;
    try {
      child = spawn(this.command.file, this.command.args, {
        cwd: this.resourcesPath,
        env,
        stdio: ["ignore", "pipe", "pipe"],
        windowsHide: true,
      });
    } catch (err) {
      throw new BackendStartupError(`Could not start the backend: ${err.message}`, {
        code: "backend_spawn_failed",
        logTail: this.logTail(),
      });
    }

    this.child = child;

    // A missing interpreter used to crash the main process with an unhandled
    // 'error' event and no window ever appeared.
    const spawnFailure = new Promise((_resolve, reject) => {
      child.once("error", (err) => {
        const missing = err && err.code === "ENOENT";
        reject(
          new BackendStartupError(
            missing
              ? `Jtutor could not launch its backend (${this.command.file} was not found).`
              : `Jtutor could not launch its backend: ${err.message}`,
            {
              code: missing ? "backend_not_found" : "backend_spawn_failed",
              hint: missing
                ? "Install Python 3.11+ and add it to PATH, or reinstall Jtutor so the bundled backend is present."
                : null,
              logTail: this.logTail(),
            },
          ),
        );
      });
    });

    child.stdout.setEncoding("utf8");
    child.stderr.setEncoding("utf8");
    child.stdout.on("data", (d) => d.split("\n").forEach((l) => this.log(l)));
    child.stderr.on("data", (d) => d.split("\n").forEach((l) => this.log(l)));

    child.on("exit", (code, signal) => {
      this.log(`backend exited code=${code} signal=${signal}`);
      this.child = null;
      this.clearPidFile();
      if (!this.stopping) this.handleUnexpectedExit(code);
    });

    this.writePidFile();
    return { spawnFailure };
  }

  async waitForHealth(timeoutMs = 60000, { spawnFailure } = {}) {
    const deadline = Date.now() + timeoutMs;
    const poll = (async () => {
      while (Date.now() < deadline) {
        if (!this.child && !this.stopping) {
          throw new BackendStartupError("The backend stopped while starting up.", {
            code: "backend_exited",
            hint: "Open the log to see why.",
            logTail: this.logTail(),
          });
        }
        const health = await httpJson(`${this.baseUrl}/health`, { timeoutMs: 1500 });
        if (health && health.ok) {
          this.setState("ready", { health });
          return health;
        }
        await new Promise((r) => setTimeout(r, HEALTH_POLL_MS));
      }
      throw new BackendStartupError("The backend did not become ready in time.", {
        code: "backend_timeout",
        hint: "This can happen on a slow first run. Try again, or open the log.",
        logTail: this.logTail(),
      });
    })();

    return spawnFailure ? Promise.race([poll, spawnFailure]) : poll;
  }

  async handleUnexpectedExit(code) {
    if (this.restarts >= MAX_RESTARTS) {
      this.setState("failed", { code, logTail: this.logTail() });
      return;
    }
    const delay = 1000 * 2 ** this.restarts;
    this.restarts += 1;
    this.setState("reconnecting", { attempt: this.restarts, delay });
    this.log(`restarting backend in ${delay}ms (attempt ${this.restarts}/${MAX_RESTARTS})`);
    await new Promise((r) => setTimeout(r, delay));
    if (this.stopping) return;
    try {
      const { spawnFailure } = await this.start();
      await this.waitForHealth(60000, { spawnFailure });
      this.setState("ready");
    } catch (err) {
      this.log(`restart failed: ${err.message}`);
      this.setState("failed", { code: err.code, logTail: this.logTail() });
    }
  }

  async stop() {
    this.stopping = true;
    const child = this.child;
    if (!child) {
      this.clearPidFile();
      return;
    }
    this.setState("stopping");

    await httpPost(`${this.baseUrl}/internal/shutdown`, {
      headers: this.authHeaders,
      timeoutMs: 1500,
    });

    const exited = new Promise((resolve) => child.once("exit", resolve));
    const timer = setTimeout(() => {
      try {
        child.kill("SIGTERM");
      } catch {
        /* already gone */
      }
    }, 400);
    const hardTimer = setTimeout(() => this.forceKill(child.pid), STOP_GRACE_MS);

    await Promise.race([exited, new Promise((r) => setTimeout(r, STOP_GRACE_MS + 1500))]);
    clearTimeout(timer);
    clearTimeout(hardTimer);

    if (child.exitCode === null && child.signalCode === null) {
      await this.forceKill(child.pid);
    }
    this.child = null;
    this.clearPidFile();
    this.setState("stopped");
  }

  diagnostics() {
    return {
      state: this.state,
      port: this.port,
      command: this.command ? `${this.command.file} ${this.command.args.join(" ")}` : null,
      kind: this.command ? this.command.kind : null,
      packaged: this.isPackaged,
      platform: `${process.platform} ${os.arch()}`,
      logPath: this.logPath,
      logTail: this.logTail(),
    };
  }
}

module.exports = { BackendSupervisor, BackendStartupError, freePort };
