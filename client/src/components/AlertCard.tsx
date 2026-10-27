import React, { useState, useEffect } from 'react';
import { 
  Car, 
  Droplet, 
  Zap, 
  CloudRain, 
  Landmark, 
  MoreHorizontal, 
  Clock, 
  MapPin, 
  ExternalLink, 
  Sparkles, 
  CheckSquare, 
  Square,
  ShieldCheck,
  AlertTriangle,
  AlertOctagon,
  AlertCircle,
  Info,
  ChevronDown,
  ChevronUp,
  Link as LinkIcon,
  Volume2,
  VolumeX,
  ThumbsUp,
  ThumbsDown,
  Flag,
  Check
} from 'lucide-react';
import { Alert, Category, Severity, formatAffectedAreas } from '../types';
import { XAIPanel } from './XAIPanel';
import { api } from '../services/api';
import { I18N, Language } from '../services/i18n';

interface AlertCardProps {
  alert: Alert;
  onOpenDetails: (alert: Alert) => void;
  onViewOnMap?: (alert: Alert) => void;
  language?: Language;
}

const CATEGORY_ICONS: Record<Category, React.FC<{ className?: string }>> = {
  road_closure: Car,
  water_supply: Droplet,
  power_cut: Zap,
  severe_weather: CloudRain,
  public_service: Landmark,
  other: MoreHorizontal,
};

const SEVERITY_STYLES: Record<Severity, { border: string; bgBadge: string; textBadge: string; dot: string }> = {
  critical: {
    border: 'border-l-4 border-l-red-500 hover:border-red-400',
    bgBadge: 'bg-red-100 dark:bg-red-950/60',
    textBadge: 'text-red-700 dark:text-red-300 border-red-200 dark:border-red-900',
    dot: 'bg-red-500',
  },
  warning: {
    border: 'border-l-4 border-l-orange-500 hover:border-orange-400',
    bgBadge: 'bg-orange-100 dark:bg-orange-950/60',
    textBadge: 'text-orange-700 dark:text-orange-300 border-orange-200 dark:border-orange-900',
    dot: 'bg-orange-500',
  },
  advisory: {
    border: 'border-l-4 border-l-yellow-500 hover:border-yellow-400',
    bgBadge: 'bg-yellow-100 dark:bg-yellow-950/60',
    textBadge: 'text-yellow-700 dark:text-yellow-300 border-yellow-200 dark:border-yellow-900',
    dot: 'bg-yellow-500',
  },
  info: {
    border: 'border-l-4 border-l-blue-500 hover:border-blue-400',
    bgBadge: 'bg-blue-100 dark:bg-blue-950/60',
    textBadge: 'text-blue-700 dark:text-blue-300 border-blue-200 dark:border-blue-900',
    dot: 'bg-blue-500',
  },
};

const SEVERITY_ICONS: Record<Severity, React.FC<{ className?: string }>> = {
  critical: AlertOctagon,
  warning: AlertTriangle,
  advisory: AlertCircle,
  info: Info,
};

function formatRelativeTime(dateStr?: string | null): string {
  if (!dateStr) return '';
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  if (isNaN(diffMs)) return '';
  const diffSec = Math.floor(diffMs / 1000);
  if (diffSec < 60) return 'Just now';
  const diffMin = Math.floor(diffSec / 60);
  if (diffMin < 60) return `${diffMin}m ago`;
  const diffHrs = Math.floor(diffMin / 60);
  if (diffHrs < 24) return `${diffHrs}h ago`;
  const diffDays = Math.floor(diffHrs / 24);
  return `${diffDays}d ago`;
}

