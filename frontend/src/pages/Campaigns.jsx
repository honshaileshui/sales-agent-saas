// Campaigns Page Component
import { useState, useEffect } from 'react';
import { 
  Plus, Search, Filter, Play, Pause, Trash2, Eye, 
  Users, Mail, Calendar, Target, ChevronRight, X, Check,
  Megaphone, TrendingUp, AlertCircle
} from 'lucide-react';
import { campaignsAPI, leadsAPI } from '../api';

function Campaigns() {
  const [campaigns, setCampaigns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showWizard, setShowWizard] = useState(false);
  const [selectedCampaign, setSelectedCampaign] = useState(null);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [statusFilter, setStatusFilter] = useState('');
  const [search, setSearch] = useState('');

  useEffect(() => {
    fetchCampaigns();
  }, [statusFilter]);

  const fetchCampaigns = async () => {
    setLoading(true);
    try {
      const params = {};
      if (statusFilter) params.status = statusFilter;
      if (search) params.search = search;
      
      const response = await campaignsAPI.getAll(params);
      setCampaigns(response.data.campaigns || response.data || []);
    } catch (err) {
      console.error('Failed to fetch campaigns:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    fetchCampaigns();
  };

  const handleStartCampaign = async (id) => {
    try {
      await campaignsAPI.start(id);
      setCampaigns(campaigns.map(c => 
        c.id === id ? { ...c, status: 'active' } : c
      ));
    } catch (err) {
      alert('Failed to start campaign');
    }
  };

  const handlePauseCampaign = async (id) => {
    try {
      await campaignsAPI.pause(id);
      setCampaigns(campaigns.map(c => 
        c.id === id ? { ...c, status: 'paused' } : c
      ));
    } catch (err) {
      alert('Failed to pause campaign');
    }
  };

  const handleDeleteCampaign = async (id) => {
    if (!window.confirm('Are you sure you want to delete this campaign?')) return;
    try {
      await campaignsAPI.delete(id);
      setCampaigns(campaigns.filter(c => c.id !== id));
    } catch (err) {
      alert('Failed to delete campaign');
    }
  };

  const handleViewCampaign = (campaign) => {
    setSelectedCampaign(campaign);
    setShowDetailModal(true);
  };

  const handleWizardComplete = () => {
    setShowWizard(false);
    fetchCampaigns();
  };

  const getStatusColor = (status) => {
    const colors = {
      draft: { bg: '#f3f4f6', text: '#6b7280' },
      active: { bg: '#d1fae5', text: '#059669' },
      paused: { bg: '#fef3c7', text: '#d97706' },
      completed: { bg: '#e0e7ff', text: '#4338ca' },
    };
    return colors[status] || colors.draft;
  };

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <div>
          <h1 style={styles.title}>Campaigns</h1>
          <p style={styles.subtitle}>Manage your email outreach campaigns</p>
        </div>
        <button style={styles.createBtn} onClick={() => setShowWizard(true)}>
          <Plus size={20} />
          Create Campaign
        </button>
      </div>

      {/* Stats Cards */}
      <div style={styles.statsGrid}>
        <div style={styles.statCard}>
          <div style={{...styles.statIcon, backgroundColor: '#667eea15'}}>
            <Megaphone size={24} color="#667eea" />
          </div>
          <div>
            <p style={styles.statValue}>{campaigns.length}</p>
            <p style={styles.statLabel}>Total Campaigns</p>
          </div>
        </div>
        <div style={styles.statCard}>
          <div style={{...styles.statIcon, backgroundColor: '#10b98115'}}>
            <Play size={24} color="#10b981" />
          </div>
          <div>
            <p style={styles.statValue}>{campaigns.filter(c => c.status === 'active').length}</p>
            <p style={styles.statLabel}>Active</p>
          </div>
        </div>
        <div style={styles.statCard}>
          <div style={{...styles.statIcon, backgroundColor: '#f59e0b15'}}>
            <Pause size={24} color="#f59e0b" />
          </div>
          <div>
            <p style={styles.statValue}>{campaigns.filter(c => c.status === 'paused').length}</p>
            <p style={styles.statLabel}>Paused</p>
          </div>
        </div>
        <div style={styles.statCard}>
          <div style={{...styles.statIcon, backgroundColor: '#8b5cf615'}}>
            <Check size={24} color="#8b5cf6" />
          </div>
          <div>
            <p style={styles.statValue}>{campaigns.filter(c => c.status === 'completed').length}</p>
            <p style={styles.statLabel}>Completed</p>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div style={styles.filters}>
        <form onSubmit={handleSearch} style={styles.searchBox}>
          <Search size={20} color="#999" />
          <input
            type="text"
            placeholder="Search campaigns..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={styles.searchInput}
          />
        </form>
        <div style={styles.filterGroup}>
          <Filter size={18} color="#666" />
          <select 
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            style={styles.select}
          >
            <option value="">All Status</option>
            <option value="draft">Draft</option>
            <option value="active">Active</option>
            <option value="paused">Paused</option>
            <option value="completed">Completed</option>
          </select>
        </div>
      </div>

      {/* Campaigns List */}
      {loading ? (
        <div style={styles.loading}>Loading campaigns...</div>
      ) : campaigns.length === 0 ? (
        <div style={styles.empty}>
          <Megaphone size={64} color="#ddd" />
          <h3 style={styles.emptyTitle}>No campaigns yet</h3>
          <p style={styles.emptyText}>Create your first campaign to start reaching out to leads</p>
          <button style={styles.emptyBtn} onClick={() => setShowWizard(true)}>
            <Plus size={20} />
            Create Your First Campaign
          </button>
        </div>
      ) : (
        <div style={styles.campaignsGrid}>
          {campaigns.map((campaign) => (
            <div key={campaign.id} style={styles.campaignCard}>
              <div style={styles.cardHeader}>
                <span style={{
                  ...styles.statusBadge,
                  backgroundColor: getStatusColor(campaign.status).bg,
                  color: getStatusColor(campaign.status).text
                }}>
                  {campaign.status}
                </span>
                <div style={styles.cardActions}>
                  {(campaign.status === 'draft' || campaign.status === 'paused') && (
                    <button style={styles.actionBtn} onClick={() => handleStartCampaign(campaign.id)} title="Start">
                      <Play size={18} />
                    </button>
                  )}
                  {campaign.status === 'active' && (
                    <button style={styles.actionBtn} onClick={() => handlePauseCampaign(campaign.id)} title="Pause">
                      <Pause size={18} />
                    </button>
                  )}
                  <button style={{...styles.actionBtn, color: '#ef4444'}} onClick={() => handleDeleteCampaign(campaign.id)} title="Delete">
                    <Trash2 size={18} />
                  </button>
                </div>
              </div>
              <h3 style={styles.cardTitle}>{campaign.name}</h3>
              <p style={styles.cardDesc}>{campaign.description || 'No description'}</p>
              <div style={styles.cardStats}>
                <div style={styles.cardStat}>
                  <Users size={16} color="#666" />
                  <span>{campaign.lead_count || 0} leads</span>
                </div>
                <div style={styles.cardStat}>
                  <Mail size={16} color="#666" />
                  <span>{campaign.email_count || 0} emails</span>
                </div>
              </div>
              <div style={styles.cardMeta}>
                <Calendar size={14} color="#999" />
                <span>{new Date(campaign.created_at).toLocaleDateString()}</span>
              </div>
              <button style={styles.viewBtn} onClick={() => handleViewCampaign(campaign)}>
                View Details <ChevronRight size={18} />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Campaign Wizard Modal */}
      {showWizard && (
        <CampaignWizard 
          onClose={() => setShowWizard(false)}
          onComplete={handleWizardComplete}
        />
      )}

      {/* Campaign Detail Modal */}
      {showDetailModal && selectedCampaign && (
        <CampaignDetailModal 
          campaign={selectedCampaign}
          onClose={() => setShowDetailModal(false)}
        />
      )}
    </div>
  );
}

// Campaign Wizard Component
function CampaignWizard({ onClose, onComplete }) {
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    template: 'default',
    daily_limit: 50,
    send_time: '09:00',
    selectedLeads: [],
  });
  const [leads, setLeads] = useState([]);
  const [loadingLeads, setLoadingLeads] = useState(false);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (step === 2) fetchLeads();
  }, [step]);

  const fetchLeads = async () => {
    setLoadingLeads(true);
    try {
      const response = await leadsAPI.getAll({ status: 'new', per_page: 100 });
      setLeads(response.data.leads || response.data || []);
    } catch (err) {
      console.error('Failed to fetch leads:', err);
    } finally {
      setLoadingLeads(false);
    }
  };

  const handleNext = () => {
    if (step === 1 && !formData.name.trim()) {
      setError('Campaign name is required');
      return;
    }
    setError('');
    setStep(step + 1);
  };

  const handleSelectLead = (id) => {
    setFormData(prev => ({
      ...prev,
      selectedLeads: prev.selectedLeads.includes(id)
        ? prev.selectedLeads.filter(x => x !== id)
        : [...prev.selectedLeads, id]
    }));
  };

  const handleSelectAll = () => {
    setFormData(prev => ({
      ...prev,
      selectedLeads: prev.selectedLeads.length === leads.length ? [] : leads.map(l => l.id)
    }));
  };

  const handleCreate = async () => {
    if (formData.selectedLeads.length === 0) {
      setError('Please select at least one lead');
      return;
    }
    setCreating(true);
    setError('');
    try {
      await campaignsAPI.create({
        name: formData.name,
        description: formData.description,
        template: formData.template,
        settings: { daily_limit: formData.daily_limit, send_time: formData.send_time },
        lead_ids: formData.selectedLeads,
      });
      onComplete();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create campaign');
    } finally {
      setCreating(false);
    }
  };

  const templates = [
    { id: 'default', name: 'Default', desc: 'Standard professional outreach' },
    { id: 'friendly', name: 'Friendly', desc: 'Casual, conversational tone' },
    { id: 'direct', name: 'Direct', desc: 'Straight to the point' },
    { id: 'value', name: 'Value-First', desc: 'Lead with value proposition' },
  ];

  return (
    <div style={styles.modalOverlay} onClick={onClose}>
      <div style={styles.wizardModal} onClick={e => e.stopPropagation()}>
        <div style={styles.wizardHeader}>
          <h2 style={styles.wizardTitle}>Create Campaign</h2>
          <button style={styles.closeBtn} onClick={onClose}><X size={24} /></button>
        </div>

        {/* Progress */}
        <div style={styles.stepProgress}>
          {['Details', 'Select Leads', 'Review'].map((label, i) => (
            <div key={i} style={styles.stepItem}>
              <div style={{
                ...styles.stepCircle,
                backgroundColor: step > i + 1 ? '#10b981' : step === i + 1 ? '#667eea' : '#e0e0e0',
                color: step >= i + 1 ? 'white' : '#999'
              }}>
                {step > i + 1 ? <Check size={16} /> : i + 1}
              </div>
              <span style={{...styles.stepLabel, color: step >= i + 1 ? '#333' : '#999'}}>{label}</span>
            </div>
          ))}
        </div>

        <div style={styles.wizardContent}>
          {error && <div style={styles.errorBox}><AlertCircle size={20} />{error}</div>}

          {/* Step 1: Details */}
          {step === 1 && (
            <div style={styles.stepContent}>
              <div style={styles.formGroup}>
                <label style={styles.label}>Campaign Name *</label>
                <input type="text" value={formData.name} onChange={(e) => setFormData({...formData, name: e.target.value})} style={styles.input} placeholder="e.g., Q1 SaaS Outreach" />
              </div>
              <div style={styles.formGroup}>
                <label style={styles.label}>Description</label>
                <textarea value={formData.description} onChange={(e) => setFormData({...formData, description: e.target.value})} style={styles.textarea} placeholder="Brief description..." rows={3} />
              </div>
              <div style={styles.formGroup}>
                <label style={styles.label}>Email Template</label>
                <div style={styles.templateGrid}>
                  {templates.map((t) => (
                    <div key={t.id} style={{...styles.templateCard, borderColor: formData.template === t.id ? '#667eea' : '#e0e0e0', backgroundColor: formData.template === t.id ? '#f0f4ff' : 'white'}} onClick={() => setFormData({...formData, template: t.id})}>
                      <strong>{t.name}</strong>
                      <span style={{fontSize: '13px', color: '#666'}}>{t.desc}</span>
                    </div>
                  ))}
                </div>
              </div>
              <div style={styles.formRow}>
                <div style={styles.formGroup}>
                  <label style={styles.label}>Daily Send Limit</label>
                  <input type="number" value={formData.daily_limit} onChange={(e) => setFormData({...formData, daily_limit: parseInt(e.target.value) || 0})} style={styles.input} min={1} max={200} />
                </div>
                <div style={styles.formGroup}>
                  <label style={styles.label}>Send Time</label>
                  <input type="time" value={formData.send_time} onChange={(e) => setFormData({...formData, send_time: e.target.value})} style={styles.input} />
                </div>
              </div>
            </div>
          )}

          {/* Step 2: Select Leads */}
          {step === 2 && (
            <div style={styles.stepContent}>
              <div style={styles.leadsHeader}>
                <div>
                  <h3 style={{margin: 0, fontSize: '16px'}}>Select Leads</h3>
                  <p style={{margin: '4px 0 0', color: '#666', fontSize: '14px'}}>{formData.selectedLeads.length} of {leads.length} selected</p>
                </div>
                <button style={styles.selectAllBtn} onClick={handleSelectAll}>
                  {formData.selectedLeads.length === leads.length ? 'Deselect All' : 'Select All'}
                </button>
              </div>
              {loadingLeads ? (
                <div style={{padding: '40px', textAlign: 'center', color: '#666'}}>Loading leads...</div>
              ) : leads.length === 0 ? (
                <div style={{padding: '40px', textAlign: 'center', color: '#666'}}>
                  <Users size={48} color="#ddd" />
                  <p>No new leads available. Import leads first.</p>
                </div>
              ) : (
                <div style={styles.leadsList}>
                  {leads.map((lead) => (
                    <div key={lead.id} style={{...styles.leadItem, backgroundColor: formData.selectedLeads.includes(lead.id) ? '#f0f4ff' : 'white', borderColor: formData.selectedLeads.includes(lead.id) ? '#667eea' : '#e0e0e0'}} onClick={() => handleSelectLead(lead.id)}>
                      <input type="checkbox" checked={formData.selectedLeads.includes(lead.id)} onChange={() => {}} style={{width: '18px', height: '18px'}} />
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
          )}

          {/* Step 3: Review */}
          {step === 3 && (
            <div style={styles.stepContent}>
              <h3 style={{fontSize: '18px', margin: '0 0 20px'}}>Review Campaign</h3>
              <div style={styles.reviewSection}>
                <div style={styles.reviewRow}><span>Campaign Name</span><span>{formData.name}</span></div>
                <div style={styles.reviewRow}><span>Description</span><span>{formData.description || 'None'}</span></div>
                <div style={styles.reviewRow}><span>Template</span><span>{templates.find(t => t.id === formData.template)?.name}</span></div>
                <div style={styles.reviewRow}><span>Daily Limit</span><span>{formData.daily_limit} emails/day</span></div>
                <div style={styles.reviewRow}><span>Send Time</span><span>{formData.send_time}</span></div>
                <div style={styles.reviewRow}><span>Selected Leads</span><span>{formData.selectedLeads.length} leads</span></div>
              </div>
              <div style={styles.reviewNote}>
                <AlertCircle size={18} color="#667eea" />
                <span>Campaign will be created in draft mode. You can start it anytime.</span>
              </div>
            </div>
          )}
        </div>

        <div style={styles.wizardFooter}>
          {step > 1 && <button style={styles.backBtn} onClick={() => setStep(step - 1)}>Back</button>}
          <div style={{marginLeft: 'auto', display: 'flex', gap: '12px'}}>
            <button style={styles.cancelBtn} onClick={onClose}>Cancel</button>
            {step < 3 ? (
              <button style={styles.nextBtn} onClick={handleNext}>Next <ChevronRight size={18} /></button>
            ) : (
              <button style={{...styles.nextBtn, opacity: creating ? 0.7 : 1}} onClick={handleCreate} disabled={creating}>
                {creating ? 'Creating...' : 'Create Campaign'}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// Campaign Detail Modal
function CampaignDetailModal({ campaign, onClose }) {
  const getStatusColor = (status) => {
    const colors = {
      draft: { bg: '#f3f4f6', text: '#6b7280' },
      active: { bg: '#d1fae5', text: '#059669' },
      paused: { bg: '#fef3c7', text: '#d97706' },
      completed: { bg: '#e0e7ff', text: '#4338ca' },
    };
    return colors[status] || colors.draft;
  };

  return (
    <div style={styles.modalOverlay} onClick={onClose}>
      <div style={styles.detailModal} onClick={e => e.stopPropagation()}>
        <div style={styles.detailHeader}>
          <div>
            <h2 style={{margin: '0 0 8px', fontSize: '20px'}}>{campaign.name}</h2>
            <span style={{...styles.statusBadge, backgroundColor: getStatusColor(campaign.status).bg, color: getStatusColor(campaign.status).text}}>
              {campaign.status}
            </span>
          </div>
          <button style={styles.closeBtn} onClick={onClose}><X size={24} /></button>
        </div>
        <div style={{padding: '24px'}}>
          {campaign.description && <p style={{color: '#666', marginBottom: '20px'}}>{campaign.description}</p>}
          <div style={styles.detailStats}>
            <div style={styles.detailStat}>
              <Users size={24} color="#667eea" />
              <div><span style={{fontSize: '24px', fontWeight: '700'}}>{campaign.lead_count || 0}</span><br/><span style={{color: '#666', fontSize: '13px'}}>Leads</span></div>
            </div>
            <div style={styles.detailStat}>
              <Mail size={24} color="#10b981" />
              <div><span style={{fontSize: '24px', fontWeight: '700'}}>{campaign.email_count || 0}</span><br/><span style={{color: '#666', fontSize: '13px'}}>Emails</span></div>
            </div>
            <div style={styles.detailStat}>
              <TrendingUp size={24} color="#f59e0b" />
              <div><span style={{fontSize: '24px', fontWeight: '700'}}>0%</span><br/><span style={{color: '#666', fontSize: '13px'}}>Open Rate</span></div>
            </div>
            <div style={styles.detailStat}>
              <Target size={24} color="#8b5cf6" />
              <div><span style={{fontSize: '24px', fontWeight: '700'}}>0%</span><br/><span style={{color: '#666', fontSize: '13px'}}>Reply Rate</span></div>
            </div>
          </div>
          <div style={{marginTop: '20px', background: '#f8f9fa', borderRadius: '8px', padding: '16px'}}>
            <div style={{display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid #e0e0e0'}}>
              <span style={{color: '#666'}}>Created</span>
              <span>{new Date(campaign.created_at).toLocaleDateString()}</span>
            </div>
            <div style={{display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid #e0e0e0'}}>
              <span style={{color: '#666'}}>Template</span>
              <span>{campaign.template || 'Default'}</span>
            </div>
            <div style={{display: 'flex', justifyContent: 'space-between', padding: '8px 0'}}>
              <span style={{color: '#666'}}>Daily Limit</span>
              <span>{campaign.settings?.daily_limit || 50} emails/day</span>
            </div>
          </div>
        </div>
        <div style={{padding: '16px 24px', borderTop: '1px solid #eee'}}>
          <button style={{width: '100%', padding: '12px', background: '#f5f5f5', border: 'none', borderRadius: '8px', cursor: 'pointer'}} onClick={onClose}>Close</button>
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
  createBtn: { display: 'flex', alignItems: 'center', gap: '8px', padding: '12px 24px', background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: 'white', border: 'none', borderRadius: '8px', fontSize: '15px', fontWeight: '500', cursor: 'pointer' },
  statsGrid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', marginBottom: '24px' },
  statCard: { background: 'white', borderRadius: '12px', padding: '20px', display: 'flex', alignItems: 'center', gap: '16px', boxShadow: '0 2px 8px rgba(0,0,0,0.08)' },
  statIcon: { width: '48px', height: '48px', borderRadius: '12px', display: 'flex', alignItems: 'center', justifyContent: 'center' },
  statValue: { fontSize: '24px', fontWeight: '700', color: '#1a1a2e', margin: 0 },
  statLabel: { fontSize: '13px', color: '#666', margin: 0 },
  filters: { display: 'flex', gap: '16px', marginBottom: '24px' },
  searchBox: { display: 'flex', alignItems: 'center', gap: '10px', padding: '10px 16px', background: 'white', borderRadius: '8px', border: '1px solid #e0e0e0', flex: '1', maxWidth: '400px' },
  searchInput: { border: 'none', outline: 'none', flex: '1', fontSize: '15px' },
  filterGroup: { display: 'flex', alignItems: 'center', gap: '8px', padding: '10px 16px', background: 'white', borderRadius: '8px', border: '1px solid #e0e0e0' },
  select: { border: 'none', outline: 'none', fontSize: '15px', background: 'transparent', cursor: 'pointer' },
  loading: { padding: '60px', textAlign: 'center', color: '#666' },
  empty: { background: 'white', borderRadius: '12px', padding: '80px 40px', textAlign: 'center', boxShadow: '0 2px 8px rgba(0,0,0,0.08)' },
  emptyTitle: { fontSize: '20px', fontWeight: '600', color: '#333', margin: '20px 0 8px' },
  emptyText: { color: '#666', margin: '0 0 24px' },
  emptyBtn: { display: 'inline-flex', alignItems: 'center', gap: '8px', padding: '12px 24px', background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: 'white', border: 'none', borderRadius: '8px', fontSize: '15px', cursor: 'pointer' },
  campaignsGrid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '20px' },
  campaignCard: { background: 'white', borderRadius: '12px', padding: '24px', boxShadow: '0 2px 8px rgba(0,0,0,0.08)', display: 'flex', flexDirection: 'column', gap: '12px' },
  cardHeader: { display: 'flex', justifyContent: 'space-between', alignItems: 'center' },
  statusBadge: { padding: '4px 12px', borderRadius: '20px', fontSize: '12px', fontWeight: '500', textTransform: 'capitalize' },
  cardActions: { display: 'flex', gap: '4px' },
  actionBtn: { background: 'none', border: 'none', padding: '6px', cursor: 'pointer', color: '#666', borderRadius: '6px' },
  cardTitle: { fontSize: '18px', fontWeight: '600', color: '#1a1a2e', margin: 0 },
  cardDesc: { fontSize: '14px', color: '#666', margin: 0, lineHeight: '1.5' },
  cardStats: { display: 'flex', gap: '20px' },
  cardStat: { display: 'flex', alignItems: 'center', gap: '6px', fontSize: '14px', color: '#666' },
  cardMeta: { display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px', color: '#999', paddingTop: '12px', borderTop: '1px solid #f0f0f0' },
  viewBtn: { display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px', padding: '10px', background: '#f5f5f5', border: 'none', borderRadius: '8px', fontSize: '14px', fontWeight: '500', color: '#333', cursor: 'pointer', marginTop: '8px' },
  modalOverlay: { position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000, padding: '20px' },
  wizardModal: { background: 'white', borderRadius: '16px', width: '100%', maxWidth: '700px', maxHeight: '90vh', display: 'flex', flexDirection: 'column' },
  wizardHeader: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '24px', borderBottom: '1px solid #eee' },
  wizardTitle: { fontSize: '20px', fontWeight: '600', margin: 0, color: '#1a1a2e' },
  closeBtn: { background: 'none', border: 'none', cursor: 'pointer', color: '#999', padding: '4px' },
  stepProgress: { display: 'flex', justifyContent: 'center', gap: '48px', padding: '20px', borderBottom: '1px solid #eee' },
  stepItem: { display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px' },
  stepCircle: { width: '32px', height: '32px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '14px', fontWeight: '600' },
  stepLabel: { fontSize: '13px', fontWeight: '500' },
  wizardContent: { flex: 1, overflow: 'auto', padding: '24px' },
  stepContent: { display: 'flex', flexDirection: 'column', gap: '20px' },
  errorBox: { display: 'flex', alignItems: 'center', gap: '10px', padding: '12px 16px', background: '#fef2f2', color: '#dc2626', borderRadius: '8px', fontSize: '14px' },
  formGroup: { display: 'flex', flexDirection: 'column', gap: '8px' },
  formRow: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' },
  label: { fontSize: '14px', fontWeight: '500', color: '#333' },
  input: { padding: '12px 14px', fontSize: '15px', border: '1px solid #ddd', borderRadius: '8px', outline: 'none' },
  textarea: { padding: '12px 14px', fontSize: '15px', border: '1px solid #ddd', borderRadius: '8px', outline: 'none', resize: 'vertical', fontFamily: 'inherit' },
  templateGrid: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' },
  templateCard: { padding: '16px', border: '2px solid #e0e0e0', borderRadius: '8px', cursor: 'pointer', display: 'flex', flexDirection: 'column', gap: '4px', transition: 'all 0.2s' },
  leadsHeader: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' },
  selectAllBtn: { padding: '8px 16px', background: '#f5f5f5', border: 'none', borderRadius: '6px', fontSize: '14px', cursor: 'pointer' },
  leadsList: { display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '300px', overflowY: 'auto' },
  leadItem: { display: 'flex', alignItems: 'center', gap: '12px', padding: '12px 16px', border: '1px solid #e0e0e0', borderRadius: '8px', cursor: 'pointer', transition: 'all 0.2s' },
  reviewSection: { background: '#f8f9fa', borderRadius: '8px', padding: '20px' },
  reviewRow: { display: 'flex', justifyContent: 'space-between', padding: '10px 0', borderBottom: '1px solid #e0e0e0' },
  reviewNote: { display: 'flex', alignItems: 'center', gap: '10px', padding: '16px', background: '#f0f4ff', borderRadius: '8px', fontSize: '14px', color: '#667eea', marginTop: '20px' },
  wizardFooter: { display: 'flex', padding: '20px 24px', borderTop: '1px solid #eee' },
  backBtn: { padding: '12px 24px', background: '#f5f5f5', border: 'none', borderRadius: '8px', fontSize: '15px', cursor: 'pointer' },
  cancelBtn: { padding: '12px 24px', background: '#f5f5f5', border: 'none', borderRadius: '8px', fontSize: '15px', cursor: 'pointer' },
  nextBtn: { display: 'flex', alignItems: 'center', gap: '6px', padding: '12px 24px', background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: 'white', border: 'none', borderRadius: '8px', fontSize: '15px', fontWeight: '600', cursor: 'pointer' },
  detailModal: { background: 'white', borderRadius: '16px', width: '100%', maxWidth: '600px', maxHeight: '90vh', overflow: 'auto' },
  detailHeader: { display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', padding: '24px', borderBottom: '1px solid #eee' },
  detailStats: { display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px' },
  detailStat: { display: 'flex', alignItems: 'center', gap: '12px', padding: '16px', background: '#f8f9fa', borderRadius: '8px' },
};

export default Campaigns;
