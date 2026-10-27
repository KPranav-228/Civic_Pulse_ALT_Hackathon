export type Severity = 'critical' | 'warning' | 'advisory' | 'info';

export type Category = 
  | 'road_closure'
  | 'water_supply'
  | 'power_cut'
  | 'severe_weather'
  | 'public_service'
  | 'other';

export interface AffectedArea {
  name: string;
  lat?: number | null;
  lng?: number | null;
}

export type SourceTier = 'official' | 'news' | 'unverified';

export type AlertStatus = 'active' | 'updated' | 'cancelled' | 'resolved' | 'past' | 'rejected' | 'upcoming';

export interface Alert {
  id: number;
  report_id?: number | null;
  title: string;
  category: Category;
  secondary_categories?: string[];
  severity: Severity;
  status: AlertStatus;
  affected_areas: Array<string | AffectedArea>;
  lat?: number | null;
  lng?: number | null;
  start_time?: string | null;
  expected_end_time?: string | null;
  expected_impact?: string | null;
  recommended_actions: string[];
  source_name: string;
  source_url?: string | null;
  source_tier: SourceTier;
  confidence: number;
  needs_review: boolean;
  parent_alert_id?: number | null;
  published_at?: string | null;
  created_at: string;
  updated_at?: string | null;
  original_text?: string | null;
  personalized_notes?: string[];
  profile_tags?: string[];
  matched_locations?: string[];
  distance_km?: number | null;
  community_confirmations?: { confirmed_resolved: number; confirmed_active: number };
}

export interface SavedLocation {
  id: number;
  user_id: string;
  label: string;
  locality_name: string;
  lat: number;
  lng: number;
  radius_km: number;
  created_at: string;
}

export type WaterSource = 'municipal' | 'borewell' | 'tanker' | 'mixed';
export type HousingType = 'apartment' | 'independent' | 'villa';

export interface UserProfile {
  id?: number;
  user_id: string;
  water_source: WaterSource;
  housing_type: HousingType;
  vulnerable_modes: string[];
  preferred_language: string;
}

export interface GazetteerLocality {
  canonical_name: string;
  lat: number;
  lng: number;
  radius_km: number;
  zone: string;
  aliases: string[];
}

export interface Area {
  id: number;
  name: string;
  city: string;
  lat?: number | null;
  lng?: number | null;
}

export interface Topic {
  id: number;
  name?: string;
  method?: string;
  algorithm?: string;
  keywords: string[];
  document_count?: number;
  report_count?: number;
  coherence_score?: number | null;
}

export interface FeatureToken {
  token: string;
  weight?: number;
  score?: number;
  favors_class?: boolean;
}

export interface XAIExplanation {
  alert_id?: number;
  predicted_category?: string;
  category_confidence?: number;
  predicted_severity?: string;
  severity_confidence?: number;
  method?: string;
  summary?: string;
  explanation_summary?: string;
  positive_features?: FeatureToken[];
  negative_features?: FeatureToken[];
  tokens?: FeatureToken[];
}

export interface IngestResponse {
  message: string;
  report_id: number;
  is_spam: boolean;
  spam_probability: number;
  alert: Alert | null;
  status?: string;
  is_duplicate?: boolean;
  existing_alert_id?: number | null;
}

export function formatAffectedAreas(areas?: Array<string | AffectedArea>): string {
  if (!areas || areas.length === 0) return 'General Hyderabad';
  return areas.map(a => typeof a === 'string' ? a : a.name).join(', ');
}

export const HYDERABAD_LOCALITY_COORDS: Record<string, { lat: number; lng: number }> = {
  gachibowli: { lat: 17.4401, lng: 78.3489 },
  madhapur: { lat: 17.4483, lng: 78.3915 },
  'hitec city': { lat: 17.4435, lng: 78.3772 },
  kondapur: { lat: 17.4699, lng: 78.3578 },
  kukatpally: { lat: 17.4849, lng: 78.4138 },
  'banjara hills': { lat: 17.4156, lng: 78.4354 },
  'jubilee hills': { lat: 17.4319, lng: 78.4073 },
  begumpet: { lat: 17.4447, lng: 78.4664 },
  secunderabad: { lat: 17.4399, lng: 78.4983 },
  charminar: { lat: 17.3616, lng: 78.4747 },
  ameerpet: { lat: 17.4375, lng: 78.4482 },
  dilsukhnagar: { lat: 17.3688, lng: 78.5247 },
  miyapur: { lat: 17.4968, lng: 78.3614 },
  mehdipatnam: { lat: 17.3916, lng: 78.4431 },
  lingampally: { lat: 17.4933, lng: 78.3159 },
  manikonda: { lat: 17.4042, lng: 78.3792 },
  uppal: { lat: 17.4022, lng: 78.5602 },
  'lb nagar': { lat: 17.3457, lng: 78.5522 },
  somajiguda: { lat: 17.4265, lng: 78.4589 },
  alwal: { lat: 17.5056, lng: 78.5089 },
  malkajgiri: { lat: 17.4526, lng: 78.5309 },
  tarnaka: { lat: 17.4286, lng: 78.5332 },
  koti: { lat: 17.3833, lng: 78.4833 },
  abids: { lat: 17.391, lng: 78.475 },
  nampally: { lat: 17.392, lng: 78.469 },
  khairatabad: { lat: 17.411, lng: 78.461 },
  tolichowki: { lat: 17.3995, lng: 78.411 },
  chandrayangutta: { lat: 17.32, lng: 78.48 },
  falaknuma: { lat: 17.33, lng: 78.47 },
  bowenpally: { lat: 17.47, lng: 78.48 },
  bahadurpura: { lat: 17.35, lng: 78.46 },
  amberpet: { lat: 17.39, lng: 78.515 },
};

export function getAlertCoordinates(alert: Alert): { lat: number; lng: number } {
  let baseCoords: { lat: number; lng: number } | null = null;
  if (alert.lat && alert.lng) {
    baseCoords = { lat: alert.lat, lng: alert.lng };
  } else if (alert.affected_areas && alert.affected_areas.length > 0) {
    const first = alert.affected_areas[0];
    if (typeof first !== 'string' && first.lat && first.lng) {
      baseCoords = { lat: first.lat, lng: first.lng };
    } else {
      const areaName = (typeof first === 'string' ? first : first.name || '').toLowerCase();
      for (const [key, coords] of Object.entries(HYDERABAD_LOCALITY_COORDS)) {
        if (areaName.includes(key) || key.includes(areaName)) {
          baseCoords = coords;
          break;
        }
      }
    }
  }

  if (!baseCoords) {
    const titleLower = alert.title.toLowerCase();
    for (const [key, coords] of Object.entries(HYDERABAD_LOCALITY_COORDS)) {
      if (titleLower.includes(key)) {
        baseCoords = coords;
        break;
      }
    }
  }

  if (!baseCoords) {
    baseCoords = { lat: 17.425, lng: 78.455 };
  }

  // Deterministic micro-jitter (~150-250m) so multiple alerts in the same ward fan out cleanly
  const idSeed = alert.id || 1;
  const jitterLat = Math.sin(idSeed * 12.9898) * 0.0035;
  const jitterLng = Math.cos(idSeed * 78.233) * 0.0035;
  return {
    lat: baseCoords.lat + jitterLat,
    lng: baseCoords.lng + jitterLng,
  };
}
