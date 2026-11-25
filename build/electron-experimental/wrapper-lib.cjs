const path = require('node:path');

function serverOrigin(port) {
  return `http://127.0.0.1:${port}`;
}

function buildServerEnvironment(userData, port, launchNonce, apiToken, base = process.env) {
  const data = path.join(userData, 'data');
  return {
    ...base,
    COGNITO_DATA_DIR: data,
    COGNITO_DB_PATH: path.join(data, 'cognito.db'),
    MATERIALS_DIR: path.join(userData, 'materials'),
    PORT: String(port),
    COGNITO_LAUNCH_NONCE: launchNonce,
    COGNITO_API_TOKEN: apiToken,
    COGNITO_DESKTOP_WRAPPER: 'experimental',
  };
}

function isTrustedNavigation(url, origin) {
  try { return new URL(url).origin === origin; }
  catch { return false; }
}

function resolveServerBinary(resourcesPath) {
  return path.join(resourcesPath, 'server', process.platform === 'win32' ? 'cognito-server.exe' : 'cognito-server');
}

module.exports = { serverOrigin, buildServerEnvironment, isTrustedNavigation, resolveServerBinary };
