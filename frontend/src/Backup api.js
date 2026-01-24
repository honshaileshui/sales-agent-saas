// api.js - Updated with Dashboard API
// Week 6 Day 5-6

import axios from 'axios';

const API_BASE = 'http://localhost:8000';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// ============================================================================
// AUTH API
// ============================================================================
export const authAPI = {
  login: (email, password) => api.post('/auth/login', { email, password }),
  register: (data) => api.post('/auth/register', data),
  me: () => api.get('/auth/me')
};

// ============================================================================
// LEADS API
// ============================================================================
export const leadsAPI = {
  getAll: (params) => api.get('/leads', { params }),
  getById: (id) => api.get(`/leads/${id}`),
  create: (data) => api.post('/leads', data),
  update: (id, data) => api.put(`/leads/${id}`, data),
  delete: (id) => api.delete(`/leads/${id}`),
  bulkDelete: (ids) => api.post('/leads/bulk-delete', { lead_ids: ids }),
  importCSV: (formData) => api.post('/leads/import', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  research: (id) => api.post(`/leads/${id}/research`),
  getResearch: (id) => api.get(`/leads/${id}/research`),
  generateEmail: (id) => api.post(`/leads/${id}/generate-email`),
  process: (id) => api.post(`/leads/${id}/process`)
};

// ============================================================================
// EMAILS API
// ============================================================================
export const emailsAPI = {
  getAll: (params) => api.get('/emails', { params }),
  getById: (id) => api.get(`/emails/${id}`),
  update: (id, data) => api.put(`/emails/${id}`, data),
  delete: (id) => api.delete(`/emails/${id}`),
  generate: (data) => api.post('/emails/generate', data),
  regenerate: (id, params) => api.post(`/emails/${id}/regenerate`, null, { params }),
  approve: (id) => api.post(`/emails/${id}/approve`),
  send: (id) => api.post(`/emails/${id}/send`),
  bulkSend: (ids) => api.post('/emails/send/bulk', { email_ids: ids }),
  bulkApprove: (ids) => api.post('/emails/approve/bulk', { email_ids: ids }),
  testSend: (email) => api.post(`/emails/test-send?to_email=${email}`),
  getVersions: (id) => api.get(`/emails/${id}/versions`),
  getStats: () => api.get('/emails/stats/summary')
};

// ============================================================================
// CAMPAIGNS API
// ============================================================================
export const campaignsAPI = {
  getAll: (params) => api.get('/campaigns', { params }),
  getById: (id) => api.get(`/campaigns/${id}`),
  create: (data) => api.post('/campaigns', data),
  update: (id, data) => api.put(`/campaigns/${id}`, data),
  delete: (id) => api.delete(`/campaigns/${id}`),
  addLeads: (id, leadIds) => api.post(`/campaigns/${id}/leads`, { lead_ids: leadIds }),
  removeLeads: (id, leadIds) => api.delete(`/campaigns/${id}/leads`, { data: { lead_ids: leadIds } }),
  start: (id) => api.post(`/campaigns/${id}/start`),
  pause: (id) => api.post(`/campaigns/${id}/pause`),
  getStats: (id) => api.get(`/campaigns/${id}/stats`)
};

// ============================================================================
// DASHBOARD API (NEW - Week 6)
// ============================================================================
export const dashboardAPI = {
  getStats: () => api.get('/dashboard/stats'),
  getRecent: (limit = 10) => api.get('/dashboard/recent', { params: { limit } }),
  getPerformance: (days = 7) => api.get('/dashboard/performance', { params: { days } }),
  getTopPerformers: (limit = 5) => api.get('/dashboard/top-performers', { params: { limit } }),
  getFunnel: () => api.get('/dashboard/lead-funnel')
};

// ============================================================================
// WEBHOOKS API
// ============================================================================
export const webhooksAPI = {
  getEmailStats: (emailId) => api.get(`/webhooks/stats/email/${emailId}`),
  getSummary: () => api.get('/webhooks/stats/summary')
};

// ============================================================================
// ANALYTICS API
// ============================================================================
export const analyticsAPI = {
  getOverview: () => api.get('/analytics/overview'),
  getEmailStats: (params) => api.get('/analytics/emails', { params }),
  getLeadStats: (params) => api.get('/analytics/leads', { params })
};

// ============================================================================
// LEGACY DASHBOARD FUNCTIONS (for existing Dashboard.jsx)
// ============================================================================

// Dashboard functions for existing Dashboard.jsx
api.getDashboardStats = async () => {
  try {
    const response = await api.get('/api/dashboard/stats');
    return {
      stats: {
        total_leads: response.data?.leads?.total || 0,
        total_emails_sent: response.data?.emails?.sent || 0,
        open_rate: response.data?.rates?.open_rate || 0,
        click_rate: response.data?.rates?.click_rate || 0,
        total_opened: response.data?.emails?.opened || 0,
        total_clicked: response.data?.emails?.clicked || 0,
        recent_activity: {
          new_leads_last_7_days: response.data?.leads?.new || 0,
          emails_sent_last_7_days: response.data?.emails?.sent || 0
        }
      }
    };
  } catch (err) {
    console.error('Dashboard stats error:', err);
    return { stats: null };
  }
};

api.getRecentLeads = async (limit = 5) => {
  try {
    const response = await api.get('/api/leads', { params: { limit } });
    return { leads: response.data?.leads || [] };
  } catch (err) {
    console.error('Recent leads error:', err);
    return { leads: [] };
  }
};

api.getEmailPerformance = async () => {
  try {
    const response = await api.get('/api/dashboard/performance', { params: { days: 30 } });
    return { performance: response.data?.performance || [] };
  } catch (err) {
    console.error('Email performance error:', err);
    return { performance: [] };
  }
};

export default api;