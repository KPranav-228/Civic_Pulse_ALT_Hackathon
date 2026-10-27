import React, { useState, useRef, useEffect, useMemo } from 'react';
import { 
  Car, 
  Droplet, 
  Zap, 
  CloudRain, 
  Landmark, 
  MoreHorizontal, 
  Search, 
  Filter,
  MapPin,
  Star,
  ArrowUpDown,
  RotateCcw,
  AlertOctagon,
  AlertTriangle,
  AlertCircle,
  Info,
  ChevronDown,
  Check
} from 'lucide-react';
import { I18N, Language } from '../services/i18n';

export type SortOption = 'urgency' | 'newest' | 'nearest';

interface FilterBarProps {
  selectedCategories: string[];
  onToggleCategory: (category: string) => void;
  onClearCategories: () => void;
  selectedSeverity: string;
  onSelectSeverity: (severity: string) => void;
  selectedLocality: string;
  onSelectLocality: (locality: string) => void;
  localitiesList: string[];
  isMyLocationsOnly: boolean;
  onToggleMyLocations: () => void;
  sortBy: SortOption;
  onSelectSort: (sort: SortOption) => void;
  searchQuery: string;
  onSearchChange: (query: string) => void;
  totalCount: number;
  onClearAllFilters: () => void;
  language?: Language;
}

