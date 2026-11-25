const { app, BrowserWindow, dialog, shell } = require('electron');
const { spawn } = require('node:child_process');
const crypto = require('node:crypto');
const fs = require('node:fs');
const http = require('node:http');
const net = require('node:net');
const path = require('node:path');
const { serverOrigin, buildServerEnvironment, isTrustedNavigation, resolveServerBinary } = require('./wrapper-lib.cjs');

let serverProcess = null;
let mainWindow = null;
let origin = null;
let launchNonce = null;
let apiToken = null;

function serverBinary() {
  if (app.isPackaged) return resolveServerBinary(process.resourcesPath);
  return path.join(__dirname, 'server-dist', 'cognito-server');
}

function reservePort() {
  return new Promise((resolve, reject) => {
    const socket = net.createServer();
    socket.unref();
    socket.on('error', reject);
    socket.listen(0, '127.0.0.1', () => {
      const address = socket.address();
      socket.close(error => error ? reject(error) : resolve(address.port));
    });
  });
}

function startServer(port) {
  const binary = serverBinary();
  if (!fs.existsSync(binary)) throw new Error(`Bundled Cognito server not found: ${binary}. Run npm run build:server.`);
  serverProcess = spawn(binary, [], {
    env: buildServerEnvironment(app.getPath('userData'), port, launchNonce, apiToken),
    stdio: ['ignore', 'pipe', 'pipe'],
    windowsHide: true,
  });
  serverProcess.stdout.on('data', data => process.stdout.write(`[cognito-server] ${data}`));
  serverProcess.stderr.on('data', data => process.stderr.write(`[cognito-server] ${data}`));
  serverProcess.on('exit', code => { if (code && !app.isQuitting) dialog.showErrorBox('Cognito server stopped', `The local server exited with code ${code}.`); });
}

function waitForServer(timeoutMs = 20000) {
  const started = Date.now();
  return new Promise((resolve, reject) => {
    const retry = () => Date.now() - started >= timeoutMs ? reject(new Error('Local Cognito server did not become ready.')) : setTimeout(attempt, 200);
    const attempt = () => {
      const request = http.get(`${origin}/api/health`, { headers: { 'X-Cognito-Token': apiToken } }, response => {
        let body = '';
        response.setEncoding('utf8');
        response.on('data', chunk => { body += chunk; });
        response.on('end', () => {
          try {
            const health = JSON.parse(body);
            if (response.statusCode === 200 && health.launch_nonce === launchNonce) resolve();
            else retry();
          } catch { retry(); }
        });
      });
      request.on('error', retry);
      request.setTimeout(800, () => request.destroy());
    };
    attempt();
  });
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1440,
    height: 920,
    minWidth: 960,
    minHeight: 640,
    backgroundColor: '#0d0e11',
    show: false,
    title: 'Cognito Experimental',
    webPreferences: {
      preload: path.join(__dirname, 'preload.cjs'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
      webSecurity: true,
    },
  });
  mainWindow.removeMenu();
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    if (url.startsWith('https://')) shell.openExternal(url);
    return { action: 'deny' };
  });
  mainWindow.webContents.on('will-navigate', (event, url) => { if (!isTrustedNavigation(url, origin)) event.preventDefault(); });
  mainWindow.once('ready-to-show', () => mainWindow.show());
  mainWindow.loadURL(origin);
}

app.whenReady().then(async () => {
  try {
    const port = await reservePort();
    origin = serverOrigin(port);
    launchNonce = crypto.randomBytes(32).toString('hex');
    apiToken = crypto.randomBytes(32).toString('hex');
    startServer(port);
    await waitForServer();
    createWindow();
  } catch (error) {
    dialog.showErrorBox('Cognito Experimental failed to start', error.message);
    app.quit();
  }
});

app.on('window-all-closed', () => app.quit());
app.on('before-quit', () => {
  app.isQuitting = true;
  if (serverProcess && !serverProcess.killed) serverProcess.kill('SIGTERM');
});
