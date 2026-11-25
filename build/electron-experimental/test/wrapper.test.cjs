const test = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');
const { buildServerEnvironment, isTrustedNavigation, resolveServerBinary } = require('../wrapper-lib.cjs');

test('server environment uses isolated writable user data and launch secrets', () => {
  const root = '/tmp/cognito-user';
  const env = buildServerEnvironment(root, 43123, 'health-nonce', 'api-token', { HOME: '/home/test' });
  assert.equal(env.COGNITO_DATA_DIR, path.join(root, 'data'));
  assert.equal(env.MATERIALS_DIR, path.join(root, 'materials'));
  assert.equal(env.COGNITO_DB_PATH, path.join(root, 'data', 'cognito.db'));
  assert.equal(env.PORT, '43123');
  assert.equal(env.COGNITO_LAUNCH_NONCE, 'health-nonce');
  assert.equal(env.COGNITO_API_TOKEN, 'api-token');
});

test('navigation only trusts the selected loopback Cognito origin', () => {
  const origin = 'http://127.0.0.1:43123';
  assert.equal(isTrustedNavigation(`${origin}/`, origin), true);
  assert.equal(isTrustedNavigation('http://127.0.0.1:18765/', origin), false);
  assert.equal(isTrustedNavigation('http://localhost:43123/', origin), false);
  assert.equal(isTrustedNavigation('https://example.com', origin), false);
});

test('server binary resolves inside packaged resources', () => {
  assert.equal(resolveServerBinary('/opt/resources'), path.join('/opt/resources', 'server', 'cognito-server'));
});
