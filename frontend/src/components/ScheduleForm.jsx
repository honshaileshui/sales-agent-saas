import { useState, useEffect } from 'react';
import { Calendar, Clock, Globe, Hash } from 'lucide-react';

const API_BASE = 'http://localhost:8000';

const TIMEZONES = [
  { value: 'UTC', label: 'UTC' },
  { value: 'America/New_York', label: 'Eastern (New York)' },
  { value: 'America/Chicago', label: 'Central (Chicago)' },
  { value: 'America/Denver', label: 'Mountain (Denver)' },
  { value: 'America/Los_Angeles', label: 'Pacific (Los Angeles)' },
  { value: 'Europe/London', label: 'Europe (London)' },
  { value: 'Europe/Paris', label: 'Europe (Paris)' },
  { value: 'Europe/Berlin', label: 'Europe (Berlin)' },
  { value: 'Asia/Tokyo', label: 'Asia (Tokyo)' },
  { value: 'Asia/Shanghai', label: 'Asia (Shanghai)' },
  { value: 'Asia/Kolkata', label: 'India (Kolkata)' },
  { value: 'Australia/Sydney', label: 'Australia (Sydney)' },
];

function ScheduleForm({ campaignId, existingSchedule, onSave, onCancel }) {
  const [scheduledDate, setScheduledDate] = useState('');
  const [scheduledTime, setScheduledTime] = useState('09:00');
  const [timezone, setTimezone] = useState('UTC');
  const [dailyLimit, setDailyLimit] = useState(50);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const id = 'schedule-form-spin';
    if (!document.getElementById(id)) {
      const el = document.createElement('style');
      el.id = id;
      el.textContent = '@keyframes spin { to { transform: rotate(360deg); } }';
      document.head.appendChild(el);
    }
  }, []);

  useEffect(() => {
    if (existingSchedule) {
      if (existingSchedule.scheduled_start_date) {
        const d = typeof existingSchedule.scheduled_start_date === 'string'
          ? existingSchedule.scheduled_start_date.slice(0, 10)
          : existingSchedule.scheduled_start_date;
        setScheduledDate(d);
      }
      if (existingSchedule.scheduled_start_time) {
        const t = String(existingSchedule.scheduled_start_time);
        setScheduledTime(t.length === 8 ? t.slice(0, 5) : t.slice(0, 5));
      }
      if (existingSchedule.timezone) setTimezone(existingSchedule.timezone);
      if (existingSchedule.daily_send_limit != null) setDailyLimit(existingSchedule.daily_send_limit);
    } else {
      const today = new Date().toISOString().slice(0, 10);
      setScheduledDate(today);
    }
  }, [existingSchedule]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    if (!scheduledDate) {
      setError('Please select a start date.');
      return;
    }
    setLoading(true);
    try {
      const timeValue = scheduledTime.length === 5 ? `${scheduledTime}:00` : scheduledTime;
      const body = {
        scheduled_start_date: scheduledDate,
        scheduled_start_time: timeValue,
        timezone,
        daily_send_limit: dailyLimit,
      };
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE}/api/campaigns/${campaignId}/schedule`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: token ? `Bearer ${token}` : '',
        },
        body: JSON.stringify(body),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(data.detail || (typeof data.detail === 'string' ? data.detail : 'Failed to save schedule'));
      }
      onSave?.(data);
    } catch (err) {
      setError(err.message || 'Failed to save schedule.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} style={styles.form}>
      <div style={styles.card}>
        <div style={styles.cardGradient} />
        <div style={styles.cardInner}>
          <h3 style={styles.title}>Schedule campaign</h3>
          <p style={styles.subtitle}>Set when and how many emails to send per day.</p>

          {error && (
            <div style={styles.errorBox}>
              {error}
            </div>
          )}

          <div style={styles.formGroup}>
            <label style={styles.label}>
              <Calendar size={16} style={{ verticalAlign: 'middle', marginRight: '6px' }} />
              Start date
            </label>
            <input
              type="date"
              value={scheduledDate}
              onChange={(e) => setScheduledDate(e.target.value)}
              style={styles.input}
              required
            />
          </div>

          <div style={styles.formGroup}>
            <label style={styles.label}>
              <Clock size={16} style={{ verticalAlign: 'middle', marginRight: '6px' }} />
              Start time
            </label>
            <input
              type="time"
              value={scheduledTime}
              onChange={(e) => setScheduledTime(e.target.value)}
              style={styles.input}
              required
            />
          </div>

          <div style={styles.formGroup}>
            <label style={styles.label}>
              <Globe size={16} style={{ verticalAlign: 'middle', marginRight: '6px' }} />
              Timezone
            </label>
            <select
              value={timezone}
              onChange={(e) => setTimezone(e.target.value)}
              style={styles.select}
            >
              {TIMEZONES.map((tz) => (
                <option key={tz.value} value={tz.value}>
                  {tz.label}
                </option>
              ))}
            </select>
          </div>

          <div style={styles.formGroup}>
            <label style={styles.label}>
              <Hash size={16} style={{ verticalAlign: 'middle', marginRight: '6px' }} />
              Daily send limit
            </label>
            <input
              type="number"
              min={1}
              max={500}
              value={dailyLimit}
              onChange={(e) => setDailyLimit(Number(e.target.value) || 50)}
              style={styles.input}
            />
            <span style={styles.hint}>1â€“500 emails per day</span>
          </div>

          <div style={styles.actions}>
            <button
              type="button"
              onClick={onCancel}
              style={styles.cancelBtn}
              disabled={loading}
            >
              Cancel
            </button>
            <button
              type="submit"
              style={styles.saveBtn}
              disabled={loading}
            >
              {loading ? (
                <>
                  <span style={styles.spinner} />
                  Savingâ€¦
                </>
              ) : (
                'Save schedule'
              )}
            </button>
          </div>
        </div>
      </div>
    </form>
  );
}

const styles = {
  form: {
    width: '100%',
    maxWidth: '420px',
  },
  card: {
    position: 'relative',
    background: 'white',
    borderRadius: '16px',
    boxShadow: '0 4px 20px rgba(102, 126, 234, 0.15)',
    overflow: 'hidden',
  },
  cardGradient: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    height: '4px',
    background: 'linear-gradient(90deg, #667eea 0%, #764ba2 100%)',
  },
  cardInner: {
    padding: '24px',
  },
  title: {
    fontSize: '20px',
    fontWeight: '600',
    color: '#1a1a2e',
    margin: '0 0 4px 0',
  },
  subtitle: {
    fontSize: '14px',
    color: '#666',
    margin: '0 0 20px 0',
  },
  errorBox: {
    padding: '12px 14px',
    background: '#fef2f2',
    color: '#dc2626',
    borderRadius: '8px',
    fontSize: '14px',
    marginBottom: '16px',
  },
  formGroup: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
    marginBottom: '18px',
  },
  label: {
    fontSize: '14px',
    fontWeight: '500',
    color: '#333',
  },
  input: {
    padding: '12px 14px',
    fontSize: '15px',
    border: '1px solid #e0e0e0',
    borderRadius: '8px',
    outline: 'none',
    transition: 'border-color 0.2s',
  },
  select: {
    padding: '12px 14px',
    fontSize: '15px',
    border: '1px solid #e0e0e0',
    borderRadius: '8px',
    outline: 'none',
    background: 'white',
    cursor: 'pointer',
  },
  hint: {
    fontSize: '12px',
    color: '#999',
    marginTop: '2px',
  },
  actions: {
    display: 'flex',
    gap: '12px',
    justifyContent: 'flex-end',
    marginTop: '24px',
    paddingTop: '20px',
    borderTop: '1px solid #eee',
  },
  cancelBtn: {
    padding: '12px 24px',
    background: '#f5f5f5',
    border: 'none',
    borderRadius: '8px',
    fontSize: '15px',
    fontWeight: '500',
    color: '#555',
    cursor: 'pointer',
  },
  saveBtn: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '8px',
    padding: '12px 24px',
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    color: 'white',
    border: 'none',
    borderRadius: '8px',
    fontSize: '15px',
    fontWeight: '600',
    cursor: 'pointer',
    boxShadow: '0 2px 8px rgba(102, 126, 234, 0.4)',
  },
  spinner: {
    width: '18px',
    height: '18px',
    border: '2px solid rgba(255,255,255,0.3)',
    borderTopColor: 'white',
    borderRadius: '50%',
    animation: 'spin 1s linear infinite',
  },
};

export default ScheduleForm;