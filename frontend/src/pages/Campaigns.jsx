// Campaigns Page Component - WITH SCHEDULE FUNCTIONALITY
import { useState, useEffect } from 'react';
import { 
  Plus, Search, Filter, Play, Pause, Trash2, Eye, 
  Users, Mail, Calendar, Target, ChevronRight, X, Check,
  Megaphone, TrendingUp, AlertCircle, Zap, Clock
} from 'lucide-react';
import { campaignsAPI, leadsAPI } from '../api';
import ScheduleForm from '../components/ScheduleForm';

function Campaigns() {
  const [campaigns, setCampaigns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showWizard, setShowWizard] = useState(false);
  const [selectedCampaign, setSelectedCampaign] = useState(null);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [statusFilter, setStatusFilter] = useState('');
  const [search, setSearch] = useState('');
  const [generating, setGenerating] = useState(false);
  const [generateProgress, setGenerateProgress] = useState(null);

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
      const campaignsData = response.campaigns || response.data?.campaigns || response.data || [];
      setCampaigns(Array.isArray(campaignsData) ? campaignsData : []);
    } catch (err) {
      console.error('Failed to fetch campaigns:', err);
      setCampaigns([]);
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

  const handleViewCampaign = async (campaign) => {
    // Fetch fresh campaign data with schedule
    try {
      const freshCampaign = await campaignsAPI.getById(campaign.id);
      setSelectedCampaign(freshCampaign);
      setShowDetailModal(true);
    } catch (err) {
      console.error('Failed to fetch campaign details:', err);
      setSelectedCampaign(campaign);
      setShowDetailModal(true);
    }
  };

  const handleWizardComplete = () => {
    setShowWizard(false);
    fetchCampaigns();
  };

  const handleGenerateEmails = async (campaignId) => {
    if (!window.confirm('Generate emails for all leads in this campaign?')) return;
    
    setGenerating(true);
    setGenerateProgress({ campaignId, status: 'generating' });
    
    try {
      const response = await fetch(`http://localhost:8000/api/campaigns/${campaignId}/generate-emails`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to generate emails');
      }
      
      const data = await response.json();
      
      setGenerateProgress({
        campaignId,
        status: 'complete',
        total: data.total_leads,
        successful: data.successful,
        failed: data.failed
      });
      
      alert(`✅ Generated ${data.successful} of ${data.total_leads} emails successfully!`);
      fetchCampaigns(); // Refresh campaign list
      
    } catch (err) {
      console.error('Failed to generate emails:', err);
      alert(`❌ ${err.message || 'Failed to generate emails'}`);
      setGenerateProgress(null);
    } finally {
      setGenerating(false);
    }
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

      {/* Progress Banner */}
      {generateProgress && (
        <div style={styles.progressBanner}>
          {generateProgress.status === 'generating' ? (
            <>
              <div style={styles.spinner}></div>
              <span>Generating emails for campaign...</span>
            </>
          ) : (
            <>
              <Check size={20} color="#10b981" />
              <span>
                ✅ Generated {generateProgress.successful} of {generateProgress.total} emails!
                {generateProgress.failed > 0 && ` (⚠️ ${generateProgress.failed} failed)`}
              </span>
              <button 
                onClick={() => setGenerateProgress(null)}
                style={styles.closeProgressBtn}
              >
                ×
              </button>
            </>
          )}
        </div>
      )}

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
          <Filter size={20} color="#666" />
          <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} style={styles.select}>
            <option value="">All Status</option>
            <option value="draft">Draft</option>
            <option value="active">Active</option>
            <option value="paused">Paused</option>
            <option value="completed">Completed</option>
          </select>
        </div>
      </div>

      {/* Loading / Empty / Campaigns */}
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
                  {/* GENERATE EMAILS BUTTON */}
                  <button 
                    style={{...styles.actionBtn, color: '#10b981'}} 
                    onClick={(e) => {
                      e.stopPropagation();
                      handleGenerateEmails(campaign.id);
                    }}
                    title="Generate Emails"
                    disabled={generating}
                  >
                    <Zap size={18} />
                  </button>
                  {/* Existing buttons */}
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
                  <span>{campaign.total_leads || 0} leads</span>
                </div>
                <div style={styles.cardStat}>
                  <Mail size={16} color="#666" />
                  <span>{campaign.emails_sent || 0} emails</span>
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
          onClose={() => {
            setShowDetailModal(false);
            setSelectedCampaign(null);
          }}
          onRefresh={() => {
            // Refresh the campaign data
            if (selectedCampaign?.id) {
              handleViewCampaign(selectedCampaign);
            }
            fetchCampaigns(); // Also refresh the list
          }}
        />
      )}
    </div>
  );
}

