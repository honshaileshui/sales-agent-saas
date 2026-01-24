// api.js - FRESH BUILD
// Clean API connector for SalesAgent AI
// Version: 3.0

import axios from 'axios';

// API Base URL - NO /api suffix, we add it per endpoint
const API_BASE = 'http://localhost:8000';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json'
  },
  timeout: 10000
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle responses and errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.status, error.response?.data);
    
    // Only redirect to login for 401 errors on protected routes
    if (error.response?.status === 401) {
      const isAuthRoute = error.config?.url?.includes('/auth/');
      if (!isAuthRoute) {
        localStorage.removeItem('token');
        // Don't auto-redirect, let the component handle it
      }
    }
    return Promise.reject(error);
  }
);

// ============================================================================
// AUTH API
// ============================================================================
export const authAPI = {
  login: async (email, password) => {
    const response = await api.post('/auth/login', { email, password });
    if (response.data.access_token) {
      localStorage.setItem('token', response.data.access_token);
    }
    return response;
  },
  register: (data) => api.post('/auth/register', data),
  me: () => api.get('/auth/me'),
  logout: () => {
    localStorage.removeItem('token');
  }
};

// ============================================================================
// LEADS API
// ============================================================================
export const leadsAPI = {
  getAll: (params) => api.get('/api/leads', { params }),
  getById: (id) => api.get(`/api/leads/${id}`),
  create: (data) => api.post('/api/leads', data),
  update: (id, data) => api.put(`/api/leads/${id}`, data),
  delete: (id) => api.delete(`/api/leads/${id}`),
  bulkDelete: (ids) => api.post('/api/leads/bulk-delete', { lead_ids: ids }),
  importCSV: (formData) => api.post('/api/leads/import', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  research: (id) => api.post(`/api/leads/${id}/research`),
  getResearch: (id) => api.get(`/api/leads/${id}/research`),
  generateEmail: (id) => api.post(`/api/leads/${id}/generate-email`),
  process: (id) => api.post(`/api/leads/${id}/process`)
};

// ============================================================================
// EMAILS API
// ============================================================================
export const emailsAPI = {
  getAll: (params) => api.get('/api/emails', { params }),
  getById: (id) => api.get(`/api/emails/${id}`),
  update: (id, data) => api.put(`/api/emails/${id}`, data),
  delete: (id) => api.delete(`/api/emails/${id}`),
  approve: (id) => api.post(`/api/emails/${id}/approve`),
  send: (id) => api.post(`/api/emails/${id}/send`),
  bulkSend: (ids) => api.post('/api/emails/send/bulk', { email_ids: ids }),
  testSend: (email) => api.post(`/api/emails/test-send?to_email=${email}`),
  
  // MISSING FUNCTIONS - ADD THESE:
  generate: (data) => api.post('/api/emails/generate', data),
  generateBulk: async (leadIds, campaignId = null, template = 'default') => {
    const results = [];
    for (const leadId of leadIds) {
      try {
        const response = await api.post('/api/emails/generate', {
          lead_id: leadId,
          campaign_id: campaignId,
          template: template
        });
        results.push(response.data);
      } catch (err) {
        console.error(`Failed to generate email for lead ${leadId}:`, err);
      }
    }
    return results;
  },
  regenerate: (id, params) => api.post(`/api/emails/${id}/regenerate`, null, { params }),
  approveBulk: (ids) => api.post('/api/emails/approve/bulk', { email_ids: ids }),
};

// ============================================================================
// CAMPAIGNS API
// ============================================================================
export const campaignsAPI = {
  getAll: (params) => api.get('/api/campaigns', { params }),
  getById: (id) => api.get(`/api/campaigns/${id}`),
  create: (data) => api.post('/api/campaigns', data),
  update: (id, data) => api.put(`/api/campaigns/${id}`, data),
  delete: (id) => api.delete(`/api/campaigns/${id}`),
  start: (id) => api.post(`/api/campaigns/${id}/start`),
  pause: (id) => api.post(`/api/campaigns/${id}/pause`)
};

// ============================================================================
// DASHBOARD API - Direct endpoint calls
// ============================================================================
export const dashboardAPI = {
  getStats: () => api.get('/api/dashboard/stats'),
  getRecent: (limit = 10) => api.get('/api/dashboard/recent', { params: { limit } }),
  getPerformance: (days = 30) => api.get('/api/dashboard/performance', { params: { days } }),
  getFunnel: () => api.get('/api/dashboard/lead-funnel')
};

// ============================================================================
// LEGACY FUNCTIONS - For existing Dashboard.jsx compatibility
// ============================================================================

// This function transforms the API response to match what Dashboard.jsx expects
api.getDashboardStats = async () => {
  try {
    const response = await api.get('/api/dashboard/stats');
    const data = response.data;
    
    // Return in the format Dashboard.jsx expects
    return {
      stats: data.stats || {
        total_leads: data.leads?.total || 0,
        total_emails_sent: data.emails?.sent || 0,
        open_rate: data.rates?.open_rate || 0,
        click_rate: data.rates?.click_rate || 0,
        total_opened: data.emails?.opened || 0,
        total_clicked: data.emails?.clicked || 0,
        recent_activity: data.stats?.recent_activity || {
          new_leads_last_7_days: 0,
          emails_sent_last_7_days: 0
        }
      }
    };
  } catch (err) {
    console.error('getDashboardStats error:', err);
    return {
      stats: {
        total_leads: 0,
        total_emails_sent: 0,
        open_rate: 0,
        click_rate: 0,
        total_opened: 0,
        total_clicked: 0,
        recent_activity: {
          new_leads_last_7_days: 0,
          emails_sent_last_7_days: 0
        }
      }
    };
  }
};

api.getRecentLeads = async (limit = 5) => {
  try {
    const response = await api.get('/api/leads', { params: { limit } });
    return { 
      leads: response.data?.leads || response.data || [] 
    };
  } catch (err) {
    console.error('getRecentLeads error:', err);
    return { leads: [] };
  }
};

api.getEmailPerformance = async () => {
  try {
    const response = await api.get('/api/dashboard/performance', { params: { days: 30 } });
    return { 
      performance: response.data?.performance || [] 
    };
  } catch (err) {
    console.error('getEmailPerformance error:', err);
    return { performance: [] };
  }
};

// ============================================================================
// EXPORT
// ============================================================================
export default api;