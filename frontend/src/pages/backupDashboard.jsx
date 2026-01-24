// Dashboard.jsx - Week 6 Day 5-6
// Email Performance Dashboard with Stats and Charts

import { useState, useEffect } from 'react';
import { 
  Mail, Send, Eye, MousePointer, AlertTriangle, Users,
  TrendingUp, TrendingDown, RefreshCw, Calendar,
  CheckCircle, Clock, XCircle, ArrowRight
} from 'lucide-react';
import { dashboardAPI } from '../api';

function Dashboard() {
  const [stats, setStats] = useState(null);
  const [recentActivity, setRecentActivity] = useState([]);
  const [funnel, setFunnel] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    setLoading(true);
    try {
      const [statsRes, recentRes, funnelRes] = await Promise.all([
        dashboardAPI.getStats(),
        dashboardAPI.getRecent(10),
        dashboardAPI.getFunnel()
      ]);
      
      setStats(statsRes.data);
      setRecentActivity(recentRes.data.recent_activity || []);
      setFunnel(funnelRes.data.funnel || []);
    } catch (err) {
      console.error('Failed to fetch dashboard data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchDashboardData();
    setRefreshing(false);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-8 h-8 animate-spin text-blue-500" />
        <span className="ml-2 text-gray-600">Loading dashboard...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-600">Email performance overview</p>
        </div>
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Emails Sent"
          value={stats?.emails?.sent || 0}
          icon={<Send className="w-6 h-6" />}
          color="blue"
          subtitle={`${stats?.emails?.total || 0} total emails`}
        />
        <StatCard
          title="Open Rate"
          value={`${stats?.rates?.open_rate || 0}%`}
          icon={<Eye className="w-6 h-6" />}
          color="green"
          subtitle={`${stats?.emails?.opened || 0} opened`}
        />
        <StatCard
          title="Click Rate"
          value={`${stats?.rates?.click_rate || 0}%`}
          icon={<MousePointer className="w-6 h-6" />}
          color="purple"
          subtitle={`${stats?.emails?.clicked || 0} clicked`}
        />
        <StatCard
          title="Bounce Rate"
          value={`${stats?.rates?.bounce_rate || 0}%`}
          icon={<AlertTriangle className="w-6 h-6" />}
          color="red"
          subtitle={`${stats?.emails?.bounced || 0} bounced`}
        />
      </div>

      {/* Lead Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard
          title="Total Leads"
          value={stats?.leads?.total || 0}
          icon={<Users className="w-6 h-6" />}
          color="gray"
          subtitle="In database"
        />
        <StatCard
          title="Engaged"
          value={stats?.leads?.engaged || 0}
          icon={<CheckCircle className="w-6 h-6" />}
          color="emerald"
          subtitle="Opened emails"
        />
        <StatCard
          title="Interested"
          value={stats?.leads?.interested || 0}
          icon={<TrendingUp className="w-6 h-6" />}
          color="cyan"
          subtitle="Clicked links"
        />
        <StatCard
          title="Pending"
          value={(stats?.leads?.new || 0) + (stats?.leads?.researched || 0)}
          icon={<Clock className="w-6 h-6" />}
          color="yellow"
          subtitle="Not yet contacted"
        />
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Lead Funnel */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Lead Funnel</h2>
          <div className="space-y-3">
            {funnel.length > 0 ? (
              funnel.map((stage, index) => (
                <FunnelBar 
                  key={stage.status}
                  label={stage.label}
                  count={stage.count}
                  color={stage.color}
                  maxCount={Math.max(...funnel.map(f => f.count))}
                />
              ))
            ) : (
              <p className="text-gray-500 text-center py-4">No lead data yet</p>
            )}
          </div>
        </div>

        {/* Recent Activity */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Activity</h2>
          <div className="space-y-3 max-h-80 overflow-y-auto">
            {recentActivity.length > 0 ? (
              recentActivity.map((activity) => (
                <ActivityItem key={activity.id} activity={activity} />
              ))
            ) : (
              <p className="text-gray-500 text-center py-4">No recent activity</p>
            )}
          </div>
        </div>
      </div>

      {/* Performance Summary */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Performance Summary</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          <SummaryItem 
            label="Total Opens" 
            value={stats?.emails?.total_opens || 0}
            icon={<Eye className="w-5 h-5 text-green-500" />}
          />
          <SummaryItem 
            label="Total Clicks" 
            value={stats?.emails?.total_clicks || 0}
            icon={<MousePointer className="w-5 h-5 text-purple-500" />}
          />
          <SummaryItem 
            label="Delivery Rate" 
            value={`${stats?.rates?.delivery_rate || 0}%`}
            icon={<CheckCircle className="w-5 h-5 text-blue-500" />}
          />
          <SummaryItem 
            label="Click-to-Open" 
            value={`${stats?.rates?.click_to_open || 0}%`}
            icon={<TrendingUp className="w-5 h-5 text-cyan-500" />}
          />
        </div>
      </div>
    </div>
  );
}

// Stat Card Component
function StatCard({ title, value, icon, color, subtitle }) {
  const colorClasses = {
    blue: 'bg-blue-50 text-blue-600',
    green: 'bg-green-50 text-green-600',
    purple: 'bg-purple-50 text-purple-600',
    red: 'bg-red-50 text-red-600',
    gray: 'bg-gray-50 text-gray-600',
    emerald: 'bg-emerald-50 text-emerald-600',
    cyan: 'bg-cyan-50 text-cyan-600',
    yellow: 'bg-yellow-50 text-yellow-600'
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-600">{title}</p>
          <p className="text-2xl font-bold text-gray-900 mt-1">{value}</p>
          {subtitle && (
            <p className="text-xs text-gray-500 mt-1">{subtitle}</p>
          )}
        </div>
        <div className={`p-3 rounded-lg ${colorClasses[color]}`}>
          {icon}
        </div>
      </div>
    </div>
  );
}

// Funnel Bar Component
function FunnelBar({ label, count, color, maxCount }) {
  const percentage = maxCount > 0 ? (count / maxCount) * 100 : 0;
  
  return (
    <div className="flex items-center gap-3">
      <div className="w-32 text-sm text-gray-600 truncate">{label}</div>
      <div className="flex-1 bg-gray-100 rounded-full h-6 overflow-hidden">
        <div 
          className="h-full rounded-full flex items-center justify-end pr-2 transition-all duration-500"
          style={{ 
            width: `${Math.max(percentage, 5)}%`,
            backgroundColor: color 
          }}
        >
          <span className="text-xs font-medium text-white">{count}</span>
        </div>
      </div>
    </div>
  );
}

// Activity Item Component
function ActivityItem({ activity }) {
  const getStatusIcon = () => {
    if (activity.click_count > 0) {
      return <MousePointer className="w-4 h-4 text-purple-500" />;
    } else if (activity.open_count > 0) {
      return <Eye className="w-4 h-4 text-green-500" />;
    } else if (activity.status === 'bounced') {
      return <XCircle className="w-4 h-4 text-red-500" />;
    } else {
      return <Send className="w-4 h-4 text-blue-500" />;
    }
  };

  const getStatusText = () => {
    if (activity.click_count > 0) {
      return `Clicked ${activity.click_count}x`;
    } else if (activity.open_count > 0) {
      return `Opened ${activity.open_count}x`;
    } else if (activity.status === 'bounced') {
      return 'Bounced';
    } else {
      return 'Sent';
    }
  };

  return (
    <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
      <div className="flex-shrink-0">
        {getStatusIcon()}
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-gray-900 truncate">
          {activity.lead_name}
        </p>
        <p className="text-xs text-gray-500 truncate">
          {activity.company} - {activity.subject}
        </p>
      </div>
      <div className="text-right">
        <p className="text-xs font-medium text-gray-700">{getStatusText()}</p>
        <p className="text-xs text-gray-400">
          {activity.sent_at ? new Date(activity.sent_at).toLocaleDateString() : '-'}
        </p>
      </div>
    </div>
  );
}

// Summary Item Component
function SummaryItem({ label, value, icon }) {
  return (
    <div className="flex items-center gap-3">
      {icon}
      <div>
        <p className="text-sm text-gray-600">{label}</p>
        <p className="text-lg font-semibold text-gray-900">{value}</p>
      </div>
    </div>
  );
}

export default Dashboard;