export const FilterBar: React.FC<FilterBarProps> = ({
  selectedCategories,
  onToggleCategory,
  onClearCategories,
  selectedSeverity,
  onSelectSeverity,
  selectedLocality,
  onSelectLocality,
  localitiesList,
  isMyLocationsOnly,
  onToggleMyLocations,
  sortBy,
  onSelectSort,
  searchQuery,
  onSearchChange,
  totalCount,
  onClearAllFilters,
  language = 'en',
}) => {
  const t = I18N[language || 'en'];

  // Custom Dropdown Open & Search States
  const [isLocalityOpen, setIsLocalityOpen] = useState(false);
  const [localitySearch, setLocalitySearch] = useState('');
  const localityRef = useRef<HTMLDivElement>(null);

  const [isSortOpen, setIsSortOpen] = useState(false);
  const sortRef = useRef<HTMLDivElement>(null);

  // Close custom dropdowns on click outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (localityRef.current && !localityRef.current.contains(e.target as Node)) {
        setIsLocalityOpen(false);
      }
      if (sortRef.current && !sortRef.current.contains(e.target as Node)) {
        setIsSortOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Filter localities by user search input
  const filteredLocalities = useMemo(() => {
    if (!localitySearch.trim()) return localitiesList;
    const q = localitySearch.toLowerCase().trim();
    return localitiesList.filter((loc) => loc.toLowerCase().includes(q));
  }, [localitiesList, localitySearch]);

  const categories = [
    { id: 'road_closure', label: t.catRoadClosure, icon: Car },
    { id: 'water_supply', label: t.catWaterSupply, icon: Droplet },
    { id: 'power_cut', label: t.catPowerCut, icon: Zap },
    { id: 'severe_weather', label: t.catSevereWeather, icon: CloudRain },
    { id: 'public_service', label: t.catPublicService, icon: Landmark },
    { id: 'other', label: t.catOther, icon: MoreHorizontal },
  ];

  const severities = [
    { id: '', label: t.allSeverities, icon: Info, badgeClass: 'border-slate-300 dark:border-slate-700 text-slate-700 dark:text-slate-300' },
    { id: 'critical', label: t.sevCritical, icon: AlertOctagon, badgeClass: 'border-red-500 text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-950/30' },
    { id: 'warning', label: t.sevWarning, icon: AlertTriangle, badgeClass: 'border-orange-500 text-orange-600 dark:text-orange-400 bg-orange-50 dark:bg-orange-950/30' },
    { id: 'advisory', label: t.sevAdvisory, icon: AlertCircle, badgeClass: 'border-yellow-500 text-yellow-600 dark:text-yellow-400 bg-yellow-50 dark:bg-yellow-950/30' },
    { id: 'info', label: t.sevInfo, icon: Info, badgeClass: 'border-blue-500 text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-950/30' },
  ];

  const isFiltered = selectedCategories.length > 0 || 
    !!selectedSeverity || 
    (!!selectedLocality && !['', 'all', 'all hyderabad', 'overall hyderabad'].includes(selectedLocality.trim().toLowerCase())) ||
    isMyLocationsOnly || 
    searchQuery.trim().length > 0;

  return (
    <div className="bg-white dark:bg-slate-800/90 rounded-2xl p-4 shadow-sm border border-slate-200 dark:border-slate-700 mb-6 space-y-3.5">
      
      {/* Row 1: Search, Custom Locality Dropdown, My Locations Toggle, Custom Sort Dropdown */}
      <div className="flex flex-col lg:flex-row gap-3 items-stretch lg:items-center justify-between">
        
        {/* Search Input */}
        <div className="relative flex-1 min-w-[200px]">
          <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
          <input
            type="text"
            placeholder={t.searchPlaceholder}
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            aria-label="Search alerts"
            className="w-full pl-9 pr-4 py-1.5 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Custom Locality Dropdown (Theme-Aware, High Visibility) */}
        <div ref={localityRef} className="relative">
          <button
            type="button"
            onClick={() => setIsLocalityOpen(!isLocalityOpen)}
            aria-expanded={isLocalityOpen}
            aria-label="Filter by Hyderabad locality"
            className={`flex items-center space-x-2 px-3 py-1.5 rounded-xl border text-xs font-semibold transition-all focus:outline-none focus:ring-2 focus:ring-blue-500 ${
              selectedLocality
                ? 'bg-blue-50 dark:bg-blue-950/60 border-blue-400 dark:border-blue-600 text-blue-700 dark:text-blue-300 shadow-sm'
                : 'bg-slate-50 dark:bg-slate-900 border-slate-200 dark:border-slate-700 text-slate-800 dark:text-slate-200 hover:border-slate-300 dark:hover:border-slate-600'
            }`}
          >
            <MapPin className="w-3.5 h-3.5 text-blue-500 shrink-0" />
            <span className="max-w-[170px] truncate">
              {selectedLocality || 'Overall Hyderabad (Citywide)'}
            </span>
            <ChevronDown className={`w-3.5 h-3.5 text-slate-400 transition-transform ${isLocalityOpen ? 'rotate-180' : ''}`} />
          </button>

          {/* Floating Dropdown Popover */}
          {isLocalityOpen && (
            <div className="absolute left-0 mt-1.5 w-64 bg-white dark:bg-slate-800 rounded-xl shadow-xl border border-slate-200 dark:border-slate-700 py-2 z-50 animate-in fade-in slide-in-from-top-1 duration-150">
              
              {/* Locality Search Input */}
              <div className="px-2.5 pb-2 border-b border-slate-100 dark:border-slate-700">
                <div className="relative">
                  <Search className="w-3 h-3 absolute left-2.5 top-2.5 text-slate-400" />
                  <input
                    type="text"
                    placeholder="Search Hyderabad locality..."
                    value={localitySearch}
                    onChange={(e) => setLocalitySearch(e.target.value)}
                    autoFocus
                    className="w-full pl-7 pr-2.5 py-1 text-xs rounded-lg bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  />
                </div>
              </div>

              {/* Options List */}
              <div className="max-h-60 overflow-y-auto py-1">
                {/* Citywide Option */}
                <button
                  type="button"
                  onClick={() => {
                    onSelectLocality('');
                    setIsLocalityOpen(false);
                    setLocalitySearch('');
                  }}
                  className={`w-full px-3 py-1.5 text-left text-xs font-semibold flex items-center justify-between transition-colors ${
                    !selectedLocality
                      ? 'bg-blue-50 dark:bg-blue-950/70 text-blue-700 dark:text-blue-300 font-bold'
                      : 'text-slate-800 dark:text-slate-100 hover:bg-slate-100 dark:hover:bg-slate-700/60'
                  }`}
                >
                  <span>Overall Hyderabad (Citywide)</span>
                  {!selectedLocality && <Check className="w-3.5 h-3.5 text-blue-600 dark:text-blue-400" />}
                </button>

                <div className="my-1 border-t border-slate-100 dark:border-slate-700/60" />

                {/* Localities List */}
                {filteredLocalities.map((loc) => {
                  const isSelected = selectedLocality === loc;
                  return (
                    <button
                      key={loc}
                      type="button"
                      onClick={() => {
                        onSelectLocality(loc);
                        setIsLocalityOpen(false);
                        setLocalitySearch('');
                      }}
                      className={`w-full px-3 py-1.5 text-left text-xs flex items-center justify-between transition-colors ${
                        isSelected
                          ? 'bg-blue-50 dark:bg-blue-950/70 text-blue-700 dark:text-blue-300 font-bold'
                          : 'text-slate-800 dark:text-slate-100 hover:bg-slate-100 dark:hover:bg-slate-700/60'
                      }`}
                    >
                      <span>{loc}</span>
                      {isSelected && <Check className="w-3.5 h-3.5 text-blue-600 dark:text-blue-400" />}
                    </button>
                  );
                })}

                {filteredLocalities.length === 0 && (
                  <div className="px-3 py-3 text-xs text-slate-400 text-center">
                    No matching locality found
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* "My Locations" Toggle */}
        <button
          type="button"
          onClick={onToggleMyLocations}
          aria-pressed={isMyLocationsOnly}
          className={`flex items-center justify-center space-x-1.5 px-3 py-1.5 rounded-xl text-xs font-bold transition-all focus:outline-none focus:ring-2 focus:ring-blue-500 ${
            isMyLocationsOnly
              ? 'bg-amber-500 text-white shadow-sm ring-2 ring-amber-400/50'
              : 'bg-slate-100 dark:bg-slate-700/60 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700 border border-slate-200 dark:border-slate-600'
          }`}
          title="Toggle alerts strictly affecting your saved home/office circles"
        >
          <Star className={`w-3.5 h-3.5 ${isMyLocationsOnly ? 'fill-current' : 'text-amber-500'}`} />
          <span>My Locations</span>
        </button>

        {/* Custom Sort Dropdown */}
        <div ref={sortRef} className="relative">
          <button
            type="button"
            onClick={() => setIsSortOpen(!isSortOpen)}
            aria-expanded={isSortOpen}
            aria-label="Sort alerts"
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 text-slate-800 dark:text-slate-200 text-xs font-semibold transition-all hover:border-slate-300 dark:hover:border-slate-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <ArrowUpDown className="w-3.5 h-3.5 text-slate-400 shrink-0" />
            <span className="text-slate-500 dark:text-slate-400 font-normal">Sort:</span>
            <span>
              {sortBy === 'urgency' ? 'Urgency' : sortBy === 'newest' ? 'Newest First' : 'Nearest Distance'}
            </span>
            <ChevronDown className={`w-3.5 h-3.5 text-slate-400 transition-transform ${isSortOpen ? 'rotate-180' : ''}`} />
          </button>

          {isSortOpen && (
            <div className="absolute right-0 mt-1.5 w-52 bg-white dark:bg-slate-800 rounded-xl shadow-xl border border-slate-200 dark:border-slate-700 py-1.5 z-50 animate-in fade-in slide-in-from-top-1 duration-150">
              {[
                { id: 'urgency' as SortOption, label: 'Urgency (Severity & Soonest)' },
                { id: 'newest' as SortOption, label: 'Newest First' },
                { id: 'nearest' as SortOption, label: 'Nearest Distance' },
              ].map(({ id, label }) => {
                const isSelected = sortBy === id;
                return (
                  <button
                    key={id}
                    type="button"
                    onClick={() => {
                      onSelectSort(id);
                      setIsSortOpen(false);
                    }}
                    className={`w-full px-3 py-1.5 text-left text-xs flex items-center justify-between transition-colors ${
                      isSelected
                        ? 'bg-blue-50 dark:bg-blue-950/70 text-blue-700 dark:text-blue-300 font-bold'
                        : 'text-slate-800 dark:text-slate-100 hover:bg-slate-100 dark:hover:bg-slate-700/60'
                    }`}
                  >
                    <span>{label}</span>
                    {isSelected && <Check className="w-3.5 h-3.5 text-blue-600 dark:text-blue-400" />}
                  </button>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Row 2: Multi-Select Category Chips (Horizontally scrollable on mobile) */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-1 scrollbar-none">
        {/* All Categories Chip */}
        <button
          type="button"
          onClick={onClearCategories}
          aria-pressed={selectedCategories.length === 0}
          className={`flex items-center space-x-1 px-3 py-1.5 rounded-xl text-xs whitespace-nowrap font-semibold transition-all focus:outline-none focus:ring-2 focus:ring-blue-500 ${
            selectedCategories.length === 0
              ? 'bg-blue-600 text-white shadow-sm'
              : 'bg-slate-50 dark:bg-slate-900/60 text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700/60 border border-slate-200 dark:border-slate-700'
          }`}
        >
          <Filter className="w-3.5 h-3.5" />
          <span>All Categories</span>
        </button>

        {/* Category Multi-select Chips */}
        {categories.map(({ id, label, icon: Icon }) => {
          const isSelected = selectedCategories.includes(id);
          return (
            <button
              key={id}
              type="button"
              onClick={() => onToggleCategory(id)}
              aria-pressed={isSelected}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-xl text-xs whitespace-nowrap transition-all font-semibold focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                isSelected
                  ? 'bg-blue-600 text-white shadow-sm ring-1 ring-blue-700'
                  : 'bg-slate-50 dark:bg-slate-900/60 text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700/60 border border-slate-200 dark:border-slate-700'
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              <span>{label}</span>
              {isSelected && <span className="ml-0.5 text-[10px] font-bold">✓</span>}
            </button>
          );
        })}
      </div>

      {/* Row 3: Severity Filter, Severity Accessibility Legend, Results Count & Clear Button */}
      <div className="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-slate-100 dark:border-slate-700/60">
        
        {/* Severity Filter Pills */}
        <div className="flex flex-wrap items-center gap-1.5">
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 mr-1">
            Severity:
          </span>
          {severities.map(({ id, label, icon: SevIcon, badgeClass }) => {
            const isSelected = selectedSeverity === id;
            return (
              <button
                key={id}
                type="button"
                onClick={() => onSelectSeverity(id)}
                aria-pressed={isSelected}
                className={`flex items-center space-x-1 px-2.5 py-0.5 rounded-lg text-[11px] font-semibold border transition-all focus:outline-none focus:ring-2 focus:ring-blue-500 ${badgeClass} ${
                  isSelected ? 'ring-2 ring-blue-500 ring-offset-1 dark:ring-offset-slate-800 font-bold' : 'opacity-85 hover:opacity-100'
                }`}
              >
                {id && <SevIcon className="w-3 h-3" />}
                <span>{label}</span>
              </button>
            );
          })}
        </div>

        {/* Results Count & Clear Filters Button */}
        <div className="flex items-center space-x-3 text-xs">
          <span className="font-bold text-slate-700 dark:text-slate-300">
            {totalCount} {t.alertsFound}
          </span>

          {isFiltered && (
            <button
              type="button"
              onClick={onClearAllFilters}
              className="flex items-center space-x-1 px-2.5 py-1 rounded-lg text-xs font-semibold text-rose-600 dark:text-rose-400 bg-rose-50 dark:bg-rose-950/40 hover:bg-rose-100 dark:hover:bg-rose-900/60 border border-rose-200 dark:border-rose-800 transition-colors focus:outline-none focus:ring-2 focus:ring-rose-500"
              title="Reset all search, category, and severity filters"
            >
              <RotateCcw className="w-3 h-3" />
              <span>Clear filters</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
