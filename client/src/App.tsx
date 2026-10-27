import React, { useState, useEffect, useMemo } from 'react';
import { Header } from './components/Header';
import { OnboardingModal } from './components/OnboardingModal';
import { FilterBar, SortOption } from './components/FilterBar';
import { AlertCard } from './components/AlertCard';
import { MapView } from './components/MapView';
import { AdminPanel } from './components/AdminPanel';
import { AlertDetailModal } from './components/AlertDetailModal';
import { Alert, Area } from './types';
import { api } from './services/api';
import { Language } from './services/i18n';
import { AlertCircle, RefreshCw, Layers, Map as MapIcon, LayoutGrid } from 'lucide-react';

const CITYWIDE_AREAS = new Set([
  '', 
  'all', 
  'all hyderabad', 
  'overall hyderabad', 
  'overall hyderabad (all zones)', 
  'all hyderabad localities', 
  'citywide',
  'hyderabad'
]);

const HYDERABAD_LOCALITIES = [
  'Banjara Hills', 'Jubilee Hills', 'HITEC City', 'Gachibowli', 'Madhapur',
  'Kondapur', 'Kukatpally', 'Begumpet', 'Secunderabad', 'Ameerpet',
  'Panjagutta', 'Dilsukhnagar', 'Miyapur', 'Mehdipatnam', 'Lingampally',
  'Manikonda', 'Uppal', 'LB Nagar', 'Somajiguda', 'Alwal',
  'Malkajgiri', 'Tarnaka', 'Koti', 'Abids', 'Nampally',
  'Khairatabad', 'Tolichowki', 'Chandrayangutta', 'Falaknuma', 'Bowenpally',
  'Bahadurpura', 'Amberpet'
];