function getTimeWindowChip(start?: string | null, end?: string | null): string | null {
  if (!start && !end) return null;
  const now = new Date();
  
  if (start && end) {
    const sDate = new Date(start);
    const eDate = new Date(end);
    if (!isNaN(sDate.getTime()) && !isNaN(eDate.getTime())) {
      const isToday = sDate.toDateString() === now.toDateString();
      const sStr = sDate.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
      const eStr = eDate.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
      if (isToday) {
        if (now >= sDate && now <= eDate) {
          return `Ongoing (Today ${sStr} – ${eStr})`;
        }
        if (now < sDate) {
          const diffHours = Math.round((sDate.getTime() - now.getTime()) / (1000 * 60 * 60));
          return diffHours <= 6 && diffHours > 0 
            ? `Starts in ${diffHours}h (Today ${sStr} – ${eStr})` 
            : `Today ${sStr} – ${eStr}`;
        }
        return `Today ${sStr} – ${eStr}`;
      }
      return `${sDate.toLocaleDateString([], { month: 'short', day: 'numeric' })} ${sStr} – ${eStr}`;
    }
  }

  if (start) {
    const sDate = new Date(start);
    if (!isNaN(sDate.getTime())) {
      if (sDate > now) {
        const diffHours = Math.round((sDate.getTime() - now.getTime()) / (1000 * 60 * 60));
        return diffHours > 0 && diffHours <= 12 
          ? `Starts in ${diffHours}h` 
          : `Starts ${sDate.toLocaleDateString([], { month: 'short', day: 'numeric', hour: 'numeric' })}`;
      }
      return 'Ongoing';
    }
  }

  if (end) {
    const eDate = new Date(end);
    if (!isNaN(eDate.getTime())) {
      return eDate > now ? `Until ${eDate.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })}` : 'Ended';
    }
  }

  return null;
}

