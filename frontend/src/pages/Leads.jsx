// Leads Page Component with CSV Import
import { useState, useEffect, useRef } from 'react';
import { Search, Filter, Plus, Trash2, Eye, Upload, X, FileText, CheckCircle, AlertCircle, Download } from 'lucide-react';
import { leadsAPI } from '../api';

function Leads() {
  const [leads, setLeads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [selectedLead, setSelectedLead] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [showImportModal, setShowImportModal] = useState(false);
  const [showAddModal, setShowAddModal] = useState(false);
  const [selectedLeads, setSelectedLeads] = useState([]);
  const [pagination, setPagination] = useState({ page: 1, total: 0, pages: 1 });

  useEffect(() => {
    fetchLeads();
  }, [statusFilter, pagination.page]);

  const fetchLeads = async () => {
    setLoading(true);
    try {
      const params = { page: pagination.page, per_page: 20 };
      if (statusFilter) params.status = statusFilter;
      if (search) params.search = search;
      
      const response = await leadsAPI.getAll(params);
      setLeads(response.data.leads || response.data);
      if (response.data.pagination) {
        setPagination(response.data.pagination);
      }
    } catch (err) {
      console.error('Failed to fetch leads:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    setPagination(prev => ({ ...prev, page: 1 }));
    fetchLeads();
  };

  const handleViewLead = (lead) => {
    setSelectedLead(lead);
    setShowModal(true);
  };

  const handleDeleteLead = async (id) => {
    if (!window.confirm('Are you sure you want to delete this lead?')) return;
    
    try {
      await leadsAPI.delete(id);
      setLeads(leads.filter(l => l.id !== id));
    } catch (err) {
      alert('Failed to delete lead');
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

  const handleBulkDelete = async () => {
    if (!selectedLeads.length) return;
    if (!window.confirm(`Delete ${selectedLeads.length} leads?`)) return;
    
    try {
      await leadsAPI.bulkDelete(selectedLeads);
      setLeads(leads.filter(l => !selectedLeads.includes(l.id)));
      setSelectedLeads([]);
    } catch (err) {
      alert('Failed to delete leads');
    }
  };

  const handleImportSuccess = (importedCount) => {
    setShowImportModal(false);
    fetchLeads();
  };

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <div>
          <h1 style={styles.title}>Leads</h1>
          <p style={styles.subtitle}>Manage your sales leads</p>
        </div>
        <div style={styles.headerActions}>
          <button style={styles.importBtn} onClick={() => setShowImportModal(true)}>
            <Upload size={20} />
            Import CSV
          </button>
          <button style={styles.addBtn} onClick={() => setShowAddModal(true)}>
            <Plus size={20} />
            Add Lead
          </button>
        </div>
      </div>

      {/* Bulk Actions */}
      {selectedLeads.length > 0 && (
        <div style={styles.bulkActions}>
          <span style={styles.bulkCount}>{selectedLeads.length} selected</span>
          <button style={styles.bulkDeleteBtn} onClick={handleBulkDelete}>
            <Trash2 size={16} />
            Delete Selected
          </button>
        </div>
      )}

      {/* Filters */}
      <div style={styles.filters}>
        <form onSubmit={handleSearch} style={styles.searchBox}>
          <Search size={20} color="#999" />
          <input
            type="text"
            placeholder="Search leads..."
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
            <option value="new">New</option>
            <option value="researched">Researched</option>
            <option value="email_drafted">Email Drafted</option>
            <option value="email_sent">Email Sent</option>
            <option value="replied">Replied</option>
            <option value="converted">Converted</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <div style={styles.tableContainer}>
        {loading ? (
          <div style={styles.loading}>Loading leads...</div>
        ) : (
          <table style={styles.table}>
            <thead>
              <tr style={styles.tableHeader}>
                <th style={styles.th}>
                  <input 
                    type="checkbox" 
                    checked={selectedLeads.length === leads.length && leads.length > 0}
                    onChange={handleSelectAll}
                    style={styles.checkbox}
                  />
                </th>
                <th style={styles.th}>Name</th>
                <th style={styles.th}>Company</th>
                <th style={styles.th}>Job Title</th>
                <th style={styles.th}>Status</th>
                <th style={styles.th}>Priority</th>
                <th style={styles.th}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {leads.map((lead) => (
                <tr key={lead.id} style={styles.tableRow}>
                  <td style={styles.td}>
                    <input 
                      type="checkbox"
                      checked={selectedLeads.includes(lead.id)}
                      onChange={() => handleSelectLead(lead.id)}
                      style={styles.checkbox}
                    />
                  </td>
                  <td style={styles.td}>
                    <strong>{lead.name}</strong>
                    <br />
                    <small style={{color: '#666'}}>{lead.email}</small>
                  </td>
                  <td style={styles.td}>{lead.company}</td>
                  <td style={styles.td}>{lead.job_title || '-'}</td>
                  <td style={styles.td}>
                    <span style={{
                      ...styles.badge,
                      backgroundColor: getStatusColor(lead.status).bg,
                      color: getStatusColor(lead.status).text
                    }}>
                      {lead.status}
                    </span>
                  </td>
                  <td style={styles.td}>
                    <span style={{
                      ...styles.priorityBadge,
                      backgroundColor: getPriorityColor(lead.priority)
                    }}>
                      {lead.priority}
                    </span>
                  </td>
                  <td style={styles.td}>
                    <div style={styles.actions}>
                      <button 
                        style={styles.iconBtn}
                        onClick={() => handleViewLead(lead)}
                        title="View"
                      >
                        <Eye size={18} />
                      </button>
                      <button 
                        style={{...styles.iconBtn, color: '#ef4444'}}
                        onClick={() => handleDeleteLead(lead.id)}
                        title="Delete"
                      >
                        <Trash2 size={18} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        {!loading && leads.length === 0 && (
          <div style={styles.empty}>
            <Upload size={48} color="#ccc" />
            <p>No leads found</p>
            <button 
              style={styles.emptyImportBtn}
              onClick={() => setShowImportModal(true)}
            >
              Import your first leads
            </button>
          </div>
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
          <span style={styles.pageInfo}>
            Page {pagination.page} of {pagination.pages}
          </span>
          <button 
            style={styles.pageBtn}
            disabled={pagination.page === pagination.pages}
            onClick={() => setPagination(prev => ({ ...prev, page: prev.page + 1 }))}
          >
            Next
          </button>
        </div>
      )}

      {/* Lead Detail Modal */}
      {showModal && selectedLead && (
        <LeadDetailModal 
          lead={selectedLead} 
          onClose={() => setShowModal(false)} 
        />
      )}

      {/* CSV Import Modal */}
      {showImportModal && (
        <CSVImportModal 
          onClose={() => setShowImportModal(false)}
          onSuccess={handleImportSuccess}
        />
      )}

      {/* Add Lead Modal */}
      {showAddModal && (
        <AddLeadModal 
          onClose={() => setShowAddModal(false)}
          onSuccess={() => {
            setShowAddModal(false);
            fetchLeads();
          }}
        />
      )}
    </div>
  );
}

// CSV Import Modal Component
function CSVImportModal({ onClose, onSuccess }) {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef(null);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleFile = (selectedFile) => {
    if (!selectedFile.name.endsWith('.csv')) {
      setError('Please upload a CSV file');
      return;
    }
    setFile(selectedFile);
    setError('');
    setResult(null);
  };

  const handleUpload = async () => {
    if (!file) return;
    
    setUploading(true);
    setProgress(0);
    setError('');
    
    try {
      const response = await leadsAPI.importCSV(file, (percent) => {
        setProgress(percent);
      });
      
      setResult(response.data);
      setTimeout(() => {
        onSuccess(response.data.imported);
      }, 2000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to import CSV. Please check the file format.');
    } finally {
      setUploading(false);
    }
  };

  const downloadTemplate = () => {
    const template = 'name,email,company,job_title,linkedin_url,priority\nJohn Doe,john@example.com,Acme Inc,CEO,https://linkedin.com/in/johndoe,high\nJane Smith,jane@example.com,TechCorp,CTO,https://linkedin.com/in/janesmith,medium';
    const blob = new Blob([template], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'leads_template.csv';
    a.click();
  };

  return (
    <div style={styles.modalOverlay} onClick={onClose}>
      <div style={styles.importModal} onClick={e => e.stopPropagation()}>
        <div style={styles.modalHeader}>
          <h2 style={styles.modalTitle}>Import Leads from CSV</h2>
          <button style={styles.closeBtn} onClick={onClose}>
            <X size={24} />
          </button>
        </div>

        {result ? (
          <div style={styles.resultContainer}>
            <CheckCircle size={64} color="#10b981" />
            <h3 style={styles.resultTitle}>Import Successful!</h3>
            <div style={styles.resultStats}>
              <div style={styles.resultStat}>
                <span style={styles.resultNumber}>{result.imported}</span>
                <span style={styles.resultLabel}>Leads Imported</span>
              </div>
              {result.skipped > 0 && (
                <div style={styles.resultStat}>
                  <span style={{...styles.resultNumber, color: '#f59e0b'}}>{result.skipped}</span>
                  <span style={styles.resultLabel}>Skipped (duplicates)</span>
                </div>
              )}
              {result.failed > 0 && (
                <div style={styles.resultStat}>
                  <span style={{...styles.resultNumber, color: '#ef4444'}}>{result.failed}</span>
                  <span style={styles.resultLabel}>Failed</span>
                </div>
              )}
            </div>
          </div>
        ) : (
          <>
            <div 
              style={{
                ...styles.dropZone,
                borderColor: dragActive ? '#667eea' : '#ddd',
                background: dragActive ? '#f0f4ff' : '#fafafa'
              }}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
            >
              <input
                type="file"
                ref={fileInputRef}
                onChange={(e) => handleFile(e.target.files[0])}
                accept=".csv"
                style={{ display: 'none' }}
              />
              
              {file ? (
                <div style={styles.fileInfo}>
                  <FileText size={48} color="#667eea" />
                  <p style={styles.fileName}>{file.name}</p>
                  <p style={styles.fileSize}>{(file.size / 1024).toFixed(1)} KB</p>
                </div>
              ) : (
                <>
                  <Upload size={48} color="#999" />
                  <p style={styles.dropText}>
                    Drag & drop your CSV file here, or click to browse
                  </p>
                  <p style={styles.dropHint}>
                    Supports: .csv files with name, email, company columns
                  </p>
                </>
              )}
            </div>

            {error && (
              <div style={styles.errorBox}>
                <AlertCircle size={20} />
                {error}
              </div>
            )}

            {uploading && (
              <div style={styles.progressContainer}>
                <div style={styles.progressBar}>
                  <div style={{...styles.progressFill, width: `${progress}%`}} />
                </div>
                <p style={styles.progressText}>Uploading... {progress}%</p>
              </div>
            )}

            <div style={styles.modalActions}>
              <button style={styles.templateBtn} onClick={downloadTemplate}>
                <Download size={18} />
                Download Template
              </button>
              <button 
                style={{
                  ...styles.uploadBtn,
                  opacity: !file || uploading ? 0.5 : 1,
                  cursor: !file || uploading ? 'not-allowed' : 'pointer'
                }}
                onClick={handleUpload}
                disabled={!file || uploading}
              >
                {uploading ? 'Importing...' : 'Import Leads'}
              </button>
            </div>

            <div style={styles.csvHelp}>
              <h4 style={styles.helpTitle}>Required CSV Columns:</h4>
              <ul style={styles.helpList}>
                <li><code>name</code> - Full name of the lead</li>
                <li><code>email</code> - Email address (required, unique)</li>
                <li><code>company</code> - Company name</li>
              </ul>
              <h4 style={styles.helpTitle}>Optional Columns:</h4>
              <ul style={styles.helpList}>
                <li><code>job_title</code> - Job title/position</li>
                <li><code>linkedin_url</code> - LinkedIn profile URL</li>
                <li><code>priority</code> - high, medium, or low</li>
                <li><code>phone</code> - Phone number</li>
                <li><code>company_website</code> - Company website URL</li>
              </ul>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

// Add Lead Modal Component
function AddLeadModal({ onClose, onSuccess }) {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    company: '',
    job_title: '',
    linkedin_url: '',
    priority: 'medium'
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      await leadsAPI.create(formData);
      onSuccess();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create lead');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.modalOverlay} onClick={onClose}>
      <div style={styles.addModal} onClick={e => e.stopPropagation()}>
        <div style={styles.modalHeader}>
          <h2 style={styles.modalTitle}>Add New Lead</h2>
          <button style={styles.closeBtn} onClick={onClose}>
            <X size={24} />
          </button>
        </div>

        <form onSubmit={handleSubmit} style={styles.addForm}>
          {error && <div style={styles.errorBox}><AlertCircle size={20} />{error}</div>}
          
          <div style={styles.formRow}>
            <div style={styles.formGroup}>
              <label style={styles.label}>Name *</label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({...formData, name: e.target.value})}
                style={styles.input}
                required
              />
            </div>
            <div style={styles.formGroup}>
              <label style={styles.label}>Email *</label>
              <input
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({...formData, email: e.target.value})}
                style={styles.input}
                required
              />
            </div>
          </div>

          <div style={styles.formRow}>
            <div style={styles.formGroup}>
              <label style={styles.label}>Company *</label>
              <input
                type="text"
                value={formData.company}
                onChange={(e) => setFormData({...formData, company: e.target.value})}
                style={styles.input}
                required
              />
            </div>
            <div style={styles.formGroup}>
              <label style={styles.label}>Job Title</label>
              <input
                type="text"
                value={formData.job_title}
                onChange={(e) => setFormData({...formData, job_title: e.target.value})}
                style={styles.input}
              />
            </div>
          </div>

          <div style={styles.formRow}>
            <div style={styles.formGroup}>
              <label style={styles.label}>LinkedIn URL</label>
              <input
                type="url"
                value={formData.linkedin_url}
                onChange={(e) => setFormData({...formData, linkedin_url: e.target.value})}
                style={styles.input}
                placeholder="https://linkedin.com/in/..."
              />
            </div>
            <div style={styles.formGroup}>
              <label style={styles.label}>Priority</label>
              <select
                value={formData.priority}
                onChange={(e) => setFormData({...formData, priority: e.target.value})}
                style={styles.input}
              >
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
              </select>
            </div>
          </div>

          <div style={styles.formActions}>
            <button type="button" style={styles.cancelBtn} onClick={onClose}>
              Cancel
            </button>
            <button 
              type="submit" 
              style={{...styles.submitBtn, opacity: loading ? 0.7 : 1}}
              disabled={loading}
            >
              {loading ? 'Creating...' : 'Create Lead'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// Lead Detail Modal Component
function LeadDetailModal({ lead, onClose }) {
  return (
    <div style={styles.modalOverlay} onClick={onClose}>
      <div style={styles.detailModal} onClick={e => e.stopPropagation()}>
        <div style={styles.modalHeader}>
          <h2 style={styles.modalTitle}>{lead.name}</h2>
          <button style={styles.closeBtn} onClick={onClose}>
            <X size={24} />
          </button>
        </div>
        <div style={styles.detailContent}>
          <div style={styles.detailRow}>
            <span style={styles.detailLabel}>Email</span>
            <span style={styles.detailValue}>{lead.email}</span>
          </div>
          <div style={styles.detailRow}>
            <span style={styles.detailLabel}>Company</span>
            <span style={styles.detailValue}>{lead.company}</span>
          </div>
          <div style={styles.detailRow}>
            <span style={styles.detailLabel}>Job Title</span>
            <span style={styles.detailValue}>{lead.job_title || 'N/A'}</span>
          </div>
          <div style={styles.detailRow}>
            <span style={styles.detailLabel}>Status</span>
            <span style={{
              ...styles.badge,
              backgroundColor: getStatusColor(lead.status).bg,
              color: getStatusColor(lead.status).text
            }}>
              {lead.status}
            </span>
          </div>
          <div style={styles.detailRow}>
            <span style={styles.detailLabel}>Priority</span>
            <span style={{
              ...styles.priorityBadge,
              backgroundColor: getPriorityColor(lead.priority)
            }}>
              {lead.priority}
            </span>
          </div>
          {lead.linkedin_url && (
            <div style={styles.detailRow}>
              <span style={styles.detailLabel}>LinkedIn</span>
              <a href={lead.linkedin_url} target="_blank" rel="noopener noreferrer" style={styles.link}>
                View Profile →
              </a>
            </div>
          )}
          <div style={styles.detailRow}>
            <span style={styles.detailLabel}>Created</span>
            <span style={styles.detailValue}>
              {new Date(lead.created_at).toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'long',
                day: 'numeric'
              })}
            </span>
          </div>
        </div>
        <div style={styles.detailActions}>
          <button style={styles.closeModalBtn} onClick={onClose}>Close</button>
        </div>
      </div>
    </div>
  );
}

const getStatusColor = (status) => {
  const colors = {
    new: { bg: '#e0e7ff', text: '#4338ca' },
    researched: { bg: '#fef3c7', text: '#d97706' },
    email_drafted: { bg: '#d1fae5', text: '#059669' },
    email_sent: { bg: '#dbeafe', text: '#2563eb' },
    replied: { bg: '#f3e8ff', text: '#9333ea' },
    converted: { bg: '#dcfce7', text: '#16a34a' },
  };
  return colors[status] || { bg: '#f3f4f6', text: '#6b7280' };
};

const getPriorityColor = (priority) => {
  const colors = {
    high: '#fee2e2',
    medium: '#fef3c7',
    low: '#e0e7ff',
  };
  return colors[priority] || '#f3f4f6';
};

const styles = {
  container: {
    padding: '30px',
    maxWidth: '1400px',
    margin: '0 auto',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '24px',
  },
  title: {
    fontSize: '28px',
    fontWeight: '700',
    color: '#1a1a2e',
    margin: '0 0 8px 0',
  },
  subtitle: {
    color: '#666',
    margin: 0,
  },
  headerActions: {
    display: 'flex',
    gap: '12px',
  },
  importBtn: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    padding: '12px 24px',
    background: 'white',
    color: '#667eea',
    border: '2px solid #667eea',
    borderRadius: '8px',
    fontSize: '15px',
    fontWeight: '500',
    cursor: 'pointer',
  },
  addBtn: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    padding: '12px 24px',
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    color: 'white',
    border: 'none',
    borderRadius: '8px',
    fontSize: '15px',
    fontWeight: '500',
    cursor: 'pointer',
  },
  bulkActions: {
    display: 'flex',
    alignItems: 'center',
    gap: '16px',
    padding: '12px 20px',
    background: '#f0f4ff',
    borderRadius: '8px',
    marginBottom: '16px',
  },
  bulkCount: {
    fontSize: '14px',
    fontWeight: '600',
    color: '#667eea',
  },
  bulkDeleteBtn: {
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
    padding: '8px 16px',
    background: '#ef4444',
    color: 'white',
    border: 'none',
    borderRadius: '6px',
    fontSize: '14px',
    cursor: 'pointer',
  },
  filters: {
    display: 'flex',
    gap: '16px',
    marginBottom: '24px',
    flexWrap: 'wrap',
  },
  searchBox: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    padding: '10px 16px',
    background: 'white',
    borderRadius: '8px',
    border: '1px solid #e0e0e0',
    flex: '1',
    minWidth: '250px',
  },
  searchInput: {
    border: 'none',
    outline: 'none',
    flex: '1',
    fontSize: '15px',
  },
  filterGroup: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    padding: '10px 16px',
    background: 'white',
    borderRadius: '8px',
    border: '1px solid #e0e0e0',
  },
  select: {
    border: 'none',
    outline: 'none',
    fontSize: '15px',
    background: 'transparent',
    cursor: 'pointer',
  },
  tableContainer: {
    background: 'white',
    borderRadius: '12px',
    boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
    overflow: 'hidden',
  },
  loading: {
    padding: '60px',
    textAlign: 'center',
    color: '#666',
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse',
  },
  tableHeader: {
    background: '#f8f9fa',
  },
  th: {
    padding: '16px',
    textAlign: 'left',
    fontSize: '12px',
    fontWeight: '600',
    color: '#666',
    textTransform: 'uppercase',
    borderBottom: '1px solid #eee',
  },
  tableRow: {
    borderBottom: '1px solid #eee',
    transition: 'background 0.2s',
  },
  td: {
    padding: '16px',
    fontSize: '14px',
    color: '#333',
  },
  checkbox: {
    width: '18px',
    height: '18px',
    cursor: 'pointer',
  },
  badge: {
    padding: '4px 12px',
    borderRadius: '20px',
    fontSize: '12px',
    fontWeight: '500',
  },
  priorityBadge: {
    padding: '4px 12px',
    borderRadius: '20px',
    fontSize: '12px',
    fontWeight: '500',
    textTransform: 'capitalize',
  },
  actions: {
    display: 'flex',
    gap: '8px',
  },
  iconBtn: {
    background: 'none',
    border: 'none',
    padding: '8px',
    cursor: 'pointer',
    color: '#666',
    borderRadius: '6px',
    transition: 'background 0.2s',
  },
  empty: {
    padding: '80px 20px',
    textAlign: 'center',
    color: '#666',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: '16px',
  },
  emptyImportBtn: {
    padding: '12px 24px',
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    color: 'white',
    border: 'none',
    borderRadius: '8px',
    fontSize: '15px',
    cursor: 'pointer',
  },
  pagination: {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    gap: '16px',
    marginTop: '24px',
  },
  pageBtn: {
    padding: '10px 20px',
    background: 'white',
    border: '1px solid #ddd',
    borderRadius: '8px',
    cursor: 'pointer',
    fontSize: '14px',
  },
  pageInfo: {
    fontSize: '14px',
    color: '#666',
  },
  // Modal Styles
  modalOverlay: {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    background: 'rgba(0,0,0,0.5)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 1000,
    padding: '20px',
  },
  importModal: {
    background: 'white',
    borderRadius: '16px',
    width: '100%',
    maxWidth: '560px',
    maxHeight: '90vh',
    overflow: 'auto',
  },
  addModal: {
    background: 'white',
    borderRadius: '16px',
    width: '100%',
    maxWidth: '600px',
    maxHeight: '90vh',
    overflow: 'auto',
  },
  detailModal: {
    background: 'white',
    borderRadius: '16px',
    width: '100%',
    maxWidth: '480px',
    maxHeight: '90vh',
    overflow: 'auto',
  },
  modalHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '24px',
    borderBottom: '1px solid #eee',
  },
  modalTitle: {
    fontSize: '20px',
    fontWeight: '600',
    margin: 0,
    color: '#1a1a2e',
  },
  closeBtn: {
    background: 'none',
    border: 'none',
    cursor: 'pointer',
    color: '#999',
    padding: '4px',
  },
  dropZone: {
    margin: '24px',
    padding: '48px 24px',
    border: '2px dashed #ddd',
    borderRadius: '12px',
    textAlign: 'center',
    cursor: 'pointer',
    transition: 'all 0.2s',
  },
  dropText: {
    margin: '16px 0 8px',
    fontSize: '16px',
    color: '#333',
  },
  dropHint: {
    margin: 0,
    fontSize: '14px',
    color: '#999',
  },
  fileInfo: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: '8px',
  },
  fileName: {
    fontSize: '16px',
    fontWeight: '600',
    color: '#333',
    margin: 0,
  },
  fileSize: {
    fontSize: '14px',
    color: '#666',
    margin: 0,
  },
  errorBox: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    margin: '0 24px',
    padding: '12px 16px',
    background: '#fef2f2',
    color: '#dc2626',
    borderRadius: '8px',
    fontSize: '14px',
  },
  progressContainer: {
    margin: '0 24px',
  },
  progressBar: {
    height: '8px',
    background: '#e0e0e0',
    borderRadius: '4px',
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    transition: 'width 0.3s',
  },
  progressText: {
    marginTop: '8px',
    fontSize: '14px',
    color: '#666',
    textAlign: 'center',
  },
  modalActions: {
    display: 'flex',
    justifyContent: 'space-between',
    padding: '0 24px 24px',
    gap: '12px',
  },
  templateBtn: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    padding: '12px 20px',
    background: '#f5f5f5',
    color: '#666',
    border: 'none',
    borderRadius: '8px',
    fontSize: '14px',
    cursor: 'pointer',
  },
  uploadBtn: {
    padding: '12px 32px',
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    color: 'white',
    border: 'none',
    borderRadius: '8px',
    fontSize: '15px',
    fontWeight: '600',
    cursor: 'pointer',
  },
  csvHelp: {
    padding: '0 24px 24px',
    borderTop: '1px solid #eee',
    marginTop: '16px',
    paddingTop: '20px',
  },
  helpTitle: {
    fontSize: '14px',
    fontWeight: '600',
    color: '#333',
    margin: '0 0 8px 0',
  },
  helpList: {
    margin: '0 0 16px 0',
    paddingLeft: '20px',
    fontSize: '13px',
    color: '#666',
    lineHeight: '1.8',
  },
  resultContainer: {
    padding: '48px 24px',
    textAlign: 'center',
  },
  resultTitle: {
    fontSize: '24px',
    fontWeight: '600',
    color: '#1a1a2e',
    margin: '24px 0',
  },
  resultStats: {
    display: 'flex',
    justifyContent: 'center',
    gap: '32px',
  },
  resultStat: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
  },
  resultNumber: {
    fontSize: '36px',
    fontWeight: '700',
    color: '#10b981',
  },
  resultLabel: {
    fontSize: '14px',
    color: '#666',
    marginTop: '4px',
  },
  // Add Lead Form Styles
  addForm: {
    padding: '24px',
    display: 'flex',
    flexDirection: 'column',
    gap: '20px',
  },
  formRow: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: '16px',
  },
  formGroup: {
    display: 'flex',
    flexDirection: 'column',
    gap: '6px',
  },
  label: {
    fontSize: '14px',
    fontWeight: '500',
    color: '#333',
  },
  input: {
    padding: '12px 14px',
    fontSize: '15px',
    border: '1px solid #ddd',
    borderRadius: '8px',
    outline: 'none',
    transition: 'border-color 0.2s',
  },
  formActions: {
    display: 'flex',
    justifyContent: 'flex-end',
    gap: '12px',
    marginTop: '12px',
  },
  cancelBtn: {
    padding: '12px 24px',
    background: '#f5f5f5',
    color: '#666',
    border: 'none',
    borderRadius: '8px',
    fontSize: '15px',
    cursor: 'pointer',
  },
  submitBtn: {
    padding: '12px 32px',
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    color: 'white',
    border: 'none',
    borderRadius: '8px',
    fontSize: '15px',
    fontWeight: '600',
    cursor: 'pointer',
  },
  // Detail Modal Styles
  detailContent: {
    padding: '24px',
  },
  detailRow: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '12px 0',
    borderBottom: '1px solid #f0f0f0',
  },
  detailLabel: {
    fontSize: '14px',
    color: '#666',
    fontWeight: '500',
  },
  detailValue: {
    fontSize: '14px',
    color: '#333',
  },
  link: {
    color: '#667eea',
    textDecoration: 'none',
    fontWeight: '500',
  },
  detailActions: {
    padding: '16px 24px',
    borderTop: '1px solid #eee',
  },
  closeModalBtn: {
    width: '100%',
    padding: '12px',
    background: '#f5f5f5',
    border: 'none',
    borderRadius: '8px',
    fontSize: '15px',
    cursor: 'pointer',
  },
};

export default Leads;