export const App: React.FC = () => {
  // Read initial filter values from URL query string
  const initialUrlFilters = useMemo(() => {
    if (typeof window === 'undefined') return { categories: [], severity: '', locality: '', myLocations: false, sort: 'urgency' as SortOption, search: '' };
    const p = new URLSearchParams(window.location.search);
    const categories = p.get('categories') ? p.get('categories')!.split(',').filter(Boolean) : [];
    const severity = p.get('severity') || '';
    const locality = p.get('locality') || p.get('area') || localStorage.getItem('civicpulse_area') || '';
    const myLocations = p.get('my_locations') === 'true';
    const sort = (p.get('sort') as SortOption) || 'urgency';
    const search = p.get('q') || '';
    return { categories, severity, locality, myLocations, sort, search };
  }, []);

  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [areas, setAreas] = useState<Area[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // User Preferences
  const [selectedArea, setSelectedArea] = useState<string>(initialUrlFilters.locality);
  const [darkMode, setDarkMode] = useState<boolean>(() => {
    return localStorage.getItem('civicpulse_theme') === 'dark';
  });
  const [language, setLanguage] = useState<Language>(() => {
    return (localStorage.getItem('civicpulse_lang') as Language) || 'en';
  });

  // UI state
  const [activeTab, setActiveTab] = useState<'feed' | 'map' | 'admin'>('feed');
  const [feedViewMode, setFeedViewMode] = useState<'cards' | 'split'>('cards');
  const [highlightAlertId, setHighlightAlertId] = useState<number | null>(null);
  const [isLocationModalOpen, setIsLocationModalOpen] = useState(false);
  const [selectedAlertForModal, setSelectedAlertForModal] = useState<Alert | null>(null);

  // Filters state (Persisted in URL)
  const [selectedCategories, setSelectedCategories] = useState<string[]>(initialUrlFilters.categories);
  const [selectedSeverity, setSelectedSeverity] = useState<string>(initialUrlFilters.severity);
  const [isMyLocationsOnly, setIsMyLocationsOnly] = useState<boolean>(initialUrlFilters.myLocations);
  const [sortBy, setSortBy] = useState<SortOption>(initialUrlFilters.sort);
  const [searchQuery, setSearchQuery] = useState<string>(initialUrlFilters.search);
  const selectedStatus = 'active';

  // Apply dark mode class to html document
  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark');
      localStorage.setItem('civicpulse_theme', 'dark');
    } else {
      document.documentElement.classList.remove('dark');
      localStorage.setItem('civicpulse_theme', 'light');
    }
  }, [darkMode]);

  // Sync state changes with URL query string
  useEffect(() => {
    if (typeof window === 'undefined') return;
    const p = new URLSearchParams();
    if (selectedCategories.length > 0) p.set('categories', selectedCategories.join(','));
    if (selectedSeverity) p.set('severity', selectedSeverity);
    if (selectedArea && !CITYWIDE_AREAS.has(selectedArea.trim().toLowerCase())) p.set('locality', selectedArea);
    if (isMyLocationsOnly) p.set('my_locations', 'true');
    if (sortBy !== 'urgency') p.set('sort', sortBy);
    if (searchQuery.trim()) p.set('q', searchQuery.trim());

    const newQuery = p.toString() ? `?${p.toString()}` : window.location.pathname;
    window.history.replaceState(null, '', newQuery);
  }, [selectedCategories, selectedSeverity, selectedArea, isMyLocationsOnly, sortBy, searchQuery]);

  // Save selected area
  const handleSelectArea = (area: string) => {
    setSelectedArea(area);
    localStorage.setItem('civicpulse_area', area);
  };

  // Fetch areas on initial mount
  useEffect(() => {
    api.getAreas().then(setAreas).catch((e) => console.error('Areas error:', e));
  }, []);

  // Fetch alerts whenever remote query parameters change
  const fetchAlerts = async () => {
    setLoading(true);
    setError(null);
    try {
      let data: Alert[];
      const isCitywide = !selectedArea || CITYWIDE_AREAS.has(selectedArea.trim().toLowerCase());
      
      if (isMyLocationsOnly || selectedArea === 'My Saved Circles') {
        data = await api.getUserPersonalizedAlerts({
          status: selectedStatus || undefined,
          lang: language,
        });
      } else if (isCitywide) {
        data = await api.getAlerts({
          status: selectedStatus || undefined,
          search: searchQuery || undefined,
          lang: language,
        });
      } else {
        data = await api.getAlerts({
          area: selectedArea,
          status: selectedStatus || undefined,
          search: searchQuery || undefined,
          lang: language,
        });
      }
      setAlerts(data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch alerts');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAlerts();
  }, [selectedArea, isMyLocationsOnly, searchQuery, language]);

  // Authentic Hyderabad localities list for dropdown
  const localitiesList = useMemo(() => {
    return [...HYDERABAD_LOCALITIES].sort();
  }, []);

  // Category Multi-Select toggle handler
  const handleToggleCategory = (catId: string) => {
    setSelectedCategories((prev) => 
      prev.includes(catId) ? prev.filter((c) => c !== catId) : [...prev, catId]
    );
  };

  // Clear all filters handler
  const handleClearAllFilters = () => {
    setSelectedCategories([]);
    setSelectedSeverity('');
    setSelectedArea('');
    setIsMyLocationsOnly(false);
    setSearchQuery('');
    setSortBy('urgency');
    localStorage.removeItem('civicpulse_area');
  };

  // Client-side filtering & Urgency / Newest / Nearest sorting
  const processedAlerts = useMemo(() => {
    let list = [...alerts];

    // 1. Multi-category filtering (checks primary category + secondary_categories)
    if (selectedCategories.length > 0) {
      list = list.filter((a) => {
        const matchesPrimary = selectedCategories.includes(a.category);
        const matchesSecondary = a.secondary_categories && a.secondary_categories.some((sec) => selectedCategories.includes(sec));
        return matchesPrimary || matchesSecondary;
      });
    }

    // 2. Severity filtering
    if (selectedSeverity) {
      list = list.filter((a) => a.severity === selectedSeverity);
    }

    // 3. Sorting
    if (sortBy === 'urgency') {
      const SEVERITY_RANK: Record<string, number> = {
        critical: 4,
        warning: 3,
        advisory: 2,
        info: 1,
      };
      list.sort((a, b) => {
        // Higher severity first
        const rankDiff = (SEVERITY_RANK[b.severity] || 0) - (SEVERITY_RANK[a.severity] || 0);
        if (rankDiff !== 0) return rankDiff;

        // Soonest start time
        const aTime = a.start_time ? new Date(a.start_time).getTime() : Infinity;
        const bTime = b.start_time ? new Date(b.start_time).getTime() : Infinity;
        if (aTime !== bTime) return aTime - bTime;

        // Newest incident (id descending)
        return b.id - a.id;
      });
    } else if (sortBy === 'newest') {
      list.sort((a, b) => {
        const aTime = a.published_at ? new Date(a.published_at).getTime() : (a.created_at ? new Date(a.created_at).getTime() : 0);
        const bTime = b.published_at ? new Date(b.published_at).getTime() : (b.created_at ? new Date(b.created_at).getTime() : 0);
        if (bTime !== aTime) return bTime - aTime;
        return b.id - a.id;
      });
    } else if (sortBy === 'nearest') {
      list.sort((a, b) => {
        const aDist = a.distance_km != null ? a.distance_km : 999;
        const bDist = b.distance_km != null ? b.distance_km : 999;
        return aDist - bDist;
      });
    }

    return list;
  }, [alerts, selectedCategories, selectedSeverity, sortBy]);

  // Critical alerts for notification bell
  const criticalAlerts = useMemo(() => {
    return alerts.filter((a) => (a.severity === 'critical' || a.severity === 'warning') && a.status === 'active');
  }, [alerts]);

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 dark:bg-slate-900 text-slate-900 dark:text-slate-100 transition-colors">
      
      {/* Top Navbar */}
      <Header
        currentArea={selectedArea}
        onOpenLocation={() => setIsLocationModalOpen(true)}
        onResetLocation={() => handleSelectArea('')}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        darkMode={darkMode}
        setDarkMode={setDarkMode}
        language={language}
        setLanguage={(l) => {
          setLanguage(l);
          localStorage.setItem('civicpulse_lang', l);
        }}
        criticalAlerts={criticalAlerts}
        onSelectAlert={(a) => setSelectedAlertForModal(a)}
      />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        
        {/* TAB 1: FEED VIEW */}
        {activeTab === 'feed' && (
          <div>
            <FilterBar
              selectedCategories={selectedCategories}
              onToggleCategory={handleToggleCategory}
              onClearCategories={() => setSelectedCategories([])}
              selectedSeverity={selectedSeverity}
              onSelectSeverity={setSelectedSeverity}
              selectedLocality={selectedArea}
              onSelectLocality={handleSelectArea}
              localitiesList={localitiesList}
              isMyLocationsOnly={isMyLocationsOnly}
              onToggleMyLocations={() => setIsMyLocationsOnly(!isMyLocationsOnly)}
              sortBy={sortBy}
              onSelectSort={setSortBy}
              searchQuery={searchQuery}
              onSearchChange={setSearchQuery}
              totalCount={processedAlerts.length}
              onClearAllFilters={handleClearAllFilters}
              language={language}
            />

            {/* View Switcher: Cards vs Split Live Map */}
            <div className="flex items-center justify-between mb-4">
              <div className="text-xs font-semibold text-slate-500 dark:text-slate-400">
                Displaying <strong className="text-slate-800 dark:text-slate-200">{processedAlerts.length}</strong> verified incidents across Greater Hyderabad
              </div>
              <div className="flex items-center space-x-1 p-1 rounded-xl bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
                <button
                  onClick={() => setFeedViewMode('cards')}
                  className={`flex items-center space-x-1.5 px-3 py-1 rounded-lg text-xs font-semibold transition-all ${
                    feedViewMode === 'cards'
                      ? 'bg-white dark:bg-slate-700 text-blue-600 dark:text-blue-400 shadow-sm'
                      : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
                  }`}
                  title="View alerts in grid"
                >
                  <LayoutGrid className="w-3.5 h-3.5" />
                  <span>Grid View</span>
                </button>
                <button
                  onClick={() => setFeedViewMode('split')}
                  className={`flex items-center space-x-1.5 px-3 py-1 rounded-lg text-xs font-semibold transition-all ${
                    feedViewMode === 'split'
                      ? 'bg-white dark:bg-slate-700 text-blue-600 dark:text-blue-400 shadow-sm'
                      : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
                  }`}
                  title="View alerts with integrated geospatial map"
                >
                  <MapIcon className="w-3.5 h-3.5" />
                  <span>Map & Feed</span>
                </button>
              </div>
            </div>

            {/* Integrated Map in Feed View */}
            {feedViewMode === 'split' && processedAlerts.length > 0 && (
              <div className="mb-6 animate-in fade-in duration-200">
                <MapView
                  alerts={processedAlerts}
                  onSelectAlert={(a) => setSelectedAlertForModal(a)}
                  highlightAlertId={highlightAlertId}
                  height="420px"
                />
              </div>
            )}

            {loading ? (
              <div className="py-20 flex flex-col items-center justify-center space-y-3 text-slate-400">
                <RefreshCw className="w-8 h-8 animate-spin text-blue-500" />
                <p className="text-xs">Loading hyperlocal verified alerts from pipeline...</p>
              </div>
            ) : error ? (
              <div className="p-6 rounded-2xl bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-900 text-center space-y-2">
                <AlertCircle className="w-8 h-8 text-rose-500 mx-auto" />
                <h4 className="text-sm font-bold text-rose-800 dark:text-rose-300">Connection Error</h4>
                <p className="text-xs text-rose-600 dark:text-rose-400">{error}</p>
                <button
                  onClick={fetchAlerts}
                  className="mt-2 px-4 py-1.5 rounded-lg bg-rose-600 text-white text-xs font-semibold"
                >
                  Retry
                </button>
              </div>
            ) : processedAlerts.length === 0 ? (
              <div className="py-20 text-center space-y-3 bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 p-8">
                <Layers className="w-12 h-12 text-slate-300 dark:text-slate-600 mx-auto" />
                <h4 className="text-sm font-bold text-slate-700 dark:text-slate-300">No matching alerts found</h4>
                <p className="text-xs text-slate-500 dark:text-slate-400 max-w-md mx-auto">
                  Try clearing your search filters or selecting &apos;Overall Hyderabad&apos; to view citywide alerts.
                </p>
                <button
                  onClick={handleClearAllFilters}
                  className="px-4 py-2 rounded-xl bg-blue-50 dark:bg-blue-950/50 text-blue-600 dark:text-blue-400 text-xs font-semibold hover:bg-blue-100"
                >
                  Reset All Filters
                </button>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {processedAlerts.map((alert) => (
                  <AlertCard
                    key={alert.id}
                    alert={alert}
                    language={language}
                    onOpenDetails={(a) => setSelectedAlertForModal(a)}
                    onViewOnMap={(a) => {
                      setFeedViewMode('split');
                      setHighlightAlertId(a.id);
                      window.scrollTo({ top: 180, behavior: 'smooth' });
                    }}
                  />
                ))}
              </div>
            )}
          </div>
        )}

        {/* TAB 2: LIVE MAP VIEW */}
        {activeTab === 'map' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-base font-bold text-slate-900 dark:text-white">
                  Geospatial Civic Incident Map
                </h3>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  Visualizing verified alerts with geographic coordinates across Hyderabad localities.
                </p>
              </div>
              <span className="text-xs font-mono text-slate-500">
                {processedAlerts.length} Geotagged Incidents
              </span>
            </div>

            <MapView
              alerts={processedAlerts}
              onSelectAlert={(a) => setSelectedAlertForModal(a)}
              selectedAreaName={selectedArea}
              highlightAlertId={highlightAlertId}
              height="650px"
            />
          </div>
        )}

        {/* TAB 3: ADMIN & INGEST */}
        {activeTab === 'admin' && <AdminPanel />}

      </main>

      {/* Onboarding / Location Selector Modal */}
      <OnboardingModal
        isOpen={isLocationModalOpen}
        onClose={() => setIsLocationModalOpen(false)}
        areas={areas}
        selectedArea={selectedArea}
        onSelectArea={handleSelectArea}
        onProfileUpdated={fetchAlerts}
      />

      {/* Alert Detail Modal */}
      <AlertDetailModal
        alert={selectedAlertForModal}
        onClose={() => setSelectedAlertForModal(null)}
        language={language}
      />

      {/* Footer */}
      <footer className="border-t border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 py-6 px-4 text-center text-xs text-slate-500 dark:text-slate-400">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2">
          <div>
            <strong>CivicPulse</strong> — End-to-End Hyperlocal Civic Intelligence System.
          </div>
          <div className="text-slate-400">
            Greater Hyderabad Hyperlocal Civic Alerts
          </div>
        </div>
      </footer>

    </div>
  );
};

export default App;
