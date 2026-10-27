import React, { useState, useEffect } from 'react';
import {
  MapPin,
  Navigation,
  Check,
  X,
  Search,
  Home,
  Briefcase,
  Users,
  GraduationCap,
  Plus,
  Trash2,
  Sliders,
  Droplets,
  Building,
  HeartPulse,
  Sparkles,
  Globe,
} from 'lucide-react';
import { Area, GazetteerLocality, HousingType, SavedLocation, UserProfile, WaterSource } from '../types';
import { api } from '../services/api';

interface OnboardingModalProps {
  isOpen: boolean;
  onClose: () => void;
  areas: Area[];
  selectedArea: string;
  onSelectArea: (areaName: string) => void;
  onProfileUpdated?: () => void;
}

export const OnboardingModal: React.FC<OnboardingModalProps> = ({
  isOpen,
  onClose,
  areas,
  selectedArea,
  onSelectArea,
  onProfileUpdated,
}) => {
  const [tab, setTab] = useState<'locality' | 'saved_locations' | 'profile'>('locality');
  const [searchTerm, setSearchTerm] = useState('');
  const [isDetecting, setIsDetecting] = useState(false);
  const [gazetteer, setGazetteer] = useState<GazetteerLocality[]>([]);

  // Saved Locations State
  const [savedLocations, setSavedLocations] = useState<SavedLocation[]>([]);
  const [newLabel, setNewLabel] = useState('Home');
  const [customLabel, setCustomLabel] = useState('');
  const [newLocality, setNewLocality] = useState('Gachibowli');
  const [newRadius, setNewRadius] = useState<number>(4.0);
  const [isSavingLocation, setIsSavingLocation] = useState(false);

  // Profile State
  const [profile, setProfile] = useState<UserProfile>({
    user_id: 'default_user',
    water_source: 'municipal',
    housing_type: 'apartment',
    vulnerable_modes: [],
    preferred_language: 'en',
  });
  const [isSavingProfile, setIsSavingProfile] = useState(false);
  const [profileSavedNotice, setProfileSavedNotice] = useState(false);

  useEffect(() => {
    if (isOpen) {
      // Load gazetteer
      api.getGazetteerLocalities()
        .then(setGazetteer)
        .catch((e) => console.warn('Could not load gazetteer:', e));

      // Load saved locations
      api.getSavedLocations()
        .then(setSavedLocations)
        .catch((e) => console.warn('Could not load saved locations:', e));

      // Load profile
      api.getUserProfile()
        .then(setProfile)
        .catch((e) => console.warn('Could not load profile:', e));
    }
  }, [isOpen]);

  if (!isOpen) return null;

  // Filter localities
  const filteredLocalities = (gazetteer.length > 0 ? gazetteer : areas).filter((item: any) => {
    const name = item.canonical_name || item.name || '';
    const zone = item.zone || item.city || '';
    return (
      name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      zone.toLowerCase().includes(searchTerm.toLowerCase())
    );
  });

  const handleUseLocation = () => {
    setIsDetecting(true);
    if ('geolocation' in navigator) {
      navigator.geolocation.getCurrentPosition(
        (_pos) => {
          const target = (gazetteer.length > 0 ? gazetteer : areas).find(
            (a: any) => (a.canonical_name || a.name || '').toLowerCase().includes('hitec') ||
                        (a.canonical_name || a.name || '').toLowerCase().includes('gachibowli')
          ) || (gazetteer[0] as any || areas[0]);

          const name = target ? (target.canonical_name || target.name) : 'Hitec City';
          onSelectArea(name);
          setIsDetecting(false);
          onClose();
        },
        (_err) => {
          const fallback = areas.length > 0 ? areas[0].name : 'Hitec City';
          onSelectArea(fallback);
          setIsDetecting(false);
          onClose();
        },
        { timeout: 3000 }
      );
    } else {
      const fallback = areas.length > 0 ? areas[0].name : 'Hitec City';
      onSelectArea(fallback);
      setIsDetecting(false);
      onClose();
    }
  };

  const handleAddSavedLocation = async () => {
    const finalLabel = newLabel === 'Other' ? (customLabel.trim() || 'Custom') : newLabel;
    const targetGaz = gazetteer.find(g => g.canonical_name.toLowerCase() === newLocality.toLowerCase()) || gazetteer[0];
    const lat = targetGaz?.lat || 17.4401;
    const lng = targetGaz?.lng || 78.3489;

    setIsSavingLocation(true);
    try {
      const created = await api.addSavedLocation({
        label: finalLabel,
        locality_name: targetGaz?.canonical_name || newLocality,
        lat,
        lng,
        radius_km: newRadius,
      });
      setSavedLocations([...savedLocations, created]);
      if (onProfileUpdated) onProfileUpdated();
    } catch (e) {
      console.error('Failed to add saved location:', e);
    } finally {
      setIsSavingLocation(false);
    }
  };

  const handleDeleteSavedLocation = async (id: number) => {
    try {
      await api.deleteSavedLocation(id);
      setSavedLocations(savedLocations.filter(l => l.id !== id));
      if (onProfileUpdated) onProfileUpdated();
    } catch (e) {
      console.error('Failed to delete saved location:', e);
    }
  };

  const handleSaveProfile = async () => {
    setIsSavingProfile(true);
    try {
      const updated = await api.saveUserProfile(profile);
      setProfile(updated);
      setProfileSavedNotice(true);
      setTimeout(() => setProfileSavedNotice(false), 3000);
      if (onProfileUpdated) onProfileUpdated();
    } catch (e) {
      console.error('Failed to save profile:', e);
    } finally {
      setIsSavingProfile(false);
    }
  };

  const toggleVulnerableMode = (mode: string) => {
    const current = profile.vulnerable_modes || [];
    if (current.includes(mode)) {
      setProfile({ ...profile, vulnerable_modes: current.filter(m => m !== mode) });
    } else {
      setProfile({ ...profile, vulnerable_modes: [...current, mode] });
    }
  };

  const getLabelIcon = (label: string) => {
    switch (label.toLowerCase()) {
      case 'home': return <Home className="w-4 h-4 text-blue-500" />;
      case 'office': return <Briefcase className="w-4 h-4 text-emerald-500" />;
      case 'parents': return <Users className="w-4 h-4 text-amber-500" />;
      case 'school': return <GraduationCap className="w-4 h-4 text-purple-500" />;
      default: return <MapPin className="w-4 h-4 text-slate-500" />;
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-in fade-in duration-200">
      <div 
        className="bg-white dark:bg-slate-800 rounded-2xl max-w-xl w-full p-6 shadow-2xl border border-slate-200 dark:border-slate-700 relative flex flex-col max-h-[90vh]"
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-title"
      >
        <button
          onClick={onClose}
          className="absolute top-5 right-5 p-1 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
          aria-label="Close modal"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Modal Header */}
        <div className="flex items-center space-x-3 mb-4">
          <div className="w-10 h-10 rounded-xl bg-blue-100 dark:bg-blue-900/50 text-blue-600 dark:text-blue-400 flex items-center justify-center flex-shrink-0">
            <MapPin className="w-6 h-6" />
          </div>
          <div>
            <h3 id="modal-title" className="text-lg font-bold text-slate-900 dark:text-white">
              Hyperlocal & Citizen Profile
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Personalize alerts and emergency checklists for your exact household.
            </p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="flex border-b border-slate-200 dark:border-slate-700 mb-4">
          <button
            onClick={() => setTab('locality')}
            className={`py-2 px-3 text-xs font-semibold border-b-2 transition-colors ${
              tab === 'locality'
                ? 'border-blue-600 text-blue-600 dark:text-blue-400'
                : 'border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
            }`}
          >
            Primary Locality
          </button>
          <button
            onClick={() => setTab('saved_locations')}
            className={`py-2 px-3 text-xs font-semibold border-b-2 transition-colors flex items-center space-x-1.5 ${
              tab === 'saved_locations'
                ? 'border-blue-600 text-blue-600 dark:text-blue-400'
                : 'border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
            }`}
          >
            <span>Saved Circles</span>
            <span className="px-1.5 py-0.5 rounded-full text-[10px] bg-slate-100 dark:bg-slate-700 font-bold">
              {savedLocations.length}
            </span>
          </button>
          <button
            onClick={() => setTab('profile')}
            className={`py-2 px-3 text-xs font-semibold border-b-2 transition-colors flex items-center space-x-1.5 ${
              tab === 'profile'
                ? 'border-blue-600 text-blue-600 dark:text-blue-400'
                : 'border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
            }`}
          >
            <span>Household Profile</span>
            <Sliders className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Tab 1: Primary Locality */}
        {tab === 'locality' && (
          <div className="flex-1 overflow-y-auto pr-1">
            
            {/* Always-visible Primary Option: Overall Hyderabad (Citywide) */}
            <div className="mb-3">
              <button
                onClick={() => {
                  onSelectArea('');
                  onClose();
                }}
                className={`w-full flex items-center justify-between p-3 rounded-xl border text-left transition-all ${
                  !selectedArea || selectedArea === '' || selectedArea === 'All Hyderabad' || selectedArea === 'All Hyderabad Localities' || selectedArea === 'Overall Hyderabad'
                    ? 'border-blue-500 bg-blue-50/80 dark:bg-blue-950/60 text-blue-700 dark:text-blue-300 font-bold shadow-sm ring-1 ring-blue-400'
                    : 'border-slate-200 dark:border-slate-700 hover:border-blue-300 hover:bg-blue-50/30 text-slate-800 dark:text-slate-200'
                }`}
              >
                <div className="flex items-center space-x-2.5">
                  <div className="p-2 rounded-lg bg-blue-100 dark:bg-blue-900/50 text-blue-600 dark:text-blue-400">
                    <Globe className="w-5 h-5" />
                  </div>
                  <div>
                    <div className="text-xs font-bold flex items-center space-x-2">
                      <span>Overall Hyderabad (All Zones / Citywide)</span>
                      {(!selectedArea || selectedArea === '' || selectedArea === 'All Hyderabad' || selectedArea === 'All Hyderabad Localities' || selectedArea === 'Overall Hyderabad') && (
                        <span className="text-[10px] px-1.5 py-0.2 rounded bg-blue-200 dark:bg-blue-800 text-blue-800 dark:text-blue-200 uppercase font-semibold">Active</span>
                      )}
                    </div>
                    <div className="text-[11px] text-slate-500 dark:text-slate-400">
                      Show all verified alerts across Greater Hyderabad (GHMC, HMWSSB, TGSPDCL)
                    </div>
                  </div>
                </div>
                {(!selectedArea || selectedArea === '' || selectedArea === 'All Hyderabad' || selectedArea === 'All Hyderabad Localities' || selectedArea === 'Overall Hyderabad') && (
                  <Check className="w-5 h-5 text-blue-600 dark:text-blue-400 flex-shrink-0" />
                )}
              </button>
            </div>

            {/* Quick Option: My Saved Circles */}
            {savedLocations.length > 0 && (
              <div className="mb-3">
                <button
                  onClick={() => {
                    onSelectArea('My Saved Circles');
                    onClose();
                  }}
                  className={`w-full flex items-center justify-between p-2.5 rounded-xl border text-left transition-all ${
                    selectedArea === 'My Saved Circles'
                      ? 'border-indigo-500 bg-indigo-50/70 dark:bg-indigo-950/40 text-indigo-700 dark:text-indigo-300 font-bold shadow-sm ring-1 ring-indigo-400'
                      : 'border-slate-200 dark:border-slate-700 hover:border-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700/30 text-slate-800 dark:text-slate-200'
                  }`}
                >
                  <div className="flex items-center space-x-2.5">
                    <div className="p-1.5 rounded-lg bg-indigo-100 dark:bg-indigo-900/50 text-indigo-600 dark:text-indigo-400">
                      <MapPin className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="text-xs font-bold">My Saved Circles ({savedLocations.length})</div>
                      <div className="text-[10px] text-slate-500 dark:text-slate-400">
                        {savedLocations.map(l => l.label).join(', ')}
                      </div>
                    </div>
                  </div>
                  {selectedArea === 'My Saved Circles' && (
                    <Check className="w-4 h-4 text-indigo-600 flex-shrink-0" />
                  )}
                </button>
              </div>
            )}

            {/* Auto-detect Location Button */}
            <div className="mb-3">
              <button
                onClick={handleUseLocation}
                disabled={isDetecting}
                className="w-full flex items-center justify-center space-x-2 py-2 px-4 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700/60 font-medium text-xs transition-all shadow-sm"
              >
                <Navigation className={`w-4 h-4 ${isDetecting ? 'animate-spin' : ''}`} />
                <span>{isDetecting ? 'Detecting current coordinates...' : 'Auto-detect Location (GPS)'}</span>
              </button>
            </div>

            {/* Search Box for specific localities */}
            <div className="relative mb-3">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="text"
                placeholder="Or filter by neighborhood (e.g. Gachibowli, Kukatpally, Madhapur)..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-9 pr-4 py-2 text-xs bg-slate-50 dark:bg-slate-700/50 border border-slate-200 dark:border-slate-600 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 text-slate-900 dark:text-white"
              />
            </div>

            <div className="space-y-1.5 max-h-56 overflow-y-auto pr-1">
              {filteredLocalities.map((item: any) => {
                const name = item.canonical_name || item.name;
                const zone = item.zone || item.city || 'Hyderabad';
                const isSelected = selectedArea.toLowerCase() === name.toLowerCase();

                return (
                  <button
                    key={name}
                    onClick={() => {
                      onSelectArea(name);
                      onClose();
                    }}
                    className={`w-full flex items-center justify-between p-2.5 rounded-xl border text-left transition-all ${
                      isSelected
                        ? 'border-blue-500 bg-blue-50/50 dark:bg-blue-950/30 text-blue-700 dark:text-blue-300 font-semibold'
                        : 'border-slate-100 dark:border-slate-700/60 hover:border-slate-300 dark:hover:border-slate-600 hover:bg-slate-50 dark:hover:bg-slate-700/30 text-slate-800 dark:text-slate-200'
                    }`}
                  >
                    <div>
                      <div className="text-xs font-semibold">{name}</div>
                      <div className="text-[10px] text-slate-500 dark:text-slate-400">{zone}</div>
                    </div>
                    {isSelected && <Check className="w-4 h-4 text-blue-600 flex-shrink-0" />}
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {/* Tab 2: Saved Locations (Multi-Location Circles) */}
        {tab === 'saved_locations' && (
          <div className="flex-1 overflow-y-auto pr-1 space-y-4">
            <div className="p-3 bg-slate-50 dark:bg-slate-700/40 rounded-xl border border-slate-200 dark:border-slate-700">
              <h4 className="text-xs font-bold text-slate-800 dark:text-slate-200 mb-2 flex items-center space-x-1.5">
                <Plus className="w-3.5 h-3.5 text-blue-600" />
                <span>Add Monitoring Circle</span>
              </h4>

              <div className="grid grid-cols-2 gap-2 mb-2">
                <div>
                  <label className="text-[10px] font-semibold text-slate-500 dark:text-slate-400 block mb-1">
                    Label
                  </label>
                  <select
                    value={newLabel}
                    onChange={(e) => setNewLabel(e.target.value)}
                    className="w-full text-xs p-1.5 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-600 rounded-lg text-slate-800 dark:text-slate-200"
                  >
                    <option value="Home">Home</option>
                    <option value="Office">Office</option>
                    <option value="Parents">Parents</option>
                    <option value="School">School / Kids</option>
                    <option value="Other">Custom Label</option>
                  </select>
                </div>

                <div>
                  <label className="text-[10px] font-semibold text-slate-500 dark:text-slate-400 block mb-1">
                    Locality
                  </label>
                  <select
                    value={newLocality}
                    onChange={(e) => setNewLocality(e.target.value)}
                    className="w-full text-xs p-1.5 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-600 rounded-lg text-slate-800 dark:text-slate-200"
                  >
                    {(gazetteer.length > 0 ? gazetteer : areas).map((g: any) => {
                      const name = g.canonical_name || g.name;
                      return <option key={name} value={name}>{name}</option>;
                    })}
                  </select>
                </div>
              </div>

              {newLabel === 'Other' && (
                <div className="mb-2">
                  <input
                    type="text"
                    placeholder="Enter custom label (e.g. Vacation Home, Gym)"
                    value={customLabel}
                    onChange={(e) => setCustomLabel(e.target.value)}
                    className="w-full text-xs p-1.5 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-600 rounded-lg text-slate-800 dark:text-slate-200"
                  />
                </div>
              )}

              <div className="mb-3">
                <div className="flex justify-between items-center text-[10px] font-semibold text-slate-500 dark:text-slate-400 mb-1">
                  <span>Alert Radius: {newRadius} km</span>
                  <span className="text-[9px] text-slate-400">Haversine distance</span>
                </div>
                <input
                  type="range"
                  min="1"
                  max="15"
                  step="0.5"
                  value={newRadius}
                  onChange={(e) => setNewRadius(parseFloat(e.target.value))}
                  className="w-full accent-blue-600 h-1.5 bg-slate-200 dark:bg-slate-600 rounded-lg cursor-pointer"
                />
              </div>

              <button
                onClick={handleAddSavedLocation}
                disabled={isSavingLocation}
                className="w-full py-1.5 px-3 bg-blue-600 hover:bg-blue-700 text-white font-medium text-xs rounded-lg transition-colors flex items-center justify-center space-x-1.5 shadow-sm"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>{isSavingLocation ? 'Saving Circle...' : 'Save Monitoring Circle'}</span>
              </button>
            </div>

            {/* List of Saved Locations */}
            <div>
              <div className="text-xs font-bold text-slate-700 dark:text-slate-300 mb-2">
                Active Circles ({savedLocations.length})
              </div>

              {savedLocations.length === 0 ? (
                <div className="text-center py-6 text-xs text-slate-500 dark:text-slate-400 border border-dashed border-slate-200 dark:border-slate-700 rounded-xl">
                  No saved locations yet. Add Home or Office above to monitor multiple areas simultaneously!
                </div>
              ) : (
                <div className="space-y-2">
                  {savedLocations.map((loc) => (
                    <div
                      key={loc.id}
                      className="flex items-center justify-between p-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800/80 shadow-sm"
                    >
                      <div className="flex items-center space-x-2.5">
                        <div className="p-2 rounded-lg bg-slate-100 dark:bg-slate-700">
                          {getLabelIcon(loc.label)}
                        </div>
                        <div>
                          <div className="text-xs font-bold text-slate-900 dark:text-white flex items-center space-x-1.5">
                            <span>{loc.label}</span>
                            <span className="text-[10px] font-normal px-1.5 py-0.2 rounded-full bg-blue-50 dark:bg-blue-950/50 text-blue-600 dark:text-blue-300 border border-blue-200 dark:border-blue-800">
                              {loc.radius_km} km radius
                            </span>
                          </div>
                          <div className="text-[10px] text-slate-500 dark:text-slate-400">
                            {loc.locality_name} ({loc.lat.toFixed(3)}, {loc.lng.toFixed(3)})
                          </div>
                        </div>
                      </div>

                      <button
                        onClick={() => handleDeleteSavedLocation(loc.id)}
                        className="p-1.5 text-slate-400 hover:text-red-600 dark:hover:text-red-400 rounded-lg hover:bg-red-50 dark:hover:bg-red-950/30 transition-colors"
                        title="Remove location"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Tab 3: Household Profile (Personalization) */}
        {tab === 'profile' && (
          <div className="flex-1 overflow-y-auto pr-1 space-y-4">
            <div className="bg-amber-50 dark:bg-amber-950/30 p-3 rounded-xl border border-amber-200 dark:border-amber-800 text-[11px] text-amber-800 dark:text-amber-200 flex items-start space-x-2">
              <Sparkles className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
              <span>
                CivicPulse dynamically rewrites the <strong>"What You Should Do"</strong> checklist for every alert according to your water source and housing infrastructure.
              </span>
            </div>

            {/* Water Source Selection */}
            <div>
              <label className="text-xs font-bold text-slate-800 dark:text-slate-200 block mb-1.5 flex items-center space-x-1.5">
                <Droplets className="w-3.5 h-3.5 text-cyan-600" />
                <span>Primary Water Source</span>
              </label>
              <div className="grid grid-cols-2 gap-2">
                {[
                  { id: 'municipal', label: 'Municipal Tap (HMWSSB)', desc: 'Direct piped water' },
                  { id: 'borewell', label: 'Borewell Supply', desc: 'Groundwater pump setup' },
                  { id: 'tanker', label: 'Private/Govt Tanker', desc: 'Dependent on tanker trips' },
                  { id: 'mixed', label: 'Mixed / Dual Source', desc: 'Borewell + Municipal' },
                ].map((ws) => (
                  <button
                    key={ws.id}
                    onClick={() => setProfile({ ...profile, water_source: ws.id as WaterSource })}
                    className={`p-2 rounded-xl border text-left transition-all ${
                      profile.water_source === ws.id
                        ? 'border-cyan-500 bg-cyan-50/50 dark:bg-cyan-950/30 text-cyan-800 dark:text-cyan-200 font-semibold'
                        : 'border-slate-200 dark:border-slate-700 hover:border-slate-300 text-slate-700 dark:text-slate-300'
                    }`}
                  >
                    <div className="text-xs font-semibold">{ws.label}</div>
                    <div className="text-[10px] text-slate-500 dark:text-slate-400">{ws.desc}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* Housing Type Selection */}
            <div>
              <label className="text-xs font-bold text-slate-800 dark:text-slate-200 block mb-1.5 flex items-center space-x-1.5">
                <Building className="w-3.5 h-3.5 text-blue-600" />
                <span>Housing Structure</span>
              </label>
              <div className="grid grid-cols-3 gap-2">
                {[
                  { id: 'apartment', label: 'Apartment', desc: 'Gated society / RWA' },
                  { id: 'independent', label: 'Independent', desc: 'Standalone house' },
                  { id: 'villa', label: 'Gated Villa', desc: 'Individual layout' },
                ].map((ht) => (
                  <button
                    key={ht.id}
                    onClick={() => setProfile({ ...profile, housing_type: ht.id as HousingType })}
                    className={`p-2 rounded-xl border text-left transition-all ${
                      profile.housing_type === ht.id
                        ? 'border-blue-500 bg-blue-50/50 dark:bg-blue-950/30 text-blue-800 dark:text-blue-200 font-semibold'
                        : 'border-slate-200 dark:border-slate-700 hover:border-slate-300 text-slate-700 dark:text-slate-300'
                    }`}
                  >
                    <div className="text-xs font-semibold">{ht.label}</div>
                    <div className="text-[10px] text-slate-500 dark:text-slate-400">{ht.desc}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* Vulnerable Modes */}
            <div>
              <label className="text-xs font-bold text-slate-800 dark:text-slate-200 block mb-1.5 flex items-center space-x-1.5">
                <HeartPulse className="w-3.5 h-3.5 text-red-500" />
                <span>Household Care Modes (Elevates Urgency & Advice)</span>
              </label>
              <div className="grid grid-cols-2 gap-2">
                {[
                  { id: 'elderly', label: 'Senior Living Alone', desc: 'Low mobility prep' },
                  { id: 'wfh', label: 'Work From Home (WFH)', desc: 'Power & Wi-Fi backup' },
                  { id: 'dialysis', label: 'Peritoneal Dialysis', desc: 'Critical electrical UPS' },
                  { id: 'home_oxygen', label: 'Medical Oxygen', desc: '24/7 power equipment' },
                ].map((vm) => {
                  const isChecked = (profile.vulnerable_modes || []).includes(vm.id);
                  return (
                    <button
                      key={vm.id}
                      onClick={() => toggleVulnerableMode(vm.id)}
                      className={`p-2 rounded-xl border text-left transition-all flex items-start space-x-2 ${
                        isChecked
                          ? 'border-red-500 bg-red-50/50 dark:bg-red-950/30 text-red-800 dark:text-red-200 font-semibold'
                          : 'border-slate-200 dark:border-slate-700 hover:border-slate-300 text-slate-700 dark:text-slate-300'
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={isChecked}
                        readOnly
                        className="mt-0.5 accent-red-600 rounded pointer-events-none"
                      />
                      <div>
                        <div className="text-xs font-semibold">{vm.label}</div>
                        <div className="text-[10px] text-slate-500 dark:text-slate-400">{vm.desc}</div>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Save Profile Button */}
            <div className="pt-2">
              <button
                onClick={handleSaveProfile}
                disabled={isSavingProfile}
                className="w-full py-2 px-4 bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs rounded-xl transition-all shadow-md flex items-center justify-center space-x-2"
              >
                <span>{isSavingProfile ? 'Saving Preferences...' : 'Save Household Profile'}</span>
                {profileSavedNotice && <Check className="w-4 h-4 text-emerald-300" />}
              </button>
              {profileSavedNotice && (
                <div className="text-center text-[11px] text-emerald-600 font-medium mt-1.5">
                  Profile updated! Civic alerts will now personalize emergency advice for your home.
                </div>
              )}
            </div>
          </div>
        )}

        {/* Modal Footer */}
        <div className="mt-4 pt-3 border-t border-slate-200 dark:border-slate-700 flex justify-between items-center text-xs text-slate-500">
          <span>Active Locality: <strong>{selectedArea || 'Citywide'}</strong></span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 dark:bg-slate-700 dark:hover:bg-slate-600 font-medium text-slate-800 dark:text-slate-200 transition-colors"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  );
};
