const { contextBridge } = require('electron');

contextBridge.exposeInMainWorld('cognitoDesktop', Object.freeze({
  experimental: true,
  platform: process.platform,
}));
