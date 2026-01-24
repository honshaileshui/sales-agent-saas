// Analytics.jsx - FRESH BUILD with Inline Styles
// Version: 3.0

import React, { useState, useEffect } from 'react';
import api from '../api';

const Analytics = () => {
  const [stats, setStats] = useState(null);
  const [performance, setPerformance] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadAnalytics();
  }, []);

  const loadAnalytics = async () => {
    try {
      setLoading(true);
      setError(null);

      const [statsResponse, performanceResponse] = await Promise.all([
        api.getDashboardStats(),
        api.getEmailPerformance()
      ]);

      if (statsResponse && statsResponse.stats) {
        setStats(statsResponse.stats);
      }

      if (performanceResponse && performanceResponse.performance) {
        setPerformance(performanceResponse.performance);
      }
    } catch (err) {
      setError(err.message);
      console.error('Error loading analytics:', err);
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
      marginBottom: '32px'
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
    statsGrid: {
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
      gap: '24px',
      marginBottom: '32px'
    },
    statCard: (borderColor) => ({
      backgroundColor: 'white',
      borderRadius: '16px',
      padding: '24px',
      boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
      borderLeft: `4px solid ${borderColor}`
    }),
    statHeader: {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      marginBottom: '8px'
    },
    statLabel: {
      color: '#6b7280',
      fontWeight: '500'
    },
    statIcon: {
      fontSize: '2rem'
    },
    statValue: {
      fontSize: '2rem',
      fontWeight: 'bold',
      color: '#111827'
    },
    statSubtext: {
      fontSize: '14px',
      color: '#9ca3af',
      marginTop: '4px'
    },
    card: {
      backgroundColor: 'white',
      borderRadius: '16px',
      padding: '24px',
      boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
      marginBottom: '24px'
    },
    cardTitle: {
      fontSize: '1.5rem',
      fontWeight: 'bold',
      color: '#111827',
      marginBottom: '24px'
    },
    engagementGrid: {
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
      gap: '24px'
    },
    engagementItem: (bgColor) => ({
      textAlign: 'center',
      padding: '24px',
      backgroundColor: bgColor,
      borderRadius: '12px'
    }),
    engagementIcon: {
      fontSize: '3rem',
      marginBottom: '12px'
    },
    engagementLabel: {
      fontSize: '14px',
      color: '#6b7280',
      marginBottom: '4px'
    },
    engagementValue: (color) => ({
      fontSize: '2rem',
      fontWeight: 'bold',
      color: color
    }),
    engagementSubtext: {
      fontSize: '12px',
      color: '#9ca3af',
      marginTop: '4px'
    },
    table: {
      width: '100%',
      borderCollapse: 'collapse'
    },
    th: {
      padding: '12px 16px',
      textAlign: 'left',
      fontSize: '14px',
      fontWeight: '600',
      color: '#6b7280',
      borderBottom: '2px solid #e5e7eb'
    },
    thCenter: {
      padding: '12px 16px',
      textAlign: 'center',
      fontSize: '14px',
      fontWeight: '600',
      color: '#6b7280',
      borderBottom: '2px solid #e5e7eb'
    },
    td: {
      padding: '12px 16px',
      fontSize: '14px',
      color: '#111827',
      borderBottom: '1px solid #f3f4f6'
    },
    tdCenter: {
      padding: '12px 16px',
      fontSize: '14px',
      textAlign: 'center',
      borderBottom: '1px solid #f3f4f6'
    },
    badge: (type) => {
      const colors = {
        good: { bg: '#d1fae5', text: '#065f46' },
        medium: { bg: '#fef3c7', text: '#92400e' },
        bad: { bg: '#fee2e2', text: '#991b1b' }
      };
      const color = colors[type] || colors.medium;
      return {
        padding: '4px 12px',
        fontSize: '12px',
        fontWeight: '600',
        borderRadius: '9999px',
        backgroundColor: color.bg,
        color: color.text
      };
    },
    emptyState: {
      textAlign: 'center',
      padding: '48px',
      color: '#6b7280'
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
        <p style={{ marginTop: '16px', color: '#6b7280', fontSize: '18px' }}>Loading analytics...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div style={styles.errorContainer}>
        <div style={styles.errorCard}>
          <div style={{ fontSize: '4rem', marginBottom: '16px' }}>⚠️</div>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 'bold', color: '#991b1b', marginBottom: '8px' }}>
            Error Loading Analytics
          </h2>
          <p style={{ color: '#dc2626', marginBottom: '16px' }}>{error}</p>
          <button onClick={loadAnalytics} style={styles.errorBtn}>
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
          <h1 style={styles.title}>Analytics</h1>
          <p style={styles.subtitle}>Email performance overview</p>
        </div>

        {/* Overview Stats */}
        <div style={styles.statsGrid}>
          <div style={styles.statCard('#3b82f6')}>
            <div style={styles.statHeader}>
              <span style={styles.statLabel}>Emails Sent</span>
              <span style={styles.statIcon}>📨</span>
            </div>
            <div style={styles.statValue}>{stats?.total_emails_sent || 0}</div>
            <div style={styles.statSubtext}>Total emails</div>
          </div>

          <div style={styles.statCard('#22c55e')}>
            <div style={styles.statHeader}>
              <span style={styles.statLabel}>Open Rate</span>
              <span style={styles.statIcon}>👀</span>
            </div>
            <div style={styles.statValue}>{stats?.open_rate || 0}%</div>
            <div style={styles.statSubtext}>{stats?.total_opened || 0} opened</div>
          </div>

          <div style={styles.statCard('#a855f7')}>
            <div style={styles.statHeader}>
              <span style={styles.statLabel}>Click Rate</span>
              <span style={styles.statIcon}>🖱️</span>
            </div>
            <div style={styles.statValue}>{stats?.click_rate || 0}%</div>
            <div style={styles.statSubtext}>{stats?.total_clicked || 0} clicked</div>
          </div>

          <div style={styles.statCard('#f97316')}>
            <div style={styles.statHeader}>
              <span style={styles.statLabel}>Bounce Rate</span>
              <span style={styles.statIcon}>⚠️</span>
            </div>
            <div style={styles.statValue}>{stats?.bounce_rate || 0}%</div>
            <div style={styles.statSubtext}>0 bounced</div>
          </div>
        </div>

        {/* Engagement Breakdown */}
        <div style={styles.card}>
          <h2 style={styles.cardTitle}>Engagement Breakdown</h2>
          <div style={styles.engagementGrid}>
            <div style={styles.engagementItem('#d1fae5')}>
              <div style={styles.engagementIcon}>✅</div>
              <div style={styles.engagementLabel}>Engaged</div>
              <div style={styles.engagementValue('#16a34a')}>{stats?.total_opened || 0}</div>
              <div style={styles.engagementSubtext}>Opened emails</div>
            </div>

            <div style={styles.engagementItem('#dbeafe')}>
              <div style={styles.engagementIcon}>💙</div>
              <div style={styles.engagementLabel}>Interested</div>
              <div style={styles.engagementValue('#2563eb')}>{stats?.total_clicked || 0}</div>
              <div style={styles.engagementSubtext}>Clicked links</div>
            </div>

            <div style={styles.engagementItem('#f3f4f6')}>
              <div style={styles.engagementIcon}>📊</div>
              <div style={styles.engagementLabel}>Total Leads</div>
              <div style={styles.engagementValue('#4b5563')}>{stats?.total_leads || 0}</div>
              <div style={styles.engagementSubtext}>In database</div>
            </div>
          </div>
        </div>

        {/* Performance by Day */}
        <div style={styles.card}>
          <h2 style={styles.cardTitle}>Performance by Day (Last 30 Days)</h2>
          {performance.length === 0 ? (
            <div style={styles.emptyState}>
              <p style={{ fontSize: '18px' }}>No email activity in the last 30 days</p>
              <p style={{ marginTop: '8px' }}>Send some emails to see performance data here!</p>
            </div>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table style={styles.table}>
                <thead>
                  <tr>
                    <th style={styles.th}>Date</th>
                    <th style={styles.thCenter}>Sent</th>
                    <th style={styles.thCenter}>Opened</th>
                    <th style={styles.thCenter}>Clicked</th>
                    <th style={styles.thCenter}>Open Rate</th>
                  </tr>
                </thead>
                <tbody>
                  {performance.map((day, index) => {
                    const badgeType = day.open_rate >= 30 ? 'good' : day.open_rate >= 15 ? 'medium' : 'bad';
                    return (
                      <tr key={index} style={{ backgroundColor: index % 2 === 0 ? 'white' : '#f9fafb' }}>
                        <td style={styles.td}>{day.date}</td>
                        <td style={styles.tdCenter}>{day.emails_sent}</td>
                        <td style={{ ...styles.tdCenter, color: '#16a34a', fontWeight: '500' }}>{day.opened}</td>
                        <td style={{ ...styles.tdCenter, color: '#2563eb', fontWeight: '500' }}>{day.clicked}</td>
                        <td style={styles.tdCenter}>
                          <span style={styles.badge(badgeType)}>{day.open_rate}%</span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Analytics;
