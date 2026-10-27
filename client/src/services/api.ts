import {
  Alert,
  Area,
  GazetteerLocality,
  IngestResponse,
  SavedLocation,
  Topic,
  UserProfile,
  XAIExplanation,
} from '../types';

const API_BASE = '/api';

export const api = {
  async getAlerts(params?: {
    area?: string;
    category?: string;
    severity?: string;
    status?: string;
    search?: string;
    lang?: string;
  }): Promise<Alert[]> {
    const query = new URLSearchParams();
    if (params?.area) query.append('area', params.area);
    if (params?.category) query.append('category', params.category);
    if (params?.severity) query.append('severity', params.severity);
    if (params?.status) query.append('status', params.status);
    if (params?.search) query.append('search', params.search);
    if (params?.lang) query.append('lang', params.lang);

    const res = await fetch(`${API_BASE}/alerts?${query.toString()}`);
    if (!res.ok) throw new Error(`Failed to fetch alerts: ${res.statusText}`);
    return res.json();
  },

  async getAlert(id: number): Promise<Alert> {
    const res = await fetch(`${API_BASE}/alerts/${id}`);
    if (!res.ok) throw new Error(`Alert #${id} not found`);
    return res.json();
  },

  async getAlertExplanation(id: number): Promise<XAIExplanation> {
    const res = await fetch(`${API_BASE}/alerts/${id}/explain`);
    if (!res.ok) throw new Error(`Failed to fetch explanation for Alert #${id}`);
    return res.json();
  },

  async updateAlert(id: number, data: Partial<Alert>): Promise<Alert> {
    const res = await fetch(`${API_BASE}/alerts/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error(`Failed to update alert #${id}`);
    return res.json();
  },

  async ingestReport(data: {
    raw_text: string;
    source_name?: string;
    source_url?: string;
  }): Promise<IngestResponse> {
    const payload = {
      text: data.raw_text,
      raw_text: data.raw_text,
      source_name: data.source_name,
      source_url: data.source_url,
    };
    const res = await fetch(`${API_BASE}/ingest`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error(`Ingestion failed: ${res.statusText}`);
    return res.json();
  },

  async getAreas(): Promise<Area[]> {
    const res = await fetch(`${API_BASE}/areas`);
    if (!res.ok) throw new Error(`Failed to fetch areas: ${res.statusText}`);
    return res.json();
  },

  async getTopics(): Promise<Topic[]> {
    const res = await fetch(`${API_BASE}/topics`);
    if (!res.ok) throw new Error(`Failed to fetch topics: ${res.statusText}`);
    return res.json();
  },

  async getReviewQueue(): Promise<Alert[]> {
    const res = await fetch(`${API_BASE}/admin/review-queue`);
    if (!res.ok) throw new Error(`Failed to fetch review queue: ${res.statusText}`);
    return res.json();
  },

  async checkHealth(): Promise<{ status: string; models_loaded: boolean }> {
    const res = await fetch(`${API_BASE}/health`);
    if (!res.ok) throw new Error(`Health check failed`);
    return res.json();
  },

  async getGazetteerLocalities(): Promise<GazetteerLocality[]> {
    const res = await fetch(`${API_BASE}/gazetteer/localities`);
    if (!res.ok) throw new Error(`Failed to fetch gazetteer: ${res.statusText}`);
    return res.json();
  },

  async resolveLocality(query: string): Promise<GazetteerLocality> {
    const res = await fetch(`${API_BASE}/gazetteer/resolve?query=${encodeURIComponent(query)}`);
    if (!res.ok) throw new Error(`Locality '${query}' could not be resolved`);
    return res.json();
  },

  async getSavedLocations(userId: string = 'default_user'): Promise<SavedLocation[]> {
    const res = await fetch(`${API_BASE}/user/locations?user_id=${encodeURIComponent(userId)}`);
    if (!res.ok) throw new Error(`Failed to fetch saved locations: ${res.statusText}`);
    return res.json();
  },

  async addSavedLocation(payload: {
    user_id?: string;
    label: string;
    locality_name: string;
    lat: number;
    lng: number;
    radius_km?: number;
  }): Promise<SavedLocation> {
    const res = await fetch(`${API_BASE}/user/locations`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error(`Failed to save location`);
    return res.json();
  },

  async deleteSavedLocation(locationId: number, userId: string = 'default_user'): Promise<void> {
    const res = await fetch(`${API_BASE}/user/locations/${locationId}?user_id=${encodeURIComponent(userId)}`, {
      method: 'DELETE',
    });
    if (!res.ok) throw new Error(`Failed to delete saved location`);
  },

  async getUserProfile(userId: string = 'default_user'): Promise<UserProfile> {
    const res = await fetch(`${API_BASE}/user/profile?user_id=${encodeURIComponent(userId)}`);
    if (!res.ok) throw new Error(`Failed to fetch user profile`);
    return res.json();
  },

  async saveUserProfile(payload: Partial<UserProfile> & { user_id?: string }): Promise<UserProfile> {
    const res = await fetch(`${API_BASE}/user/profile`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error(`Failed to save user profile`);
    return res.json();
  },

  async getUserPersonalizedAlerts(params?: {
    user_id?: string;
    category?: string;
    status?: string;
    lang?: string;
  }): Promise<Alert[]> {
    const query = new URLSearchParams();
    query.append('user_id', params?.user_id || 'default_user');
    if (params?.category) query.append('category', params?.category);
    if (params?.status) query.append('status', params?.status);
    if (params?.lang) query.append('lang', params?.lang);

    const res = await fetch(`${API_BASE}/user/alerts?${query.toString()}`);
    if (!res.ok) throw new Error(`Failed to fetch personalized alerts`);
    return res.json();
  },

  async submitAlertFeedback(
    alertId: number,
    data: {
      suggested_category?: string;
      suggested_severity?: string;
      comment?: string;
      user_id?: string;
    }
  ): Promise<any> {
    const res = await fetch(`${API_BASE}/alerts/${alertId}/feedback`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error(`Failed to submit feedback`);
    return res.json();
  },

  async submitCommunityConfirmation(
    alertId: number,
    statusVote: 'resolved' | 'still_active',
    userId: string = 'default_user'
  ): Promise<any> {
    const res = await fetch(`${API_BASE}/alerts/${alertId}/confirm`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status_vote: statusVote, user_id: userId }),
    });
    if (!res.ok) throw new Error(`Failed to submit confirmation`);
    return res.json();
  },

  async getMonitoringMetrics(): Promise<any> {
    const res = await fetch(`${API_BASE}/monitoring`);
    if (!res.ok) throw new Error(`Failed to fetch monitoring metrics`);
    return res.json();
  },
};
