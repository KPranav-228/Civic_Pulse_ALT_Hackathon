import React from 'react';
import { 
  X, 
  MapPin, 
  Clock, 
  ShieldAlert, 
  ExternalLink, 
  FileText, 
  CheckCircle, 
  Sparkles,
  Info
} from 'lucide-react';
import { Alert, formatAffectedAreas } from '../types';
import { XAIPanel } from './XAIPanel';
import { I18N, Language } from '../services/i18n';

interface AlertDetailModalProps {
  alert: Alert | null;
  onClose: () => void;
  language?: Language;
}

export const AlertDetailModal: React.FC<AlertDetailModalProps> = ({ alert, onClose, language = 'en' }) => {
  if (!alert) return null;
  const t = I18N[language || 'en'];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-in fade-in duration-150">
      <div 
        className="bg-white dark:bg-slate-800 rounded-2xl max-w-2xl w-full max-h-[90vh] flex flex-col shadow-2xl border border-slate-200 dark:border-slate-700 relative overflow-hidden"
        role="dialog"
        aria-modal="true"
      >
        {/* Header */}
        <div className="p-6 border-b border-slate-200 dark:border-slate-700 flex items-start justify-between">
          <div className="space-y-1 pr-6">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-blue-100 dark:bg-blue-950 text-blue-700 dark:text-blue-300">
                {alert.category.replace('_', ' ')}
              </span>
              <span className={`text-xs font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full ${
                alert.severity === 'critical' ? 'bg-red-100 text-red-700 dark:bg-red-950 dark:text-red-300' :
                alert.severity === 'warning' ? 'bg-orange-100 text-orange-700 dark:bg-orange-950 dark:text-orange-300' :
                alert.severity === 'advisory' ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-950 dark:text-yellow-300' :
                'bg-blue-100 text-blue-700 dark:bg-blue-950 dark:text-blue-300'
              }`}>
                {alert.severity}
              </span>
              <span className={`text-xs font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full ${
                alert.source_tier === 'official' ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300' :
                alert.source_tier === 'news' ? 'bg-indigo-100 text-indigo-800 dark:bg-indigo-950 dark:text-indigo-300' :
                'bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300'
              }`}>
                {alert.source_tier} Tier
              </span>
              <span className="text-xs text-slate-400 capitalize">Status: {alert.status}</span>
            </div>
            <h2 className="text-xl font-bold text-slate-900 dark:text-white leading-tight">
              {alert.title}
            </h2>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
            aria-label="Close modal"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Scrollable Body */}
        <div className="p-6 overflow-y-auto space-y-5">
          {/* Metadata badges */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs bg-slate-50 dark:bg-slate-900/40 p-3 rounded-xl border border-slate-100 dark:border-slate-800">
            <div className="flex items-center space-x-2 text-slate-600 dark:text-slate-300">
              <MapPin className="w-4 h-4 text-blue-500 shrink-0" />
              <span><strong>Areas:</strong> {formatAffectedAreas(alert.affected_areas)}</span>
            </div>
            <div className="flex items-center space-x-2 text-slate-600 dark:text-slate-300">
              <Clock className="w-4 h-4 text-slate-400 shrink-0" />
              <span><strong>Window:</strong> {alert.start_time ? new Date(alert.start_time).toLocaleString() : 'Immediate'}</span>
            </div>
            <div className="flex items-center space-x-2 text-slate-600 dark:text-slate-300">
              <ShieldAlert className="w-4 h-4 text-emerald-500 shrink-0" />
              <span><strong>Source:</strong> {alert.source_name}</span>
            </div>
            <div className="flex items-center space-x-2 text-slate-600 dark:text-slate-300">
              <Info className="w-4 h-4 text-indigo-500 shrink-0" />
              <span><strong>Pipeline Confidence:</strong> {(alert.confidence * 100).toFixed(1)}%</span>
            </div>
          </div>

          {/* Unverified Rumor Warning */}
          {alert.source_tier === 'unverified' && (
            <div className="p-3 rounded-xl bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900/60 text-xs text-amber-900 dark:text-amber-200 leading-relaxed">
              <strong>⚠️ Caution - Unverified Incident:</strong> This alert was ingested from a non-official crowd/community report without municipal corroboration. Please verify with local authorities before taking safety actions.
            </div>
          )}

          {/* Linked Parent Alert */}
          {alert.parent_alert_id && (
            <div className="p-3 rounded-xl bg-purple-50 dark:bg-purple-950/40 border border-purple-200 dark:border-purple-900/60 text-xs text-purple-900 dark:text-purple-200 leading-relaxed">
              <strong>🔗 Event History:</strong> This announcement updates previously reported incident <strong>#{alert.parent_alert_id}</strong>. The prior record has been marked as <em>{alert.status}</em> to prevent stale alert overload.
            </div>
          )}

          {/* Expected Impact */}
          {alert.expected_impact && (
            <div>
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-1">
                Expected Citizen Impact
              </h4>
              <p className="text-sm text-slate-800 dark:text-slate-200 leading-relaxed bg-blue-50/50 dark:bg-blue-950/20 p-3 rounded-xl border border-blue-100 dark:border-blue-900/40">
                {alert.expected_impact}
              </p>
            </div>
          )}

          {/* Action Steps */}
          {alert.recommended_actions && alert.recommended_actions.length > 0 && (
            <div>
              <div className="flex items-center justify-between mb-2">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                  Citizen Advisory Action Plan
                </h4>
                {alert.profile_tags && alert.profile_tags.length > 0 && (
                  <span className="text-[10px] text-indigo-600 dark:text-indigo-400 font-semibold flex items-center space-x-1">
                    <Sparkles className="w-3 h-3" />
                    <span>Personalized for your household</span>
                  </span>
                )}
              </div>

              {/* Profile Tags */}
              {alert.profile_tags && alert.profile_tags.length > 0 && (
                <div className="flex flex-wrap gap-1.5 mb-2">
                  {alert.profile_tags.map((t, idx) => (
                    <span
                      key={idx}
                      className="px-2 py-0.5 rounded-md text-[10px] font-bold bg-indigo-50 dark:bg-indigo-950/60 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-850"
                    >
                      {t}
                    </span>
                  ))}
                </div>
              )}

              {/* Personalized Notes */}
              {alert.personalized_notes && alert.personalized_notes.length > 0 && (
                <div className="mb-2.5 p-2 rounded-xl bg-indigo-50/60 dark:bg-indigo-950/40 border border-indigo-100 dark:border-indigo-900/60 text-xs text-indigo-900 dark:text-indigo-200 space-y-1">
                  {alert.personalized_notes.map((note, i) => (
                    <div key={i} className="flex items-start space-x-1.5">
                      <span className="text-indigo-500 font-bold">•</span>
                      <span>{note}</span>
                    </div>
                  ))}
                </div>
              )}

              <ul className="space-y-1.5">
                {alert.recommended_actions.map((act, i) => (
                  <li key={i} className="flex items-start space-x-2 text-xs text-slate-700 dark:text-slate-300">
                    <CheckCircle className="w-4 h-4 text-emerald-500 shrink-0 mt-0.5" />
                    <span>{act}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Original News / Announcement Excerpt */}
          {alert.original_text && (
            <div>
              <div className="flex items-center space-x-1.5 text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-1">
                <FileText className="w-4 h-4" />
                <span>Original Ingested Report Excerpt</span>
              </div>
              <div className="p-3 bg-slate-100 dark:bg-slate-900 rounded-xl text-xs font-mono text-slate-700 dark:text-slate-300 whitespace-pre-wrap leading-relaxed max-h-40 overflow-y-auto border border-slate-200 dark:border-slate-800">
                {alert.original_text}
              </div>
            </div>
          )}

          {/* XAI Attribution Module */}
          <div>
            <XAIPanel alertId={alert.id} />
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 bg-slate-50 dark:bg-slate-900/80 border-t border-slate-200 dark:border-slate-700 flex justify-between items-center">
          <div className="text-[11px] text-slate-500 dark:text-slate-400">
            {alert.source_url ? (
              <a 
                href={alert.source_url} 
                target="_blank" 
                rel="noreferrer" 
                className="text-blue-600 dark:text-blue-400 hover:underline flex items-center space-x-1"
              >
                <span>Read official release</span>
                <ExternalLink className="w-3.5 h-3.5" />
              </a>
            ) : (
              <span>Verified local announcement</span>
            )}
          </div>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-xl bg-slate-200 dark:bg-slate-700 text-slate-800 dark:text-slate-200 text-xs font-semibold hover:bg-slate-300 dark:hover:bg-slate-600 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
