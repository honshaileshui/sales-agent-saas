// Emails Page Component
import { useState, useEffect } from 'react';
import { 
  Search, Filter, Mail, Eye, Edit2, Check, Send, Trash2, 
  RefreshCw, X, AlertCircle, Clock, CheckCircle, XCircle,
  ChevronDown, MoreHorizontal
} from 'lucide-react';
import { emailsAPI, leadsAPI } from '../api';

function Emails() {
  const [emails, setEmails] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('');
  const [search, setSearch] = useState('');
  const [selectedEmail, setSelectedEmail] = useState(null);
  const [showPreviewModal, setShowPreviewModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showGenerateModal, setShowGenerateModal] = useState(false);
  const [selectedEmails, setSelectedEmails] = useState([]);
  const [pagination, setPagination] = useState({ page: 1, total: 0, pages: 1 });

  useEffect(() => {
    fetchEmails();
  }, [statusFilter, pagination.page]);

  const fetchEmails = async () => {
    setLoading(true);
    try {
      const params = { page: pagination.page, per_page: 20 };
      if (statusFilter) params.status = statusFilter;
      if (search) params.search = search;
      
      const response = await emailsAPI.getAll(params);
      setEmails(response.data.emails || response.data || []);
      if (response.data.pagination) {
        setPagination(response.data.pagination);
      }
    } catch (err) {
      console.error('Failed to fetch emails:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    setPagination(prev => ({ ...prev, page: 1 }));
    fetchEmails();
  };

  const handlePreview = (email) => {
    setSelectedEmail(email);
    setShowPreviewModal(true);
  };

  const handleEdit = (email) => {
    setSelectedEmail(email);
    setShowEditModal(true);
  };

  const handleApprove = async (id) => {
    try {
      await emailsAPI.approve(id);
      setEmails(emails.map(e => e.id === id ? { ...e, status: 'approved' } : e));
    } catch (err) {
      alert('Failed to approve email');
    }
  };

  const handleSend = async (id) => {
    if (!window.confirm('Send this email now?')) return;
    try {
      await emailsAPI.send(id);
      setEmails(emails.map(e => e.id === id ? { ...e, status: 'sent' } : e));
    } catch (err) {
      alert('Failed to send email');
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this email?')) return;
    try {
      await emailsAPI.delete(id);
      setEmails(emails.filter(e => e.id !== id));
    } catch (err) {
      alert('Failed to delete email');
    }
  };

  const handleRegenerate = async (id) => {
    try {
      const response = await emailsAPI.regenerate(id);
      setEmails(emails.map(e => e.id === id ? response.data : e));
    } catch (err) {
      alert('Failed to regenerate email');
    }
  };

  const handleSelectEmail = (id) => {
    setSelectedEmails(prev => 
      prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
    );
  };

  const handleSelectAll = () => {
    if (selectedEmails.length === emails.length) {
      setSelectedEmails([]);
    } else {
      setSelectedEmails(emails.map(e => e.id));
    }
  };

  const handleBulkApprove = async () => {
    if (!selectedEmails.length) return;
    try {
      await emailsAPI.approveBulk(selectedEmails);
      setEmails(emails.map(e => 
        selectedEmails.includes(e.id) ? { ...e, status: 'approved' } : e
      ));
      setSelectedEmails([]);
    } catch (err) {
      alert('Failed to approve emails');
    }
  };

  const handleBulkSend = async () => {
    if (!selectedEmails.length) return;
    if (!window.confirm(`Send ${selectedEmails.length} emails now?`)) return;
    try {
      await emailsAPI.sendBulk(selectedEmails);
      setEmails(emails.map(e => 
        selectedEmails.includes(e.id) ? { ...e, status: 'sent' } : e
      ));
      setSelectedEmails([]);
    } catch (err) {
      alert('Failed to send emails');
    }
  };

  const handleEditSave = async (id, updatedData) => {
    try {
      await emailsAPI.update(id, updatedData);
      setEmails(emails.map(e => e.id === id ? { ...e, ...updatedData } : e));
      setShowEditModal(false);
    } catch (err) {
      alert('Failed to update email');
    }
  };

  const getStatusInfo = (status) => {
    const statuses = {
      draft: { bg: '#f3f4f6', text: '#6b7280', icon: Clock, label: 'Draft' },
      approved: { bg: '#d1fae5', text: '#059669', icon: CheckCircle, label: 'Approved' },
      sent: { bg: '#dbeafe', text: '#2563eb', icon: Send, label: 'Sent' },
      opened: { bg: '#fef3c7', text: '#d97706', icon: Eye, label: 'Opened' },
      clicked: { bg: '#e0e7ff', text: '#4338ca', icon: Check, label: 'Clicked' },
      replied: { bg: '#f3e8ff', text: '#9333ea', icon: Mail, label: 'Replied' },
      bounced: { bg: '#fee2e2', text: '#dc2626', icon: XCircle, label: 'Bounced' },
    };
    return statuses[status] || statuses.draft;
  };

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <div>
          <h1 style={styles.title}>Emails</h1>
          <p style={styles.subtitle}>Manage AI-generated sales emails</p>
        </div>
        <button style={styles.generateBtn} onClick={() => setShowGenerateModal(true)}>
          <Mail size={20} />
          Generate Emails
        </button>
      </div>

      {/* Stats Cards */}
      <div style={styles.statsGrid}>
        <div style={styles.statCard}>
          <Mail size={24} color="#667eea" />
          <div>
            <p style={styles.statValue}>{emails.length}</p>
            <p style={styles.statLabel}>Total Emails</p>
          </div>
        </div>
        <div style={styles.statCard}>
          <Clock size={24} color="#f59e0b" />
          <div>
            <p style={styles.statValue}>{emails.filter(e => e.status === 'draft').length}</p>
            <p style={styles.statLabel}>Drafts</p>
          </div>
        </div>
        <div style={styles.statCard}>
          <CheckCircle size={24} color="#10b981" />
          <div>
            <p style={styles.statValue}>{emails.filter(e => e.status === 'approved').length}</p>
            <p style={styles.statLabel}>Approved</p>
          </div>
        </div>
        <div style={styles.statCard}>
          <Send size={24} color="#3b82f6" />
          <div>
            <p style={styles.statValue}>{emails.filter(e => e.status === 'sent').length}</p>
            <p style={styles.statLabel}>Sent</p>
          </div>
        </div>
      </div>

      {/* Bulk Actions */}
      {selectedEmails.length > 0 && (
        <div style={styles.bulkActions}>
          <span style={styles.bulkCount}>{selectedEmails.length} selected</span>
          <button style={styles.bulkBtn} onClick={handleBulkApprove}>
            <Check size={16} /> Approve All
          </button>
          <button style={{...styles.bulkBtn, background: '#3b82f6'}} onClick={handleBulkSend}>
            <Send size={16} /> Send All
          </button>
        </div>
      )}

      {/* Filters */}
      <div style={styles.filters}>
        <form onSubmit={handleSearch} style={styles.searchBox}>
          <Search size={20} color="#999" />
          <input
            type="text"
            placeholder="Search by recipient..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={styles.searchInput}
          />
        </form>
        <div style={styles.filterGroup}>
          <Filter size={18} color="#666" />
          <select 
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value);
              setPagination(prev => ({ ...prev, page: 1 }));
            }}
            style={styles.select}
          >
            <option value="">All Status</option>
            <option value="draft">Draft</option>
            <option value="approved">Approved</option>
            <option value="sent">Sent</option>
            <option value="opened">Opened</option>
            <option value="replied">Replied</option>
            <option value="bounced">Bounced</option>
          </select>
        </div>
      </div>

      {/* Emails Table */}
      <div style={styles.tableContainer}>
        {loading ? (
          <div style={styles.loading}>Loading emails...</div>
        ) : emails.length === 0 ? (
          <div style={styles.empty}>
            <Mail size={64} color="#ddd" />
            <h3 style={styles.emptyTitle}>No emails yet</h3>
            <p style={styles.emptyText}>Generate emails for your leads to get started</p>
            <button style={styles.emptyBtn} onClick={() => setShowGenerateModal(true)}>
              Generate Emails
            </button>
          </div>
        ) : (
          <table style={styles.table}>
            <thead>
              <tr style={styles.tableHeader}>
                <th style={styles.th}>
                  <input 
                    type="checkbox" 
                    checked={selectedEmails.length === emails.length && emails.length > 0}
                    onChange={handleSelectAll}
                    style={styles.checkbox}
                  />
                </th>
                <th style={styles.th}>Recipient</th>
                <th style={styles.th}>Subject</th>
                <th style={styles.th}>Status</th>
                <th style={styles.th}>Created</th>
                <th style={styles.th}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {emails.map((email) => {
                const statusInfo = getStatusInfo(email.status);
                return (
                  <tr key={email.id} style={styles.tableRow}>
                    <td style={styles.td}>
                      <input 
                        type="checkbox"
                        checked={selectedEmails.includes(email.id)}
                        onChange={() => handleSelectEmail(email.id)}
                        style={styles.checkbox}
                      />
                    </td>
                    <td style={styles.td}>
                      <div style={styles.recipient}>
                        <strong>{email.lead_name || 'Unknown'}</strong>
                        <span style={styles.recipientEmail}>{email.to_email}</span>
                      </div>
                    </td>
                    <td style={styles.td}>
                      <div style={styles.subjectCell}>
                        {email.subject || 'No subject'}
                      </div>
                    </td>
                    <td style={styles.td}>
                      <span style={{
                        ...styles.statusBadge,
                        backgroundColor: statusInfo.bg,
                        color: statusInfo.text
                      }}>
                        <statusInfo.icon size={14} />
                        {statusInfo.label}
                      </span>
                    </td>
                    <td style={styles.td}>
                      <span style={styles.dateCell}>
                        {new Date(email.created_at).toLocaleDateString()}
                      </span>
                    </td>
                    <td style={styles.td}>
                      <div style={styles.actions}>
                        <button style={styles.iconBtn} onClick={() => handlePreview(email)} title="Preview">
                          <Eye size={18} />
                        </button>
                        <button style={styles.iconBtn} onClick={() => handleEdit(email)} title="Edit">
                          <Edit2 size={18} />
                        </button>
                        {email.status === 'draft' && (
                          <>
                            <button style={{...styles.iconBtn, color: '#10b981'}} onClick={() => handleApprove(email.id)} title="Approve">
                              <Check size={18} />
                            </button>
                            <button style={styles.iconBtn} onClick={() => handleRegenerate(email.id)} title="Regenerate">
                              <RefreshCw size={18} />
                            </button>
                          </>
                        )}
                        {email.status === 'approved' && (
                          <button style={{...styles.iconBtn, color: '#3b82f6'}} onClick={() => handleSend(email.id)} title="Send">
                            <Send size={18} />
                          </button>
                        )}
                        <button style={{...styles.iconBtn, color: '#ef4444'}} onClick={() => handleDelete(email.id)} title="Delete">
                          <Trash2 size={18} />
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>

      {/* Pagination */}
      {pagination.pages > 1 && (
        <div style={styles.pagination}>
          <button 
            style={styles.pageBtn}
            disabled={pagination.page === 1}
            onClick={() => setPagination(prev => ({ ...prev, page: prev.page - 1 }))}
          >
            Previous
          </button>
          <span style={styles.pageInfo}>Page {pagination.page} of {pagination.pages}</span>
          <button 
            style={styles.pageBtn}
            disabled={pagination.page === pagination.pages}
            onClick={() => setPagination(prev => ({ ...prev, page: prev.page + 1 }))}
          >
            Next
          </button>
        </div>
      )}

      {/* Preview Modal */}
      {showPreviewModal && selectedEmail && (
        <EmailPreviewModal 
          email={selectedEmail}
          onClose={() => setShowPreviewModal(false)}
          onApprove={() => {
            handleApprove(selectedEmail.id);
            setShowPreviewModal(false);
          }}
          onEdit={() => {
            setShowPreviewModal(false);
            setShowEditModal(true);
          }}
        />
      )}

      {/* Edit Modal */}
      {showEditModal && selectedEmail && (
        <EmailEditModal 
          email={selectedEmail}
          onClose={() => setShowEditModal(false)}
          onSave={(data) => handleEditSave(selectedEmail.id, data)}
        />
      )}

      {/* Generate Modal */}
      {showGenerateModal && (
        <GenerateEmailsModal 
          onClose={() => setShowGenerateModal(false)}
          onSuccess={() => {
            setShowGenerateModal(false);
            fetchEmails();
          }}
        />
      )}
    </div>
  );
}

// Email Preview Modal
function EmailPreviewModal({ email, onClose, onApprove, onEdit }) {
  return (
    <div style={styles.modalOverlay} onClick={onClose}>
      <div style={styles.previewModal} onClick={e => e.stopPropagation()}>
        <div style={styles.modalHeader}>
          <h2 style={styles.modalTitle}>Email Preview</h2>
          <button style={styles.closeBtn} onClick={onClose}><X size={24} /></button>
        </div>
        
        <div style={styles.emailMeta}>
          <div style={styles.metaRow}>
            <span style={styles.metaLabel}>To:</span>
            <span>{email.to_email}</span>
          </div>
          <div style={styles.metaRow}>
            <span style={styles.metaLabel}>Subject:</span>
            <span style={{fontWeight: '600'}}>{email.subject}</span>
          </div>
        </div>

        <div style={styles.emailBody}>
          <div style={styles.emailContent}>
            {email.body?.split('\n').map((line, i) => (
              <p key={i} style={{margin: '0 0 12px'}}>{line || <br/>}</p>
            ))}
          </div>
        </div>

        <div style={styles.previewFooter}>
          {email.status === 'draft' && (
            <>
              <button style={styles.editBtn} onClick={onEdit}>
                <Edit2 size={18} /> Edit
              </button>
              <button style={styles.approveBtn} onClick={onApprove}>
                <Check size={18} /> Approve
              </button>
            </>
          )}
          <button style={styles.closeModalBtn} onClick={onClose}>Close</button>
        </div>
      </div>
    </div>
  );
}

// Email Edit Modal
function EmailEditModal({ email, onClose, onSave }) {
  const [subject, setSubject] = useState(email.subject || '');
  const [body, setBody] = useState(email.body || '');
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    setSaving(true);
    await onSave({ subject, body });
    setSaving(false);
  };

  return (
    <div style={styles.modalOverlay} onClick={onClose}>
      <div style={styles.editModal} onClick={e => e.stopPropagation()}>
        <div style={styles.modalHeader}>
          <h2 style={styles.modalTitle}>Edit Email</h2>
          <button style={styles.closeBtn} onClick={onClose}><X size={24} /></button>
        </div>
        
        <div style={styles.editContent}>
          <div style={styles.editMeta}>
            <span style={styles.metaLabel}>To:</span>
            <span>{email.to_email}</span>
          </div>

          <div style={styles.formGroup}>
            <label style={styles.label}>Subject</label>
            <input
              type="text"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              style={styles.input}
            />
          </div>

          <div style={styles.formGroup}>
            <label style={styles.label}>Body</label>
            <textarea
              value={body}
              onChange={(e) => setBody(e.target.value)}
              style={styles.bodyTextarea}
              rows={12}
            />
          </div>
        </div>

        <div style={styles.editFooter}>
          <button style={styles.cancelBtn} onClick={onClose}>Cancel</button>
          <button 
            style={{...styles.saveBtn, opacity: saving ? 0.7 : 1}}
            onClick={handleSave}
            disabled={saving}
          >
            {saving ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      </div>
    </div>
  );
}

// Generate Emails Modal
function GenerateEmailsModal({ onClose, onSuccess }) {
  const [leads, setLeads] = useState([]);
  const [selectedLeads, setSelectedLeads] = useState([]);
  const [template, setTemplate] = useState('default');
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchLeads();
  }, []);

  const fetchLeads = async () => {
    try {
      // Get leads that don't have emails yet
      const response = await leadsAPI.getAll({ status: 'new', per_page: 100 });
      setLeads(response.data.leads || response.data || []);
    } catch (err) {
      console.error('Failed to fetch leads:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectLead = (id) => {
    setSelectedLeads(prev => 
      prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
    );
  };

  const handleSelectAll = () => {
    if (selectedLeads.length === leads.length) {
      setSelectedLeads([]);
    } else {
      setSelectedLeads(leads.map(l => l.id));
    }
  };

  const handleGenerate = async () => {
    if (selectedLeads.length === 0) {
      setError('Please select at least one lead');
      return;
    }

    setGenerating(true);
    setError('');

    try {
      await emailsAPI.generateBulk(selectedLeads, null, template);
      onSuccess();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to generate emails');
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div style={styles.modalOverlay} onClick={onClose}>
      <div style={styles.generateModal} onClick={e => e.stopPropagation()}>
        <div style={styles.modalHeader}>
          <h2 style={styles.modalTitle}>Generate Emails</h2>
          <button style={styles.closeBtn} onClick={onClose}><X size={24} /></button>
        </div>

        <div style={styles.generateContent}>
          {error && (
            <div style={styles.errorBox}>
              <AlertCircle size={20} />{error}
            </div>
          )}

          <div style={styles.formGroup}>
            <label style={styles.label}>Email Template</label>
            <select 
              value={template}
              onChange={(e) => setTemplate(e.target.value)}
              style={styles.selectFull}
            >
              <option value="default">Default - Professional outreach</option>
              <option value="friendly">Friendly - Conversational tone</option>
              <option value="direct">Direct - Straight to the point</option>
              <option value="value">Value-First - Lead with benefits</option>
            </select>
          </div>

          <div style={styles.leadsSection}>
            <div style={styles.leadsHeader}>
              <label style={styles.label}>Select Leads ({selectedLeads.length} selected)</label>
              <button style={styles.selectAllBtn} onClick={handleSelectAll}>
                {selectedLeads.length === leads.length ? 'Deselect All' : 'Select All'}
              </button>
            </div>

            {loading ? (
              <div style={{padding: '40px', textAlign: 'center', color: '#666'}}>Loading leads...</div>
            ) : leads.length === 0 ? (
              <div style={{padding: '40px', textAlign: 'center', color: '#666'}}>
                No new leads available. Import leads first.
              </div>
            ) : (
              <div style={styles.leadsList}>
                {leads.map((lead) => (
                  <div 
                    key={lead.id}
                    style={{
                      ...styles.leadItem,
                      backgroundColor: selectedLeads.includes(lead.id) ? '#f0f4ff' : 'white',
                      borderColor: selectedLeads.includes(lead.id) ? '#667eea' : '#e0e0e0'
                    }}
                    onClick={() => handleSelectLead(lead.id)}
                  >
                    <input
                      type="checkbox"
                      checked={selectedLeads.includes(lead.id)}
                      onChange={() => {}}
                      style={styles.checkbox}
                    />
                    <div style={{flex: 1}}>
                      <strong>{lead.name}</strong>
                      <div style={{fontSize: '13px', color: '#666'}}>{lead.email}</div>
                    </div>
                    <div style={{color: '#666', fontSize: '14px'}}>{lead.company}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        <div style={styles.generateFooter}>
          <button style={styles.cancelBtn} onClick={onClose}>Cancel</button>
          <button 
            style={{...styles.generateBtn2, opacity: generating || selectedLeads.length === 0 ? 0.7 : 1}}
            onClick={handleGenerate}
            disabled={generating || selectedLeads.length === 0}
          >
            {generating ? 'Generating...' : `Generate ${selectedLeads.length} Email${selectedLeads.length !== 1 ? 's' : ''}`}
          </button>
        </div>
      </div>
    </div>
  );
}

const styles = {
  container: { padding: '30px', maxWidth: '1400px', margin: '0 auto' },
  header: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' },
  title: { fontSize: '28px', fontWeight: '700', color: '#1a1a2e', margin: '0 0 8px 0' },
  subtitle: { color: '#666', margin: 0 },
  generateBtn: { display: 'flex', alignItems: 'center', gap: '8px', padding: '12px 24px', background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: 'white', border: 'none', borderRadius: '8px', fontSize: '15px', fontWeight: '500', cursor: 'pointer' },
  statsGrid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '16px', marginBottom: '24px' },
  statCard: { background: 'white', borderRadius: '12px', padding: '20px', display: 'flex', alignItems: 'center', gap: '16px', boxShadow: '0 2px 8px rgba(0,0,0,0.08)' },
  statValue: { fontSize: '24px', fontWeight: '700', color: '#1a1a2e', margin: 0 },
  statLabel: { fontSize: '13px', color: '#666', margin: 0 },
  bulkActions: { display: 'flex', alignItems: 'center', gap: '16px', padding: '12px 20px', background: '#f0f4ff', borderRadius: '8px', marginBottom: '16px' },
  bulkCount: { fontSize: '14px', fontWeight: '600', color: '#667eea' },
  bulkBtn: { display: 'flex', alignItems: 'center', gap: '6px', padding: '8px 16px', background: '#10b981', color: 'white', border: 'none', borderRadius: '6px', fontSize: '14px', cursor: 'pointer' },
  filters: { display: 'flex', gap: '16px', marginBottom: '24px' },
  searchBox: { display: 'flex', alignItems: 'center', gap: '10px', padding: '10px 16px', background: 'white', borderRadius: '8px', border: '1px solid #e0e0e0', flex: '1', maxWidth: '400px' },
  searchInput: { border: 'none', outline: 'none', flex: '1', fontSize: '15px' },
  filterGroup: { display: 'flex', alignItems: 'center', gap: '8px', padding: '10px 16px', background: 'white', borderRadius: '8px', border: '1px solid #e0e0e0' },
  select: { border: 'none', outline: 'none', fontSize: '15px', background: 'transparent', cursor: 'pointer' },
  tableContainer: { background: 'white', borderRadius: '12px', boxShadow: '0 2px 8px rgba(0,0,0,0.08)', overflow: 'hidden' },
  loading: { padding: '60px', textAlign: 'center', color: '#666' },
  empty: { padding: '80px 40px', textAlign: 'center' },
  emptyTitle: { fontSize: '20px', fontWeight: '600', color: '#333', margin: '20px 0 8px' },
  emptyText: { color: '#666', margin: '0 0 24px' },
  emptyBtn: { padding: '12px 24px', background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: 'white', border: 'none', borderRadius: '8px', fontSize: '15px', cursor: 'pointer' },
  table: { width: '100%', borderCollapse: 'collapse' },
  tableHeader: { background: '#f8f9fa' },
  th: { padding: '16px', textAlign: 'left', fontSize: '12px', fontWeight: '600', color: '#666', textTransform: 'uppercase', borderBottom: '1px solid #eee' },
  tableRow: { borderBottom: '1px solid #eee' },
  td: { padding: '16px', fontSize: '14px', color: '#333' },
  checkbox: { width: '18px', height: '18px', cursor: 'pointer' },
  recipient: { display: 'flex', flexDirection: 'column', gap: '2px' },
  recipientEmail: { fontSize: '13px', color: '#666' },
  subjectCell: { maxWidth: '300px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' },
  statusBadge: { display: 'inline-flex', alignItems: 'center', gap: '6px', padding: '4px 12px', borderRadius: '20px', fontSize: '12px', fontWeight: '500' },
  dateCell: { color: '#666', fontSize: '13px' },
  actions: { display: 'flex', gap: '4px' },
  iconBtn: { background: 'none', border: 'none', padding: '6px', cursor: 'pointer', color: '#666', borderRadius: '6px' },
  pagination: { display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '16px', marginTop: '24px' },
  pageBtn: { padding: '10px 20px', background: 'white', border: '1px solid #ddd', borderRadius: '8px', cursor: 'pointer', fontSize: '14px' },
  pageInfo: { fontSize: '14px', color: '#666' },
  // Modal styles
  modalOverlay: { position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000, padding: '20px' },
  previewModal: { background: 'white', borderRadius: '16px', width: '100%', maxWidth: '700px', maxHeight: '90vh', display: 'flex', flexDirection: 'column' },
  editModal: { background: 'white', borderRadius: '16px', width: '100%', maxWidth: '700px', maxHeight: '90vh', display: 'flex', flexDirection: 'column' },
  generateModal: { background: 'white', borderRadius: '16px', width: '100%', maxWidth: '600px', maxHeight: '90vh', display: 'flex', flexDirection: 'column' },
  modalHeader: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '24px', borderBottom: '1px solid #eee' },
  modalTitle: { fontSize: '20px', fontWeight: '600', margin: 0, color: '#1a1a2e' },
  closeBtn: { background: 'none', border: 'none', cursor: 'pointer', color: '#999', padding: '4px' },
  emailMeta: { padding: '20px 24px', background: '#f8f9fa', borderBottom: '1px solid #eee' },
  metaRow: { display: 'flex', gap: '12px', padding: '6px 0' },
  metaLabel: { fontWeight: '500', color: '#666', minWidth: '60px' },
  emailBody: { flex: 1, overflow: 'auto', padding: '24px' },
  emailContent: { fontSize: '15px', lineHeight: '1.6', color: '#333' },
  previewFooter: { display: 'flex', justifyContent: 'flex-end', gap: '12px', padding: '20px 24px', borderTop: '1px solid #eee' },
  editBtn: { display: 'flex', alignItems: 'center', gap: '6px', padding: '12px 20px', background: '#f5f5f5', border: 'none', borderRadius: '8px', fontSize: '15px', cursor: 'pointer' },
  approveBtn: { display: 'flex', alignItems: 'center', gap: '6px', padding: '12px 20px', background: '#10b981', color: 'white', border: 'none', borderRadius: '8px', fontSize: '15px', cursor: 'pointer' },
  closeModalBtn: { padding: '12px 20px', background: '#f5f5f5', border: 'none', borderRadius: '8px', fontSize: '15px', cursor: 'pointer' },
  editContent: { flex: 1, overflow: 'auto', padding: '24px' },
  editMeta: { display: 'flex', gap: '12px', padding: '12px 16px', background: '#f8f9fa', borderRadius: '8px', marginBottom: '20px' },
  formGroup: { display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '20px' },
  label: { fontSize: '14px', fontWeight: '500', color: '#333' },
  input: { padding: '12px 14px', fontSize: '15px', border: '1px solid #ddd', borderRadius: '8px', outline: 'none' },
  bodyTextarea: { padding: '14px', fontSize: '15px', border: '1px solid #ddd', borderRadius: '8px', outline: 'none', resize: 'vertical', fontFamily: 'inherit', lineHeight: '1.6' },
  editFooter: { display: 'flex', justifyContent: 'flex-end', gap: '12px', padding: '20px 24px', borderTop: '1px solid #eee' },
  cancelBtn: { padding: '12px 24px', background: '#f5f5f5', border: 'none', borderRadius: '8px', fontSize: '15px', cursor: 'pointer' },
  saveBtn: { padding: '12px 24px', background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: 'white', border: 'none', borderRadius: '8px', fontSize: '15px', fontWeight: '600', cursor: 'pointer' },
  generateContent: { flex: 1, overflow: 'auto', padding: '24px' },
  errorBox: { display: 'flex', alignItems: 'center', gap: '10px', padding: '12px 16px', background: '#fef2f2', color: '#dc2626', borderRadius: '8px', fontSize: '14px', marginBottom: '20px' },
  selectFull: { padding: '12px 14px', fontSize: '15px', border: '1px solid #ddd', borderRadius: '8px', outline: 'none', width: '100%' },
  leadsSection: { marginTop: '20px' },
  leadsHeader: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' },
  selectAllBtn: { padding: '8px 16px', background: '#f5f5f5', border: 'none', borderRadius: '6px', fontSize: '14px', cursor: 'pointer' },
  leadsList: { display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '300px', overflowY: 'auto' },
  leadItem: { display: 'flex', alignItems: 'center', gap: '12px', padding: '12px 16px', border: '1px solid #e0e0e0', borderRadius: '8px', cursor: 'pointer', transition: 'all 0.2s' },
  generateFooter: { display: 'flex', justifyContent: 'flex-end', gap: '12px', padding: '20px 24px', borderTop: '1px solid #eee' },
  generateBtn2: { padding: '12px 24px', background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: 'white', border: 'none', borderRadius: '8px', fontSize: '15px', fontWeight: '600', cursor: 'pointer' },
};

export default Emails;