export const AlertCard: React.FC<AlertCardProps> = ({ 
  alert, 
  onOpenDetails, 
  onViewOnMap, 
  language = 'en' 
}) => {
  const [showXAI, setShowXAI] = useState(false);
  const [checkedActions, setCheckedActions] = useState<Record<number, boolean>>({});
  const [isPlayingTTS, setIsPlayingTTS] = useState(false);
  const [hasVoice, setHasVoice] = useState(true);
  const t = I18N[language || 'en'];

  // Check TTS voice availability for the selected language
  useEffect(() => {
    if (typeof window === 'undefined' || !('speechSynthesis' in window)) {
      setHasVoice(false);
      return;
    }
    const checkVoices = () => {
      const voices = window.speechSynthesis.getVoices();
      if (!voices || voices.length === 0) return;
      const targetLangPrefix = language === 'te' ? 'te' : language === 'hi' ? 'hi' : 'en';
      const match = voices.some(v => v.lang && v.lang.toLowerCase().startsWith(targetLangPrefix));
      setHasVoice(match);
    };
    checkVoices();
    if (window.speechSynthesis.onvoiceschanged !== undefined) {
      window.speechSynthesis.onvoiceschanged = checkVoices;
    }
  }, [language]);

  // Localized category and severity
  const categoryLabel = 
    alert.category === 'road_closure' ? t.catRoadClosure :
    alert.category === 'water_supply' ? t.catWaterSupply :
    alert.category === 'power_cut' ? t.catPowerCut :
    alert.category === 'severe_weather' ? t.catSevereWeather :
    alert.category === 'public_service' ? t.catPublicService :
    t.catOther;

  const severityLabel =
    alert.severity === 'critical' ? t.sevCritical :
    alert.severity === 'warning' ? t.sevWarning :
    alert.severity === 'advisory' ? t.sevAdvisory :
    t.sevInfo;

  // Community Confirmations State
  const [resolvedVotes, setResolvedVotes] = useState(alert.community_confirmations?.confirmed_resolved || 0);
  const [activeVotes, setActiveVotes] = useState(alert.community_confirmations?.confirmed_active || 0);
  const [userVote, setUserVote] = useState<'resolved' | 'still_active' | null>(null);

  // Feedback Correction Modal/Form State
  const [showCorrectionForm, setShowCorrectionForm] = useState(false);
  const [correctedCategory, setCorrectedCategory] = useState(alert.category);
  const [correctedSeverity, setCorrectedSeverity] = useState(alert.severity);
  const [correctionComment, setCorrectionComment] = useState('');
  const [correctionSaved, setCorrectionSaved] = useState(false);

  const Icon = CATEGORY_ICONS[alert.category] || MoreHorizontal;
  const SeverityIcon = SEVERITY_ICONS[alert.severity] || Info;
  const severityStyle = SEVERITY_STYLES[alert.severity] || SEVERITY_STYLES.info;

  const isMuted = alert.status === 'cancelled' || alert.status === 'resolved';
  const isUnverified = alert.source_tier === 'unverified';
  const timeWindow = getTimeWindowChip(alert.start_time, alert.expected_end_time);
  const relativeTime = formatRelativeTime(alert.published_at || alert.created_at);
  const exactTimeTooltip = alert.published_at 
    ? new Date(alert.published_at).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' })
    : alert.created_at 
      ? new Date(alert.created_at).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' })
      : undefined;

  const toggleAction = (idx: number, e: React.MouseEvent) => {
    e.stopPropagation();
    setCheckedActions(prev => ({ ...prev, [idx]: !prev[idx] }));
  };

  const handleVote = async (vote: 'resolved' | 'still_active', e: React.MouseEvent) => {
    e.stopPropagation();
    if (userVote === vote) return;
    try {
      if (vote === 'resolved') {
        setResolvedVotes(prev => prev + 1);
        if (userVote === 'still_active') setActiveVotes(prev => Math.max(0, prev - 1));
      } else {
        setActiveVotes(prev => prev + 1);
        if (userVote === 'resolved') setResolvedVotes(prev => Math.max(0, prev - 1));
      }
      setUserVote(vote);
      await api.submitCommunityConfirmation(alert.id, vote);
    } catch (err) {
      console.error('Confirmation error:', err);
    }
  };

  const handleSubmitCorrection = async (e: React.FormEvent) => {
    e.preventDefault();
    e.stopPropagation();
    try {
      await api.submitAlertFeedback(alert.id, {
        suggested_category: correctedCategory !== alert.category ? correctedCategory : undefined,
        suggested_severity: correctedSeverity !== alert.severity ? correctedSeverity : undefined,
        comment: correctionComment.trim() || undefined,
      });
      setCorrectionSaved(true);
      setTimeout(() => {
        setShowCorrectionForm(false);
        setCorrectionSaved(false);
      }, 2000);
    } catch (err) {
      console.error('Feedback error:', err);
    }
  };

  const handlePlayTTS = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (typeof window === 'undefined' || !('speechSynthesis' in window)) {
      console.warn('Speech synthesis is not supported on this device.');
      return;
    }

    if (isPlayingTTS) {
      window.speechSynthesis.cancel();
      setIsPlayingTTS(false);
      return;
    }

    const actionText = alert.recommended_actions?.slice(0, 2).join('. ') || '';
    const voiceText = `${alert.title}. ${alert.expected_impact || ''}. Actions: ${actionText}`;
    const utterance = new SpeechSynthesisUtterance(voiceText);

    utterance.lang = language === 'te' ? 'te-IN' : language === 'hi' ? 'hi-IN' : 'en-IN';
    utterance.rate = 0.95;

    utterance.onend = () => setIsPlayingTTS(false);
    utterance.onerror = () => setIsPlayingTTS(false);

    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(utterance);
    setIsPlayingTTS(true);
  };

  return (
    <article 
      className={`rounded-2xl p-5 shadow-sm hover:shadow-md transition-all border ${severityStyle.border} relative ${
        isMuted
          ? 'bg-slate-50/70 dark:bg-slate-800/60 opacity-80 border-slate-300 dark:border-slate-700'
          : 'bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700'
      }`}
    >
      {/* Top Header Row: Category, Secondary Tags, Tier Badge, Status Badge, Severity Badge, Real Confidence */}
      <div className="flex flex-wrap items-center justify-between gap-2 mb-2.5">
        <div className="flex flex-wrap items-center gap-1.5">
          <div className="p-1.5 rounded-lg bg-slate-100 dark:bg-slate-700/60 text-slate-700 dark:text-slate-300">
            <Icon className="w-4 h-4" />
          </div>
          <span className="text-xs font-bold text-slate-700 dark:text-slate-200 uppercase tracking-wider">
            {categoryLabel}
          </span>

          {/* Secondary Category Tag Chips */}
          {alert.secondary_categories && alert.secondary_categories.length > 0 && (
            alert.secondary_categories.map((sec, idx) => (
              <span 
                key={`sec-${idx}`}
                className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-semibold bg-slate-100 dark:bg-slate-700/70 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-600 capitalize"
              >
                +{sec.replace('_', ' ')}
              </span>
            ))
          )}

          {/* Source Tier Badge */}
          {alert.source_tier === 'official' && (
            <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-800">
              <ShieldCheck className="w-3 h-3 text-emerald-600" />
              <span>{t.officialBadge}</span>
            </span>
          )}
          {alert.source_tier === 'news' && (
            <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-indigo-50 text-indigo-700 dark:bg-indigo-950/60 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800">
              <span>{t.newsBadge}</span>
            </span>
          )}
          {alert.source_tier === 'unverified' && (
            <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-amber-50 text-amber-700 dark:bg-amber-950/60 dark:text-amber-300 border border-amber-300 dark:border-amber-800">
              <AlertTriangle className="w-3 h-3 text-amber-600" />
              <span>{t.unverifiedBadge}</span>
            </span>
          )}

          {/* Status Badge */}
          {alert.status && (
            <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider border ${
              alert.status === 'updated' 
                ? 'bg-purple-50 text-purple-700 dark:bg-purple-950/60 dark:text-purple-300 border-purple-300' 
                : alert.status === 'resolved' 
                  ? 'bg-teal-50 text-teal-700 dark:bg-teal-950/60 dark:text-teal-300 border-teal-300' 
                  : alert.status === 'cancelled' 
                    ? 'bg-rose-50 text-rose-700 dark:bg-rose-950/60 dark:text-rose-300 line-through border-rose-300' 
                    : 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300 border-emerald-300'
            }`}>
              {alert.status}
            </span>
          )}
        </div>

        <div className="flex items-center space-x-2">
          {/* Severity Badge with Severity Icon for Accessibility */}
          <span 
            className={`inline-flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider border ${severityStyle.bgBadge} ${severityStyle.textBadge}`}
            title={`Severity: ${alert.severity}`}
          >
            <SeverityIcon className="w-3.5 h-3.5 shrink-0" />
            <span>{severityLabel}</span>
          </span>

          {/* Real Confidence Indicator (Hidden if value is missing/0) */}
          {alert.confidence != null && !isNaN(alert.confidence) && alert.confidence > 0 && (
            <span 
              className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-700/50 text-slate-500 dark:text-slate-400"
              title="Real model prediction probability"
            >
              {(alert.confidence * 100).toFixed(0)}% Conf
            </span>
          )}
        </div>
      </div>

      {/* Linked parent update notification */}
      {alert.parent_alert_id && (
        <div className="mb-2 text-[11px] text-purple-700 dark:text-purple-300 font-medium flex items-center space-x-1 bg-purple-50 dark:bg-purple-950/40 p-1.5 rounded-lg border border-purple-200 dark:border-purple-900">
          <LinkIcon className="w-3.5 h-3.5" />
          <span>Update to prior incident #{alert.parent_alert_id} (Original marked {alert.status})</span>
        </div>
      )}

      {/* Visible Rumor Warning Banner if Unverified */}
      {isUnverified && (
        <div className="mb-3 p-2.5 rounded-xl bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900/60 flex items-start space-x-2 text-xs text-amber-800 dark:text-amber-200">
          <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
          <div>
            <strong>{t.unverifiedWarningTitle}</strong> {t.unverifiedWarningBody}
          </div>
        </div>
      )}

      {/* Untruncated Title with CSS line-clamp-2 and Full Title Tooltip */}
      <h3 
        onClick={() => onOpenDetails(alert)}
        title={alert.title}
        tabIndex={0}
        onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') onOpenDetails(alert); }}
        className="text-base font-bold text-slate-900 dark:text-slate-100 hover:text-blue-600 dark:hover:text-blue-400 focus:text-blue-600 focus:outline-none cursor-pointer transition-colors leading-snug line-clamp-2 mb-1.5"
      >
        {alert.title}
      </h3>

      {/* Time Window Chip under Title */}
      {timeWindow && (
        <div className="mb-2.5">
          <span className={`inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-semibold ${
            isMuted
              ? 'bg-slate-100 dark:bg-slate-700/60 text-slate-500 dark:text-slate-400 line-through'
              : 'bg-blue-50 dark:bg-blue-950/50 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-800'
          }`}>
            <Clock className="w-3 h-3 mr-1" />
            <span>{timeWindow}</span>
          </span>
        </div>
      )}

      {/* Affected Area & Timestamp Metadata */}
      <div className="flex flex-wrap items-center gap-y-2 gap-x-4 text-xs text-slate-500 dark:text-slate-400 mb-3">
        <div className="flex items-center space-x-1">
          <MapPin className="w-3.5 h-3.5 text-blue-500 shrink-0" />
          <span className="font-semibold text-slate-700 dark:text-slate-300">
            {formatAffectedAreas(alert.affected_areas)}
          </span>
        </div>

        {relativeTime && (
          <div className="flex items-center space-x-1 text-slate-500 dark:text-slate-400 cursor-help" title={exactTimeTooltip}>
            <span>Posted {relativeTime}</span>
          </div>
        )}
      </div>

      {/* Expected Impact Summary (Darkened label for WCAG AA contrast) */}
      {alert.expected_impact && (
        <div className="bg-slate-50 dark:bg-slate-900/40 rounded-xl p-3 mb-3 border border-slate-100 dark:border-slate-800/80">
          <div className="text-[11px] font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-0.5">
            {t.expectedImpact}
          </div>
          <p className="text-xs text-slate-700 dark:text-slate-200 leading-relaxed">
            {alert.expected_impact}
          </p>
        </div>
      )}

      {/* Matched Saved Circles & Personalization Tags */}
      {(alert.matched_locations?.length || alert.profile_tags?.length) ? (
        <div className="flex flex-wrap items-center gap-1.5 mb-2.5">
          {alert.matched_locations?.map((mloc, i) => (
            <span
              key={`mloc-${i}`}
              className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-md text-[10px] font-bold bg-blue-50 dark:bg-blue-950/60 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-800"
            >
              <MapPin className="w-2.5 h-2.5" />
              <span>{mloc}</span>
            </span>
          ))}

          {alert.profile_tags?.map((tag, i) => (
            <span
              key={`ptag-${i}`}
              className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-md text-[10px] font-semibold bg-indigo-50 dark:bg-indigo-950/50 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800"
            >
              <Sparkles className="w-2.5 h-2.5 text-indigo-500" />
              <span>{tag}</span>
            </span>
          ))}
        </div>
      ) : null}

      {/* Profile Personalized Advisory Note */}
      {alert.personalized_notes && alert.personalized_notes.length > 0 && (
        <div className="mb-2.5 p-2 rounded-lg bg-indigo-50/60 dark:bg-indigo-950/30 border border-indigo-100 dark:border-indigo-900/50 text-[11px] text-indigo-800 dark:text-indigo-200 space-y-0.5">
          {alert.personalized_notes.map((note, idx) => (
            <div key={idx} className="flex items-start space-x-1.5">
              <span className="text-indigo-500 font-bold">•</span>
              <span>{note}</span>
            </div>
          ))}
        </div>
      )}

      {/* "What You Should Do" Checklist */}
      {alert.recommended_actions && alert.recommended_actions.length > 0 && (
        <div className="mb-4">
          <div className="text-[11px] font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-1.5 flex items-center justify-between">
            <div className="flex items-center space-x-1">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
              <span>{t.recommendedActions}</span>
            </div>
            {alert.profile_tags && alert.profile_tags.length > 0 && (
              <span className="text-[10px] font-normal text-indigo-600 dark:text-indigo-400 flex items-center space-x-0.5">
                <Sparkles className="w-3 h-3" />
                <span>Tailored for your profile</span>
              </span>
            )}
          </div>
          <ul className="space-y-1">
            {alert.recommended_actions.map((action, idx) => {
              const isChecked = !!checkedActions[idx];
              return (
                <li 
                  key={idx}
                  onClick={(e) => toggleAction(idx, e)}
                  className={`flex items-start space-x-2 text-xs p-1.5 rounded-lg cursor-pointer transition-colors ${
                    isChecked 
                      ? 'bg-emerald-50/60 dark:bg-emerald-950/20 text-slate-400 line-through' 
                      : 'hover:bg-slate-50 dark:hover:bg-slate-700/30 text-slate-700 dark:text-slate-300'
                  }`}
                >
                  <button 
                    type="button"
                    className="mt-0.5 text-emerald-600 dark:text-emerald-400 shrink-0 focus:outline-none focus:ring-2 focus:ring-emerald-500 rounded"
                    aria-label={isChecked ? `Uncheck action: ${action}` : `Complete action: ${action}`}
                  >
                    {isChecked ? <CheckSquare className="w-4 h-4" /> : <Square className="w-4 h-4 text-slate-400" />}
                  </button>
                  <span className="leading-snug">{action}</span>
                </li>
              );
            })}
          </ul>
        </div>
      )}

      {/* Community Confirmation & Accuracy Feedback Bar */}
      <div className="mb-3 pt-2.5 pb-2 px-3 rounded-xl bg-slate-50 dark:bg-slate-900/50 border border-slate-100 dark:border-slate-800 flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center space-x-2">
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400">
            Ground Status:
          </span>
          <button
            type="button"
            onClick={(e) => handleVote('resolved', e)}
            aria-label={`Confirm resolved, currently ${resolvedVotes} votes`}
            className={`px-2.5 py-1 rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition-all focus:outline-none focus:ring-2 focus:ring-emerald-500 ${
              userVote === 'resolved'
                ? 'bg-emerald-600 text-white shadow-sm'
                : 'bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-emerald-50 dark:hover:bg-emerald-950/40 border border-slate-200 dark:border-slate-700'
            }`}
            title="Confirm resolved or service restored"
          >
            <ThumbsUp className="w-3 h-3 text-emerald-500" />
            <span>Resolved ({resolvedVotes})</span>
          </button>

          <button
            type="button"
            onClick={(e) => handleVote('still_active', e)}
            aria-label={`Confirm still happening, currently ${activeVotes} votes`}
            className={`px-2.5 py-1 rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition-all focus:outline-none focus:ring-2 focus:ring-rose-500 ${
              userVote === 'still_active'
                ? 'bg-rose-600 text-white shadow-sm'
                : 'bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-rose-50 dark:hover:bg-rose-950/40 border border-slate-200 dark:border-slate-700'
            }`}
            title="Confirm still happening / disrupted"
          >
            <ThumbsDown className="w-3 h-3 text-rose-500" />
            <span>Still happening ({activeVotes})</span>
          </button>
        </div>

        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            setShowCorrectionForm(!showCorrectionForm);
          }}
          aria-label="Submit correction or report wrong category"
          className="text-[11px] font-medium text-slate-600 dark:text-slate-400 hover:text-amber-600 dark:hover:text-amber-400 flex items-center space-x-1 focus:outline-none focus:underline"
        >
          <Flag className="w-3 h-3" />
          <span>Wrong category?</span>
        </button>
      </div>

      {/* Citizen Correction Inline Modal/Form */}
      {showCorrectionForm && (
        <form
          onSubmit={handleSubmitCorrection}
          onClick={(e) => e.stopPropagation()}
          className="mb-3 p-3 rounded-xl bg-amber-50/80 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800 space-y-2 animate-in fade-in duration-150"
        >
          <div className="text-xs font-bold text-amber-900 dark:text-amber-200 flex items-center justify-between">
            <span>Suggest Correction: Help Retrain CivicPulse</span>
            {correctionSaved && (
              <span className="text-emerald-600 dark:text-emerald-400 font-bold flex items-center space-x-1">
                <Check className="w-3.5 h-3.5" />
                <span>Correction queued for merge!</span>
              </span>
            )}
          </div>

          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="text-[10px] font-semibold text-slate-700 dark:text-slate-300 block mb-0.5">
                Suggested Category
              </label>
              <select
                value={correctedCategory}
                onChange={(e) => setCorrectedCategory(e.target.value as Category)}
                className="w-full text-xs p-1 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="road_closure">Road Closure</option>
                <option value="water_supply">Water Supply</option>
                <option value="power_cut">Power Cut</option>
                <option value="severe_weather">Severe Weather</option>
                <option value="public_service">Public Service</option>
                <option value="other">Other</option>
              </select>
            </div>

            <div>
              <label className="text-[10px] font-semibold text-slate-700 dark:text-slate-300 block mb-0.5">
                Suggested Severity
              </label>
              <select
                value={correctedSeverity}
                onChange={(e) => setCorrectedSeverity(e.target.value as Severity)}
                className="w-full text-xs p-1 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="info">Info</option>
                <option value="advisory">Advisory</option>
                <option value="warning">Warning</option>
                <option value="critical">Critical</option>
              </select>
            </div>
          </div>

          <div>
            <input
              type="text"
              placeholder="Optional comment (e.g. Feeder trip, not planned load shedding)"
              value={correctionComment}
              onChange={(e) => setCorrectionComment(e.target.value)}
              className="w-full text-xs p-1.5 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div className="flex justify-end space-x-2">
            <button
              type="button"
              onClick={() => setShowCorrectionForm(false)}
              className="px-2.5 py-1 text-xs text-slate-600 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200 font-medium"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-3 py-1 bg-amber-600 hover:bg-amber-700 text-white font-semibold text-xs rounded-lg transition-colors shadow-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
            >
              Submit Feedback
            </button>
          </div>
        </form>
      )}

      {/* Bottom Footer: Source Link, TTS Read-Aloud, XAI Button, Map, Full View */}
      <div className="pt-3 border-t border-slate-100 dark:border-slate-700/80 flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center space-x-1.5 text-xs text-slate-700 dark:text-slate-300">
          <span className="font-bold text-slate-700 dark:text-slate-300">Source:</span>
          {alert.source_url ? (
            <a 
              href={alert.source_url} 
              target="_blank" 
              rel="noopener noreferrer" 
              className="text-blue-600 dark:text-blue-400 hover:underline flex items-center space-x-0.5 font-bold focus:outline-none focus:ring-2 focus:ring-blue-500 rounded px-0.5"
              onClick={(e) => e.stopPropagation()}
              title={`Visit source: ${alert.source_url}`}
            >
              <span>{alert.source_name}</span>
              <ExternalLink className="w-3 h-3 inline ml-0.5" />
            </a>
          ) : (
            <strong className="text-slate-800 dark:text-slate-200">{alert.source_name}</strong>
          )}
        </div>

        <div className="flex items-center space-x-2">
          {/* Text-to-Speech (TTS) Voice Readout Button (Hidden if no matching voice available) */}
          {hasVoice && (
            <button
              type="button"
              onClick={handlePlayTTS}
              aria-label={isPlayingTTS ? "Stop voice read-aloud" : "Read alert aloud"}
              className={`flex items-center space-x-1.5 px-3 py-1 rounded-lg text-xs font-semibold transition-all focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                isPlayingTTS
                  ? 'bg-rose-600 text-white animate-pulse shadow-sm'
                  : 'bg-slate-100 dark:bg-slate-700/60 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700'
              }`}
              title="Read alert aloud in selected language (Web Speech API)"
            >
              {isPlayingTTS ? <VolumeX className="w-3.5 h-3.5" /> : <Volume2 className="w-3.5 h-3.5" />}
              <span>{isPlayingTTS ? t.stopAudio : t.voiceReadout}</span>
            </button>
          )}

          {/* Explain with XAI Button */}
          <button
            type="button"
            onClick={() => setShowXAI(!showXAI)}
            aria-label="Explain classification with LIME"
            className={`flex items-center space-x-1 px-2.5 py-1 rounded-lg text-xs font-medium transition-all focus:outline-none focus:ring-2 focus:ring-indigo-500 ${
              showXAI
                ? 'bg-indigo-600 text-white shadow-sm'
                : 'bg-indigo-50 dark:bg-indigo-950/50 text-indigo-700 dark:text-indigo-300 hover:bg-indigo-100 dark:hover:bg-indigo-900/60 border border-indigo-200 dark:border-indigo-800'
            }`}
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Why this alert?</span>
            {showXAI ? <ChevronUp className="w-3 h-3 ml-1" /> : <ChevronDown className="w-3 h-3 ml-1" />}
          </button>

          {/* Map Shortcut Button */}
          {onViewOnMap && (
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                onViewOnMap(alert);
              }}
              aria-label="Locate incident on map"
              className="flex items-center space-x-1 px-2.5 py-1 rounded-lg text-xs font-semibold bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 hover:bg-emerald-100 dark:hover:bg-emerald-900/60 border border-emerald-200 dark:border-emerald-800 transition-colors focus:outline-none focus:ring-2 focus:ring-emerald-500"
              title="Locate incident pin on Hyderabad map"
            >
              <MapPin className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
              <span>Map</span>
            </button>
          )}

          <button
            type="button"
            onClick={() => onOpenDetails(alert)}
            aria-label="Open full alert view details"
            className="text-xs font-bold text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-500 rounded px-1"
          >
            Full View →
          </button>
        </div>
      </div>

      {/* Expandable Explainable AI Panel */}
      {showXAI && (
        <div className="mt-4 pt-3 border-t border-slate-200 dark:border-slate-700 animate-in fade-in duration-200">
          <XAIPanel alertId={alert.id} />
        </div>
      )}
    </article>
  );
};
