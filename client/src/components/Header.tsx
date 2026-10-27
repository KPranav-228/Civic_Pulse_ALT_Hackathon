import React from 'react';
import { 
  ShieldAlert, 
  MapPin, 
  Bell, 
  Moon, 
  Sun, 
  CheckCircle2,
  AlertTriangle,
  X
} from 'lucide-react';
import { Alert, formatAffectedAreas } from '../types';
import { I18N, Language } from '../services/i18n';

interface HeaderProps {
  currentArea: string;
  onOpenLocation: () => void;
  onResetLocation?: () => void;
  activeTab: 'feed' | 'map' | 'admin';
  setActiveTab: (tab: 'feed' | 'map' | 'admin') => void;
  darkMode: boolean;
  setDarkMode: (val: boolean) => void;
  language?: Language;
  setLanguage?: (lang: Language) => void;
  criticalAlerts: Alert[];
  onSelectAlert: (alert: Alert) => void;
}

export const Header: React.FC<HeaderProps> = ({
  currentArea,
  onOpenLocation,
  onResetLocation,
  activeTab,
  setActiveTab,
  darkMode,
  setDarkMode,
  language = 'en',
  setLanguage,
  criticalAlerts,
  onSelectAlert,
}) => {
  const [showBellDropdown, setShowBellDropdown] = React.useState(false);
  const t = I18N[language || 'en'];

  const isLocalityFiltered = !!currentArea && ![
    '', 'all', 'all hyderabad', 'overall hyderabad', 
    'overall hyderabad (all zones)', 'all hyderabad localities', 'citywide'
  ].includes(currentArea.trim().toLowerCase());

  return (
    <header className="sticky top-0 z-40 bg-white/90 dark:bg-slate-900/90 backdrop-blur-md border-b border-slate-200 dark:border-slate-800 transition-colors">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          
          {/* Logo & Civic Branding */}
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center text-white shadow-md shadow-blue-500/20">
              <ShieldAlert className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-bold text-xl tracking-tight text-slate-900 dark:text-white">
                  {t.appTitle}
                </span>
                <span className="text-[10px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded-full bg-blue-100 dark:bg-blue-900/50 text-blue-700 dark:text-blue-300">
                  Live NLP
                </span>
              </div>
              <p className="text-xs text-slate-500 dark:text-slate-400 hidden sm:block">
                {t.tagline}
              </p>
            </div>
          </div>

          {/* Area Selector & Reset Button */}
          <div className="flex items-center space-x-1.5">
            <button
              onClick={onOpenLocation}
              className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg border text-xs font-medium transition-all hover:shadow-sm ${
                isLocalityFiltered
                  ? 'border-blue-400 bg-blue-50 dark:bg-blue-950/40 text-blue-700 dark:text-blue-300'
                  : 'border-slate-200 dark:border-slate-700 hover:border-blue-400 dark:hover:border-blue-500 bg-slate-50 dark:bg-slate-800/80 text-slate-700 dark:text-slate-200'
              }`}
              title="Change monitored locality / View All Hyderabad"
            >
              <MapPin className="w-4 h-4 text-blue-600 dark:text-blue-400" />
              <span className="font-semibold">{currentArea || t.allLocalities}</span>
            </button>

            {/* Instant Clear to Overall Hyderabad */}
            {isLocalityFiltered && onResetLocation && (
              <button
                onClick={onResetLocation}
                title={t.resetToCitywide}
                className="flex items-center space-x-1 px-2 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-500 hover:text-rose-600 hover:border-rose-300 dark:hover:border-rose-800 text-xs font-medium transition-colors"
              >
                <X className="w-3.5 h-3.5" />
                <span className="hidden sm:inline text-[11px] font-bold">All Hyderabad</span>
              </button>
            )}
          </div>

          {/* Navigation Tabs */}
          <nav className="hidden md:flex items-center space-x-1">
            <button
              onClick={() => setActiveTab('feed')}
              className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-all ${
                activeTab === 'feed'
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800'
              }`}
            >
              {t.feedTab}
            </button>
            <button
              onClick={() => setActiveTab('map')}
              className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-all ${
                activeTab === 'map'
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800'
              }`}
            >
              {t.mapTab}
            </button>
            <button
              onClick={() => setActiveTab('admin')}
              className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-all ${
                activeTab === 'admin'
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800'
              }`}
            >
              {t.adminTab}
            </button>
          </nav>

          {/* Right Controls: Notification Bell, Language Selector, Dark Mode */}
          <div className="flex items-center space-x-2">
            
            {/* Notification Bell */}
            <div className="relative">
              <button
                onClick={() => setShowBellDropdown(!showBellDropdown)}
                className="relative p-2 rounded-lg text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                aria-label="High severity alerts notification"
              >
                <Bell className="w-5 h-5" />
                {criticalAlerts.length > 0 && (
                  <span className="absolute top-1 right-1 flex h-4 w-4 items-center justify-center rounded-full bg-red-600 text-[10px] font-bold text-white animate-pulse">
                    {criticalAlerts.length}
                  </span>
                )}
              </button>

              {/* Notification Dropdown */}
              {showBellDropdown && (
                <div className="absolute right-0 mt-2 w-80 sm:w-96 bg-white dark:bg-slate-800 rounded-xl shadow-xl border border-slate-200 dark:border-slate-700 py-2 z-50 animate-in fade-in slide-in-from-top-2 duration-150">
                  <div className="px-4 py-2 border-b border-slate-100 dark:border-slate-700 flex items-center justify-between">
                    <span className="font-semibold text-xs uppercase tracking-wider text-slate-700 dark:text-slate-200 flex items-center space-x-1.5">
                      <AlertTriangle className="w-4 h-4 text-amber-500" />
                      <span>Priority Disruption Alerts</span>
                    </span>
                    <span className="text-[11px] text-slate-500">{criticalAlerts.length} Active</span>
                  </div>

                  <div className="max-h-72 overflow-y-auto divide-y divide-slate-100 dark:divide-slate-700/50">
                    {criticalAlerts.length === 0 ? (
                      <div className="p-4 text-center text-xs text-slate-500 flex flex-col items-center">
                        <CheckCircle2 className="w-8 h-8 text-emerald-500 mb-1" />
                        No critical or warning disruptions in your area!
                      </div>
                    ) : (
                      criticalAlerts.slice(0, 5).map((alert) => (
                        <div
                          key={alert.id}
                          onClick={() => {
                            onSelectAlert(alert);
                            setShowBellDropdown(false);
                          }}
                          className="p-3 hover:bg-slate-50 dark:hover:bg-slate-700/50 cursor-pointer transition-colors"
                        >
                          <div className="flex items-center space-x-2">
                            <span className={`w-2 h-2 rounded-full ${alert.severity === 'critical' ? 'bg-red-500' : 'bg-orange-500'}`} />
                            <span className="font-semibold text-xs text-slate-900 dark:text-slate-100 truncate">
                              {alert.title}
                            </span>
                          </div>
                          <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1 line-clamp-1">
                            {alert.expected_impact}
                          </p>
                          <div className="flex items-center justify-between mt-1 text-[10px] text-slate-400">
                            <span>{formatAffectedAreas(alert.affected_areas)}</span>
                            <span className="uppercase font-semibold">{alert.category.replace('_', ' ')}</span>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Language Toggle: EN / తె / हिं */}
            {setLanguage && (
              <div 
                className="flex items-center rounded-lg bg-slate-100 dark:bg-slate-800 p-0.5 border border-slate-200 dark:border-slate-700"
                role="group"
                aria-label="Language selection toggle"
              >
                {[
                  { code: 'en' as Language, label: 'EN', title: 'English' },
                  { code: 'te' as Language, label: 'తె', title: 'తెలుగు (Telugu)' },
                  { code: 'hi' as Language, label: 'हिं', title: 'हिंदी (Hindi)' },
                ].map(({ code, label, title }) => (
                  <button
                    key={code}
                    onClick={() => setLanguage(code)}
                    className={`px-2 py-1 text-xs font-bold rounded-md transition-all focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                      (language || 'en') === code
                        ? 'bg-blue-600 text-white shadow-sm'
                        : 'text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white'
                    }`}
                    title={title}
                    aria-label={`Switch language to ${title}`}
                  >
                    {label}
                  </button>
                ))}
              </div>
            )}

            {/* Dark Mode Toggle */}
            <button
              onClick={() => setDarkMode(!darkMode)}
              className="p-2 rounded-lg text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
              aria-label="Toggle dark mode"
            >
              {darkMode ? <Sun className="w-5 h-5 text-amber-400" /> : <Moon className="w-5 h-5" />}
            </button>
          </div>

        </div>

        {/* Mobile Navigation bar */}
        <div className="flex md:hidden border-t border-slate-200 dark:border-slate-800 py-2 space-x-1 justify-around">
          <button
            onClick={() => setActiveTab('feed')}
            className={`px-3 py-1 text-xs font-medium rounded-lg ${activeTab === 'feed' ? 'bg-blue-600 text-white' : 'text-slate-600 dark:text-slate-400'}`}
          >
            {t.feedTab}
          </button>
          <button
            onClick={() => setActiveTab('map')}
            className={`px-3 py-1 text-xs font-medium rounded-lg ${activeTab === 'map' ? 'bg-blue-600 text-white' : 'text-slate-600 dark:text-slate-400'}`}
          >
            {t.mapTab}
          </button>
          <button
            onClick={() => setActiveTab('admin')}
            className={`px-3 py-1 text-xs font-medium rounded-lg ${activeTab === 'admin' ? 'bg-blue-600 text-white' : 'text-slate-600 dark:text-slate-400'}`}
          >
            {t.adminTab}
          </button>
        </div>

      </div>

      {/* Official AI Disclaimer Banner */}
      <div className="bg-slate-100 dark:bg-slate-800/60 border-t border-b border-slate-200 dark:border-slate-800 py-1 px-4 text-center">
        <p className="text-[11px] text-slate-500 dark:text-slate-400">
          {t.disclaimer}
        </p>
      </div>
    </header>
  );
};
