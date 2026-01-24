// Dashboard.jsx - FRESH BUILD with Inline Styles
// Version: 3.1 - Works without Tailwind dependency issues

import React, { useState, useEffect } from 'react';
import api from '../api';

const Dashboard = () => {
  const [stats, setStats] = useState(null);
  const [recentLeads, setRecentLeads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const statsResponse = await api.getDashboardStats();
      if (statsResponse && statsResponse.stats) {
        setStats(statsResponse.stats);
      }
      
      const leadsResponse = await api.getRecentLeads(5);
      if (leadsResponse && leadsResponse.leads) {
        setRecentLeads(leadsResponse.leads);
      }
    } catch (err) {
      console.error('Dashboard error:', err);
      setError(err.message || 'Failed to load dashboard');
    } finally {
      setLoading(false);
    }
  };

  // Styles
  const styles = {
    container: {
      minHeight: '100vh',
      backgroundColor: '#f9fafb',
      padding: '24px'
    },
    maxWidth: {
      maxWidth: '1280px',
      margin: '0 auto'
    },
    header: {
      marginBottom: '32px',
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center'
    },
    title: {
      fontSize: '2.5rem',
      fontWeight: 'bold',
      color: '#111827',
      marginBottom: '8px'
    },
    subtitle: {
      color: '#6b7280'
    },
    refreshBtn: {
      padding: '10px 20px',
      backgroundColor: '#2563eb',
      color: 'white',
      border: 'none',
      borderRadius: '8px',
      cursor: 'pointer',
      fontWeight: '600'
    },
    statsGrid: {
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
      gap: '24px',
      marginBottom: '32px'
    },
    statCard: (gradient) => ({
      background: gradient,
      borderRadius: '16px',
      padding: '24px',
      color: 'white',
      boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)'
    }),
    statHeader: {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      marginBottom: '12px'
    },
    statLabel: {
      fontSize: '14px',
      opacity: 0.9,
      fontWeight: '500'
    },
    statIcon: {
      fontSize: '2.5rem'
    },
    statValue: {
      fontSize: '2.5rem',
      fontWeight: 'bold'
    },
    statSubtext: {
      fontSize: '14px',
      opacity: 0.8,
      marginTop: '8px'
    },
    twoColumn: {
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))',
      gap: '24px',
      marginBottom: '32px'
    },
    card: {
      backgroundColor: 'white',
      borderRadius: '16px',
      padding: '24px',
      boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
    },
    cardTitle: {
      fontSize: '1.5rem',
      fontWeight: 'bold',
      color: '#111827',
      marginBottom: '16px'
    },
    activityItem: (bgColor) => ({
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      padding: '16px',
      backgroundColor: bgColor,
      borderRadius: '12px',
      marginBottom: '12px'
    }),
    activityLabel: {
      display: 'flex',
      alignItems: 'center',
      gap: '12px'
    },
    activityIcon: {
      fontSize: '1.5rem'
    },
    activityText: {
      fontWeight: '500',
      color: '#374151'
    },
    activityValue: (color) => ({
      fontSize: '1.5rem',
      fontWeight: 'bold',
      color: color
    }),
    leadItem: {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      padding: '12px',
      border: '2px solid #e5e7eb',
      borderRadius: '12px',
      marginBottom: '12px',
      cursor: 'pointer',
      transition: 'all 0.2s'
    },
    leadName: {
      fontWeight: '600',
      color: '#111827'
    },
    leadEmail: {
      fontSize: '14px',
      color: '#6b7280'
    },
    statusBadge: (status) => {
      const colors = {
        new: { bg: '#f3f4f6', text: '#374151' },
        contacted: { bg: '#fef3c7', text: '#92400e' },
        engaged: { bg: '#dbeafe', text: '#1e40af' },
        converted: { bg: '#d1fae5', text: '#065f46' },
        email_drafted: { bg: '#e0e7ff', text: '#3730a3' }
      };
      const color = colors[status] || colors.new;
      return {
        padding: '4px 12px',
        fontSize: '12px',
        fontWeight: '600',
        borderRadius: '9999px',
        backgroundColor: color.bg,
        color: color.text
      };
    },
    quickActions: {
      background: 'linear-gradient(to right, #2563eb, #4f46e5)',
      borderRadius: '16px',
      padding: '32px',
      boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)'
    },
    quickActionsTitle: {
      fontSize: '1.5rem',
      fontWeight: 'bold',
      color: 'white',
      marginBottom: '24px'
    },
    quickActionsGrid: {
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
      gap: '16px'
    },
    quickActionBtn: {
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      gap: '12px',
      backgroundColor: 'white',
      color: '#2563eb',
      padding: '16px 24px',
      borderRadius: '12px',
      fontWeight: '600',
      textDecoration: 'none',
      transition: 'all 0.2s'
    },
    loadingContainer: {
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: '100vh',
      backgroundColor: '#f9fafb'
    },
    spinner: {
      width: '64px',
      height: '64px',
      border: '4px solid #e5e7eb',
      borderTop: '4px solid #2563eb',
      borderRadius: '50%',
      animation: 'spin 1s linear infinite'
    },
    errorContainer: {
      minHeight: '100vh',
      backgroundColor: '#f9fafb',
      padding: '24px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center'
    },
    errorCard: {
      backgroundColor: '#fef2f2',
      border: '2px solid #fecaca',
      borderRadius: '12px',
      padding: '32px',
      textAlign: 'center',
      maxWidth: '500px'
    },
    errorIcon: {
      fontSize: '4rem',
      color: '#dc2626',
      marginBottom: '16px'
    },
    errorTitle: {
      fontSize: '1.25rem',
      fontWeight: 'bold',
      color: '#991b1b',
      marginBottom: '8px'
    },
    errorMessage: {
      color: '#dc2626',
      marginBottom: '16px'
    },
    errorBtn: {
      padding: '10px 24px',
      backgroundColor: '#dc2626',
      color: 'white',
      border: 'none',
      borderRadius: '8px',
      cursor: 'pointer',
      fontWeight: '600'
    }
  };

  if (loading) {
    return (
      <div style={styles.loadingContainer}>
        <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
        <div style={styles.spinner}></div>
        <p style={{ marginTop: '16px', color: '#6b7280', fontSize: '18px' }}>Loading dashboard...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div style={styles.errorContainer}>
        <div style={styles.errorCard}>
          <div style={styles.errorIcon}>⚠️</div>
          <h2 style={styles.errorTitle}>Error Loading Dashboard</h2>
          <p style={styles.errorMessage}>{error}</p>
          <button onClick={loadDashboardData} style={styles.errorBtn}>
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div style={styles.container}>
      <div style={styles.maxWidth}>
        {/* Header */}
        <div style={styles.header}>
          <div>
            <h1 style={styles.title}>Dashboard</h1>
            <p style={styles.subtitle}>Welcome to SalesAgent AI</p>
          </div>
          <button onClick={loadDashboardData} style={styles.refreshBtn}>
            🔄 Refresh
          </button>
        </div>

        {/* Stats Cards */}
        <div style={styles.statsGrid}>
          <div style={styles.statCard('linear-gradient(135deg, #3b82f6, #2563eb)')}>
            <div style={styles.statHeader}>
              <span style={styles.statLabel}>Total Leads</span>
              <span style={styles.statIcon}>👥</span>
            </div>
            <div style={styles.statValue}>{stats?.total_leads || 0}</div>
            <div style={styles.statSubtext}>In database</div>
          </div>

          <div style={styles.statCard('linear-gradient(135deg, #22c55e, #16a34a)')}>
            <div style={styles.statHeader}>
              <span style={styles.statLabel}>Emails Sent</span>
              <span style={styles.statIcon}>📧</span>
            </div>
            <div style={styles.statValue}>{stats?.total_emails_sent || 0}</div>
            <div style={styles.statSubtext}>Total emails</div>
          </div>

          <div style={styles.statCard('linear-gradient(135deg, #a855f7, #9333ea)')}>
            <div style={styles.statHeader}>
              <span style={styles.statLabel}>Open Rate</span>
              <span style={styles.statIcon}>📬</span>
            </div>
            <div style={styles.statValue}>{stats?.open_rate || 0}%</div>
            <div style={styles.statSubtext}>{stats?.total_opened || 0} opened</div>
          </div>

          <div style={styles.statCard('linear-gradient(135deg, #f97316, #ea580c)')}>
            <div style={styles.statHeader}>
              <span style={styles.statLabel}>Click Rate</span>
              <span style={styles.statIcon}>🖱️</span>
            </div>
            <div style={styles.statValue}>{stats?.click_rate || 0}%</div>
            <div style={styles.statSubtext}>{stats?.total_clicked || 0} clicked</div>
          </div>
        </div>

        {/* Two Column Layout */}
        <div style={styles.twoColumn}>
          {/* Recent Activity */}
          <div style={styles.card}>
            <h2 style={styles.cardTitle}>📊 Recent Activity (7 days)</h2>
            <div style={styles.activityItem('#dbeafe')}>
              <div style={styles.activityLabel}>
                <span style={styles.activityIcon}>📈</span>
                <span style={styles.activityText}>New Leads</span>
              </div>
              <span style={styles.activityValue('#2563eb')}>
                {stats?.recent_activity?.new_leads_last_7_days || 0}
              </span>
            </div>
            <div style={styles.activityItem('#d1fae5')}>
              <div style={styles.activityLabel}>
                <span style={styles.activityIcon}>✉️</span>
                <span style={styles.activityText}>Emails Sent</span>
              </div>
              <span style={styles.activityValue('#16a34a')}>
                {stats?.recent_activity?.emails_sent_last_7_days || 0}
              </span>
            </div>
          </div>

          {/* Recent Leads */}
          <div style={styles.card}>
            <h2 style={styles.cardTitle}>👥 Recent Leads</h2>
            {recentLeads.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '48px 0' }}>
                <p style={{ color: '#6b7280', marginBottom: '16px' }}>No leads yet</p>
                <a href="/leads" style={{ ...styles.refreshBtn, textDecoration: 'none' }}>
                  Import Your First Leads
                </a>
              </div>
            ) : (
              recentLeads.slice(0, 5).map((lead) => (
                <div 
                  key={lead.id} 
                  style={styles.leadItem}
                  onClick={() => window.location.href = `/leads/${lead.id}`}
                  onMouseOver={(e) => {
                    e.currentTarget.style.borderColor = '#93c5fd';
                    e.currentTarget.style.backgroundColor = '#eff6ff';
                  }}
                  onMouseOut={(e) => {
                    e.currentTarget.style.borderColor = '#e5e7eb';
                    e.currentTarget.style.backgroundColor = 'white';
                  }}
                >
                  <div>
                    <p style={styles.leadName}>{lead.company || lead.name}</p>
                    <p style={styles.leadEmail}>{lead.name || lead.email}</p>
                  </div>
                  <span style={styles.statusBadge(lead.status)}>
                    {lead.status || 'new'}
                  </span>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Quick Actions */}
        <div style={styles.quickActions}>
          <h2 style={styles.quickActionsTitle}>🚀 Quick Actions</h2>
          <div style={styles.quickActionsGrid}>
            <a href="/leads" style={styles.quickActionBtn}>
              <span>📋</span>
              <span>View All Leads</span>
            </a>
            <a href="/emails" style={styles.quickActionBtn}>
              <span>📧</span>
              <span>View Emails</span>
            </a>
            <a href="/campaigns" style={styles.quickActionBtn}>
              <span>🎯</span>
              <span>Campaigns</span>
            </a>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