// Campaign Wizard Component (unchanged from original)
function CampaignWizard({ onClose, onComplete }) {
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    template: 'default',
    tone: 'professional',
    selectedLeads: [],
  });
  const [leads, setLeads] = useState([]);
  const [loadingLeads, setLoadingLeads] = useState(false);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (step === 3) fetchLeads();
  }, [step]);

  const fetchLeads = async () => {
    setLoadingLeads(true);
    try {
      const response = await leadsAPI.getAll({ status: 'new' });
      setLeads(response.data?.leads || response.data || []);
    } catch (err) {
      console.error('Failed to fetch leads:', err);
      setError('Failed to load leads');
    } finally {
      setLoadingLeads(false);
    }
  };

  const handleNext = () => {
    if (step === 1 && !formData.name.trim()) {
      setError('Campaign name is required');
      return;
    }
    if (step === 3 && formData.selectedLeads.length === 0) {
      setError('Please select at least one lead');
      return;
    }
    setError('');
    setStep(step + 1);
  };

  const handleBack = () => {
    setError('');
    setStep(step - 1);
  };

  const handleSubmit = async () => {
    setCreating(true);
    setError('');
    try {
      // Create campaign
      const campaignResponse = await campaignsAPI.create({
        name: formData.name,
        description: formData.description,
        template: formData.template,
        tone: formData.tone
      });

      const campaignId = campaignResponse.id;

      // Add leads to campaign
      if (formData.selectedLeads.length > 0) {
        await campaignsAPI.addLeads(campaignId, formData.selectedLeads);
      }

      alert(`✅ Campaign "${formData.name}" created successfully with ${formData.selectedLeads.length} leads!`);
      onComplete();
    } catch (err) {
      console.error('Failed to create campaign:', err);
      setError(err.response?.data?.detail || 'Failed to create campaign');
    } finally {
      setCreating(false);
    }
  };

  const toggleLead = (leadId) => {
    setFormData(prev => ({
      ...prev,
      selectedLeads: prev.selectedLeads.includes(leadId)
        ? prev.selectedLeads.filter(id => id !== leadId)
        : [...prev.selectedLeads, leadId]
    }));
  };

  const selectAllLeads = () => {
    setFormData(prev => ({
      ...prev,
      selectedLeads: prev.selectedLeads.length === leads.length ? [] : leads.map(l => l.id)
    }));
  };

  return (
    <div style={styles.modalOverlay} onClick={onClose}>
      <div style={styles.wizardModal} onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div style={styles.wizardHeader}>
          <h2 style={styles.wizardTitle}>Create New Campaign</h2>
          <button style={styles.closeBtn} onClick={onClose}><X size={24} /></button>
        </div>

        {/* Step Progress */}
        <div style={styles.stepProgress}>
          {[
            { num: 1, label: 'Details' },
            { num: 2, label: 'Template' },
            { num: 3, label: 'Select Leads' },
            { num: 4, label: 'Review' }
          ].map(s => (
            <div key={s.num} style={styles.stepItem}>
              <div style={{
                ...styles.stepCircle,
                backgroundColor: step >= s.num ? '#667eea' : '#f0f0f0',
                color: step >= s.num ? 'white' : '#999'
              }}>
                {s.num}
              </div>
              <span style={{
                ...styles.stepLabel,
                color: step >= s.num ? '#333' : '#999'
              }}>
                {s.label}
              </span>
            </div>
          ))}
        </div>

        {/* Content */}
        <div style={styles.wizardContent}>
          {error && (
            <div style={styles.errorBox}>
              <AlertCircle size={20} />
              {error}
            </div>
          )}

          {/* Step 1: Campaign Details */}
          {step === 1 && (
            <div style={styles.stepContent}>
              <div style={styles.formGroup}>
                <label style={styles.label}>Campaign Name *</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({...formData, name: e.target.value})}
                  placeholder="e.g., Q1 Outreach Campaign"
                  style={styles.input}
                  autoFocus
                />
              </div>
              <div style={styles.formGroup}>
                <label style={styles.label}>Description</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({...formData, description: e.target.value})}
                  placeholder="What is this campaign about?"
                  rows={4}
                  style={styles.textarea}
                />
              </div>
            </div>
          )}

          {/* Step 2: Template Selection */}
          {step === 2 && (
            <div style={styles.stepContent}>
              <div style={styles.formGroup}>
                <label style={styles.label}>Email Template</label>
                <div style={styles.templateGrid}>
                  {['default', 'professional', 'casual', 'brief'].map(template => (
                    <div
                      key={template}
                      onClick={() => setFormData({...formData, template})}
                      style={{
                        ...styles.templateCard,
                        borderColor: formData.template === template ? '#667eea' : '#e0e0e0',
                        backgroundColor: formData.template === template ? '#f0f4ff' : 'white'
                      }}
                    >
                      <strong style={{textTransform: 'capitalize'}}>{template}</strong>
                      <span style={{fontSize: '13px', color: '#666'}}>
                        {template === 'default' && 'Balanced and versatile'}
                        {template === 'professional' && 'Formal and detailed'}
                        {template === 'casual' && 'Friendly and conversational'}
                        {template === 'brief' && 'Short and to the point'}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
              <div style={styles.formGroup}>
                <label style={styles.label}>Tone</label>
                <select 
                  value={formData.tone} 
                  onChange={(e) => setFormData({...formData, tone: e.target.value})}
                  style={styles.input}
                >
                  <option value="professional">Professional</option>
                  <option value="friendly">Friendly</option>
                  <option value="enthusiastic">Enthusiastic</option>
                  <option value="formal">Formal</option>
                </select>
              </div>
            </div>
          )}

          {/* Step 3: Select Leads */}
          {step === 3 && (
            <div style={styles.stepContent}>
              <div style={styles.leadsHeader}>
                <h4 style={{margin: 0}}>Select Leads ({formData.selectedLeads.length} selected)</h4>
                <button onClick={selectAllLeads} style={styles.selectAllBtn}>
                  {formData.selectedLeads.length === leads.length ? 'Deselect All' : 'Select All'}
                </button>
              </div>
              {loadingLeads ? (
                <div style={{padding: '40px', textAlign: 'center', color: '#666'}}>Loading leads...</div>
              ) : leads.length === 0 ? (
                <div style={{padding: '40px', textAlign: 'center', color: '#666'}}>
                  No leads available. Please add leads first.
                </div>
              ) : (
                <div style={styles.leadsList}>
                  {leads.map(lead => (
                    <div
                      key={lead.id}
                      onClick={() => toggleLead(lead.id)}
                      style={{
                        ...styles.leadItem,
                        backgroundColor: formData.selectedLeads.includes(lead.id) ? '#f0f4ff' : 'white',
                        borderColor: formData.selectedLeads.includes(lead.id) ? '#667eea' : '#e0e0e0'
                      }}
                    >
                      <input
                        type="checkbox"
                        checked={formData.selectedLeads.includes(lead.id)}
                        onChange={() => {}}
                        style={{cursor: 'pointer'}}
                      />
                      <div style={{flex: 1}}>
                        <strong>{lead.name}</strong>
                        <div style={{fontSize: '13px', color: '#666'}}>
                          {lead.company} • {lead.email}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Step 4: Review */}
          {step === 4 && (
            <div style={styles.stepContent}>
              <h3 style={{marginTop: 0}}>Review Your Campaign</h3>
              <div style={styles.reviewSection}>
                <div style={styles.reviewRow}>
                  <span style={{fontWeight: '500'}}>Campaign Name:</span>
                  <span>{formData.name}</span>
                </div>
                <div style={styles.reviewRow}>
                  <span style={{fontWeight: '500'}}>Description:</span>
                  <span>{formData.description || 'None'}</span>
                </div>
                <div style={styles.reviewRow}>
                  <span style={{fontWeight: '500'}}>Template:</span>
                  <span style={{textTransform: 'capitalize'}}>{formData.template}</span>
                </div>
                <div style={styles.reviewRow}>
                  <span style={{fontWeight: '500'}}>Tone:</span>
                  <span style={{textTransform: 'capitalize'}}>{formData.tone}</span>
                </div>
                <div style={{...styles.reviewRow, borderBottom: 'none'}}>
                  <span style={{fontWeight: '500'}}>Leads:</span>
                  <span>{formData.selectedLeads.length} selected</span>
                </div>
              </div>
              <div style={styles.reviewNote}>
                <AlertCircle size={18} />
                Campaign will be created in <strong>draft</strong> status. You can generate emails and start it later.
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div style={{...styles.wizardFooter, justifyContent: step === 1 ? 'flex-end' : 'space-between'}}>
          {step > 1 && (
            <button onClick={handleBack} style={styles.backBtn} disabled={creating}>
              Back
            </button>
          )}
          <div style={{display: 'flex', gap: '12px', marginLeft: 'auto'}}>
            <button onClick={onClose} style={styles.cancelBtn} disabled={creating}>
              Cancel
            </button>
            {step < 4 ? (
              <button onClick={handleNext} style={styles.nextBtn}>
                Next <ChevronRight size={18} />
              </button>
            ) : (
              <button onClick={handleSubmit} style={styles.nextBtn} disabled={creating}>
                {creating ? 'Creating...' : 'Create Campaign'}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// Campaign Detail Modal - WITH SCHEDULE INTEGRATION
function CampaignDetailModal({ campaign, onClose, onRefresh }) {
  const [showScheduleForm, setShowScheduleForm] = useState(false);
  const [currentCampaign, setCurrentCampaign] = useState(campaign);

  const hasSchedule = currentCampaign.scheduled_start_date && currentCampaign.scheduled_start_time;

  const handleScheduleSave = async (data) => {
    console.log('Schedule saved:', data);
    setShowScheduleForm(false);
    
    // Refetch campaign data to get updated schedule
    try {
      const freshCampaign = await campaignsAPI.getById(campaign.id);
      setCurrentCampaign(freshCampaign);
      if (onRefresh) onRefresh();
    } catch (err) {
      console.error('Failed to refresh campaign:', err);
    }
  };

  const handleRemoveSchedule = async () => {
    if (!window.confirm('Are you sure you want to remove the schedule?')) return;
    
    try {
      const response = await fetch(`http://localhost:8000/api/campaigns/${campaign.id}/schedule`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      if (!response.ok) throw new Error('Failed to remove schedule');
      
      // Refresh campaign data
      const freshCampaign = await campaignsAPI.getById(campaign.id);
      setCurrentCampaign(freshCampaign);
      if (onRefresh) onRefresh();
      
      alert('✅ Schedule removed successfully');
    } catch (err) {
      alert('❌ Failed to remove schedule');
    }
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
    <div style={styles.modalOverlay} onClick={onClose}>
      <div style={styles.detailModal} onClick={e => e.stopPropagation()}>
        <div style={styles.detailHeader}>
          <div>
            <h2 style={{margin: '0 0 8px', fontSize: '20px'}}>{currentCampaign.name}</h2>
            <span style={{...styles.statusBadge, backgroundColor: getStatusColor(currentCampaign.status).bg, color: getStatusColor(currentCampaign.status).text}}>
              {currentCampaign.status}
            </span>
          </div>
          <button style={styles.closeBtn} onClick={onClose}><X size={24} /></button>
        </div>

        <div style={{padding: '24px'}}>
          {currentCampaign.description && <p style={{color: '#666', marginBottom: '20px'}}>{currentCampaign.description}</p>}
          
          {/* Stats Grid */}
          <div style={styles.detailStats}>
            <div style={styles.detailStat}>
              <Users size={24} color="#667eea" />
              <div><span style={{fontSize: '24px', fontWeight: '700'}}>{currentCampaign.total_leads || 0}</span><br/><span style={{color: '#666', fontSize: '13px'}}>Leads</span></div>
            </div>
            <div style={styles.detailStat}>
              <Mail size={24} color="#10b981" />
              <div><span style={{fontSize: '24px', fontWeight: '700'}}>{currentCampaign.emails_sent || 0}</span><br/><span style={{color: '#666', fontSize: '13px'}}>Emails</span></div>
            </div>
            <div style={styles.detailStat}>
              <TrendingUp size={24} color="#f59e0b" />
              <div><span style={{fontSize: '24px', fontWeight: '700'}}>{currentCampaign.emails_opened || 0}%</span><br/><span style={{color: '#666', fontSize: '13px'}}>Open Rate</span></div>
            </div>
            <div style={styles.detailStat}>
              <Target size={24} color="#8b5cf6" />
              <div><span style={{fontSize: '24px', fontWeight: '700'}}>{currentCampaign.replies_received || 0}%</span><br/><span style={{color: '#666', fontSize: '13px'}}>Reply Rate</span></div>
            </div>
          </div>

          {/* Schedule Section */}
          <div style={{marginTop: '24px', background: '#f8f9fa', borderRadius: '12px', padding: '20px'}}>
            <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px'}}>
              <h3 style={{margin: 0, display: 'flex', alignItems: 'center', gap: '8px'}}>
                <Clock size={20} color="#667eea" />
                Campaign Schedule
              </h3>
              {!showScheduleForm && (
                hasSchedule ? (
                  <div style={{display: 'flex', gap: '8px'}}>
                    <button 
                      onClick={() => setShowScheduleForm(true)}
                      style={{...styles.scheduleBtn, background: '#667eea', color: 'white'}}
                    >
                      Edit Schedule
                    </button>
                    <button 
                      onClick={handleRemoveSchedule}
                      style={{...styles.scheduleBtn, background: '#ef4444', color: 'white'}}
                    >
                      Remove
                    </button>
                  </div>
                ) : (
                  <button 
                    onClick={() => setShowScheduleForm(true)}
                    style={{...styles.scheduleBtn, background: '#667eea', color: 'white'}}
                  >
                    + Schedule Campaign
                  </button>
                )
              )}
            </div>

            {showScheduleForm ? (
              <ScheduleForm
                campaignId={currentCampaign.id}
                existingSchedule={hasSchedule ? {
                  scheduled_start_date: currentCampaign.scheduled_start_date,
                  scheduled_start_time: currentCampaign.scheduled_start_time,
                  timezone: currentCampaign.timezone,
                  daily_send_limit: currentCampaign.daily_send_limit
                } : null}
                onSave={handleScheduleSave}
                onCancel={() => setShowScheduleForm(false)}
              />
            ) : hasSchedule ? (
              <div style={{background: 'white', borderRadius: '8px', padding: '16px'}}>
                <div style={{display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px'}}>
                  <div>
                    <div style={{fontSize: '12px', color: '#666', marginBottom: '4px'}}>Start Date</div>
                    <div style={{fontWeight: '600'}}>{new Date(currentCampaign.scheduled_start_date).toLocaleDateString()}</div>
                  </div>
                  <div>
                    <div style={{fontSize: '12px', color: '#666', marginBottom: '4px'}}>Start Time</div>
                    <div style={{fontWeight: '600'}}>{currentCampaign.scheduled_start_time}</div>
                  </div>
                  <div>
                    <div style={{fontSize: '12px', color: '#666', marginBottom: '4px'}}>Timezone</div>
                    <div style={{fontWeight: '600'}}>{currentCampaign.timezone || 'UTC'}</div>
                  </div>
                  <div>
                    <div style={{fontSize: '12px', color: '#666', marginBottom: '4px'}}>Daily Limit</div>
                    <div style={{fontWeight: '600'}}>{currentCampaign.daily_send_limit || 50} emails/day</div>
                  </div>
                </div>
              </div>
            ) : (
              <div style={{textAlign: 'center', padding: '32px', color: '#999'}}>
                <Clock size={48} color="#ddd" style={{marginBottom: '12px'}} />
                <p style={{margin: 0}}>No schedule set</p>
                <p style={{margin: '4px 0 0', fontSize: '14px'}}>Click "Schedule Campaign" to set when emails should be sent</p>
              </div>
            )}
          </div>

          {/* Campaign Info */}
          <div style={{marginTop: '20px', background: '#f8f9fa', borderRadius: '8px', padding: '16px'}}>
            <div style={{display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid #e0e0e0'}}>
              <span style={{color: '#666'}}>Created</span>
              <span>{new Date(currentCampaign.created_at).toLocaleDateString()}</span>
            </div>
            <div style={{display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid #e0e0e0'}}>
              <span style={{color: '#666'}}>Template</span>
              <span style={{textTransform: 'capitalize'}}>{currentCampaign.template || 'Default'}</span>
            </div>
            <div style={{display: 'flex', justifyContent: 'space-between', padding: '8px 0'}}>
              <span style={{color: '#666'}}>Status</span>
              <span style={{textTransform: 'capitalize'}}>{currentCampaign.status}</span>
            </div>
          </div>
        </div>

        <div style={{padding: '16px 24px', borderTop: '1px solid #eee'}}>
          <button style={{width: '100%', padding: '12px', background: '#f5f5f5', border: 'none', borderRadius: '8px', cursor: 'pointer', fontWeight: '500'}} onClick={onClose}>Close</button>
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
  
  // Schedule button
  scheduleBtn: {
    padding: '8px 16px',
    border: 'none',
    borderRadius: '6px',
    fontSize: '14px',
    fontWeight: '500',
    cursor: 'pointer',
    transition: 'opacity 0.2s'
  },

  // PROGRESS BANNER
  progressBanner: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    padding: '16px 24px',
    background: '#f0fdf4',
    border: '1px solid #86efac',
    borderRadius: '8px',
    marginBottom: '20px',
    fontSize: '15px',
    color: '#166534'
  },
  closeProgressBtn: {
    marginLeft: 'auto',
    background: 'none',
    border: 'none',
    fontSize: '24px',
    cursor: 'pointer',
    color: '#166534',
    padding: '0 8px',
    lineHeight: 1
  },
  spinner: {
    width: '20px',
    height: '20px',
    border: '3px solid #d1fae5',
    borderTop: '3px solid #10b981',
    borderRadius: '50%',
    animation: 'spin 1s linear infinite'
  },
  
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
  campaignCard: { background: 'white', borderRadius: '12px', padding: '24px', boxShadow: '0 2px 8px rgba(0,0,0,0.08)', display: 'flex', flexDirection: 'column', gap: '12px', transition: 'transform 0.2s, box-shadow 0.2s', cursor: 'pointer' },
  cardHeader: { display: 'flex', justifyContent: 'space-between', alignItems: 'center' },
  statusBadge: { padding: '4px 12px', borderRadius: '20px', fontSize: '12px', fontWeight: '500', textTransform: 'capitalize' },
  cardActions: { display: 'flex', gap: '4px' },
  actionBtn: { background: 'none', border: 'none', padding: '6px', cursor: 'pointer', color: '#666', borderRadius: '6px', display: 'flex', alignItems: 'center', justifyContent: 'center', transition: 'background 0.2s' },
  cardTitle: { fontSize: '18px', fontWeight: '600', color: '#1a1a2e', margin: 0 },
  cardDesc: { fontSize: '14px', color: '#666', margin: 0, lineHeight: '1.5' },
  cardStats: { display: 'flex', gap: '20px' },
  cardStat: { display: 'flex', alignItems: 'center', gap: '6px', fontSize: '14px', color: '#666' },
  cardMeta: { display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px', color: '#999', paddingTop: '12px', borderTop: '1px solid #f0f0f0' },
  viewBtn: { display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px', padding: '10px', background: '#f5f5f5', border: 'none', borderRadius: '8px', fontSize: '14px', fontWeight: '500', color: '#333', cursor: 'pointer', marginTop: '8px', transition: 'background 0.2s' },
  modalOverlay: { position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000, padding: '20px' },
  wizardModal: { background: 'white', borderRadius: '16px', width: '100%', maxWidth: '700px', maxHeight: '90vh', display: 'flex', flexDirection: 'column' },
  wizardHeader: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '24px', borderBottom: '1px solid #eee' },
  wizardTitle: { fontSize: '20px', fontWeight: '600', margin: 0, color: '#1a1a2e' },
  closeBtn: { background: 'none', border: 'none', cursor: 'pointer', color: '#999', padding: '4px', display: 'flex', alignItems: 'center' },
  stepProgress: { display: 'flex', justifyContent: 'center', gap: '48px', padding: '20px', borderBottom: '1px solid #eee' },
  stepItem: { display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px' },
  stepCircle: { width: '32px', height: '32px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '14px', fontWeight: '600' },
  stepLabel: { fontSize: '13px', fontWeight: '500' },
  wizardContent: { flex: 1, overflow: 'auto', padding: '24px' },
  stepContent: { display: 'flex', flexDirection: 'column', gap: '20px' },
  errorBox: { display: 'flex', alignItems: 'center', gap: '10px', padding: '12px 16px', background: '#fef2f2', color: '#dc2626', borderRadius: '8px', fontSize: '14px', marginBottom: '16px' },
  formGroup: { display: 'flex', flexDirection: 'column', gap: '8px' },
  label: { fontSize: '14px', fontWeight: '500', color: '#333' },
  input: { padding: '12px 14px', fontSize: '15px', border: '1px solid #ddd', borderRadius: '8px', outline: 'none' },
  textarea: { padding: '12px 14px', fontSize: '15px', border: '1px solid #ddd', borderRadius: '8px', outline: 'none', resize: 'vertical', fontFamily: 'inherit' },
  templateGrid: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' },
  templateCard: { padding: '16px', border: '2px solid #e0e0e0', borderRadius: '8px', cursor: 'pointer', display: 'flex', flexDirection: 'column', gap: '4px', transition: 'all 0.2s' },
  leadsHeader: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' },
  selectAllBtn: { padding: '8px 16px', background: '#f5f5f5', border: 'none', borderRadius: '6px', fontSize: '14px', cursor: 'pointer', fontWeight: '500' },
  leadsList: { display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '300px', overflowY: 'auto' },
  leadItem: { display: 'flex', alignItems: 'center', gap: '12px', padding: '12px 16px', border: '2px solid #e0e0e0', borderRadius: '8px', cursor: 'pointer', transition: 'all 0.2s' },
  reviewSection: { background: '#f8f9fa', borderRadius: '8px', padding: '20px' },
  reviewRow: { display: 'flex', justifyContent: 'space-between', padding: '10px 0', borderBottom: '1px solid #e0e0e0' },
  reviewNote: { display: 'flex', alignItems: 'center', gap: '10px', padding: '16px', background: '#f0f4ff', borderRadius: '8px', fontSize: '14px', color: '#667eea', marginTop: '20px' },
  wizardFooter: { display: 'flex', padding: '20px 24px', borderTop: '1px solid #eee' },
  backBtn: { padding: '12px 24px', background: '#f5f5f5', border: 'none', borderRadius: '8px', fontSize: '15px', cursor: 'pointer', fontWeight: '500' },
  cancelBtn: { padding: '12px 24px', background: '#f5f5f5', border: 'none', borderRadius: '8px', fontSize: '15px', cursor: 'pointer', fontWeight: '500' },
  nextBtn: { display: 'flex', alignItems: 'center', gap: '6px', padding: '12px 24px', background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: 'white', border: 'none', borderRadius: '8px', fontSize: '15px', fontWeight: '600', cursor: 'pointer' },
  detailModal: { background: 'white', borderRadius: '16px', width: '100%', maxWidth: '600px', maxHeight: '90vh', overflow: 'auto' },
  detailHeader: { display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', padding: '24px', borderBottom: '1px solid #eee' },
  detailStats: { display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px' },
  detailStat: { display: 'flex', alignItems: 'center', gap: '12px', padding: '16px', background: '#f8f9fa', borderRadius: '8px' },
};

// Add spinner animation
const styleSheet = document.createElement("style");
styleSheet.textContent = `
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
`;
document.head.appendChild(styleSheet);

export default Campaigns;
