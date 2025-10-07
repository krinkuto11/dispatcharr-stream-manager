import axios from 'axios';

// Create axios instance with default config
// Use /api path since both frontend and backend are served from the same origin
const baseURL = '/api';

export const api = axios.create({
  baseURL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// API methods
export const automationAPI = {
  getStatus: () => api.get('/automation/status'),
  start: () => api.post('/automation/start'),
  stop: () => api.post('/automation/stop'),
  runCycle: () => api.post('/automation/cycle'),
  getConfig: () => api.get('/automation/config'),
  updateConfig: (config) => api.put('/automation/config', config),
};

export const channelsAPI = {
  getChannels: () => api.get('/channels'),
  getGroups: () => api.get('/channels/groups'),
};

export const regexAPI = {
  getPatterns: () => api.get('/regex-patterns'),
  addPattern: (pattern) => api.post('/regex-patterns', pattern),
  deletePattern: (channelId) => api.delete(`/regex-patterns/${channelId}`),
  testPattern: (data) => api.post('/test-regex', data),
  testPatternLive: (data) => api.post('/test-regex-live', data),
};

export const streamAPI = {
  discoverStreams: () => api.post('/discover-streams'),
  refreshPlaylist: (accountId) => api.post('/refresh-playlist', accountId ? { account_id: accountId } : {}),
};

export const m3uAPI = {
  getAccounts: () => api.get('/m3u-accounts'),
};

export const streamCheckerAPI = {
  getStatus: () => api.get('/stream-checker/status'),
  start: () => api.post('/stream-checker/start'),
  stop: () => api.post('/stream-checker/stop'),
  getQueue: () => api.get('/stream-checker/queue'),
  addToQueue: (data) => api.post('/stream-checker/queue/add', data),
  clearQueue: () => api.post('/stream-checker/queue/clear'),
  getConfig: () => api.get('/stream-checker/config'),
  updateConfig: (config) => api.put('/stream-checker/config', config),
  getProgress: () => api.get('/stream-checker/progress'),
  checkChannel: (channelId) => api.post('/stream-checker/check-channel', { channel_id: channelId }),
  markUpdated: (data) => api.post('/stream-checker/mark-updated', data),
  queueAllChannels: () => api.post('/stream-checker/queue-all'),
};

export const changelogAPI = {
  getChangelog: (days = 7) => api.get(`/changelog?days=${days}`),
};

export const setupAPI = {
  getStatus: () => api.get('/setup-wizard'),
};

export const dispatcharrAPI = {
  getConfig: () => api.get('/dispatcharr/config'),
  updateConfig: (config) => api.put('/dispatcharr/config', config),
  testConnection: (config) => api.post('/dispatcharr/test-connection', config),
};