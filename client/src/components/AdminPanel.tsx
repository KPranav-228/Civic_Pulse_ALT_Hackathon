import React, { useState, useEffect } from 'react';
import { 
  CheckCircle, 
  XCircle, 
  Edit3, 
  PlusCircle, 
  Send, 
  AlertTriangle, 
  ShieldAlert, 
  RefreshCw,
  Sparkles,
  ExternalLink
} from 'lucide-react';
import { Alert, IngestResponse, formatAffectedAreas } from '../types';
import { api } from '../services/api';

export const AdminPanel: React.FC = () => {
  const [reviewQueue, setReviewQueue] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(false);
  const [ingestText, setIngestText] = useState('');
  const [sourceName, setSourceName] = useState('Local Reporter / Admin');
  const [sourceUrl, setSourceUrl] = useState('');
  const [ingesting, setIngesting] = useState(false);
  const [ingestResult, setIngestResult] = useState<IngestResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [editingAlert, setEditingAlert] = useState<Alert | null>(null);

  const fetchQueue = async () => {
    setLoading(true);
    try {
      const data = await api.getReviewQueue();
      setReviewQueue(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchQueue();
  }, []);

  const handleApprove = async (id: number) => {
    try {
      await api.updateAlert(id, { needs_review: false, status: 'active' });
      setReviewQueue(prev => prev.filter(a => a.id !== id));
    } catch (err) {
      setErrorMessage('Error approving alert: ' + err);
    }
  };

  const handleReject = async (id: number) => {
    try {
      await api.updateAlert(id, { needs_review: false, status: 'past' });
      setReviewQueue(prev => prev.filter(a => a.id !== id));
    } catch (err) {
      setErrorMessage('Error rejecting alert: ' + err);
    }
  };

  const handleIngest = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!ingestText.trim() || ingestText.trim().length < 15) {
      setErrorMessage('Please enter at least 15 characters so the NLP pipeline can analyze and extract details.');
      return;
    }

    setErrorMessage(null);
    setIngesting(true);
    setIngestResult(null);
    try {
      const res = await api.ingestReport({
        raw_text: ingestText.trim(),
        source_name: sourceName,
        source_url: sourceUrl || undefined,
      });
      setIngestResult(res);
      setIngestText('');
      fetchQueue();
    } catch (err: any) {
      setErrorMessage(err.message || 'Ingestion failed. Make sure the FastAPI backend is running on port 8000.');
    } finally {
      setIngesting(false);
    }
  };

  const handleSaveEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingAlert) return;

    try {
      await api.updateAlert(editingAlert.id, {
        title: editingAlert.title,
        category: editingAlert.category,
        severity: editingAlert.severity,
        expected_impact: editingAlert.expected_impact,
        needs_review: false,
      });
      setEditingAlert(null);
      fetchQueue();
    } catch (err: any) {
      alert('Failed to update alert: ' + err.message);
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-200">
      
      {/* Top Section: Live Raw Ingestion Form */}
      <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 shadow-sm border border-slate-200 dark:border-slate-700">
        <div className="flex items-center space-x-3 mb-4">
          <div className="p-2 rounded-xl bg-blue-100 dark:bg-blue-900/50 text-blue-600 dark:text-blue-400">
            <PlusCircle className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-slate-900 dark:text-white">
              Live Ingestion & NLP Classification Pipeline
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Paste unstructured municipal notices, emergency updates, or local tweets to run them through our spam filter, category classifier, severity analyzer, NER, and LLM structured extractor.
            </p>
          </div>
        </div>

        {/* Error Notification Banner */}
        {errorMessage && (
          <div className="mb-4 p-3 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 text-xs text-rose-700 dark:text-rose-300 flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <AlertTriangle className="w-4 h-4 text-rose-500 shrink-0" />
              <span>{errorMessage}</span>
            </div>
            <button 
              type="button" 
              onClick={() => setErrorMessage(null)}
              className="text-rose-500 hover:text-rose-700 font-bold ml-2 text-sm"
            >
              ×
            </button>
          </div>
        )}

        <form onSubmit={handleIngest} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
              Raw Announcement / News Text <span className="text-slate-400 font-normal">(min 15 characters)</span>
            </label>
            <textarea
              rows={4}
              required
              minLength={15}
              value={ingestText}
              onChange={(e) => setIngestText(e.target.value)}
              placeholder="e.g. GHMC Alert: Due to heavy downpour, waterlogging reported near Gachibowli flyover. Inward traffic diverted via Bio Diversity Junction. Citizens advised to take alternative routes..."
              className="w-full p-3 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                Source Name / Authority
              </label>
              <input
                type="text"
                value={sourceName}
                onChange={(e) => setSourceName(e.target.value)}
                className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                Source URL (optional)
              </label>
              <input
                type="url"
                value={sourceUrl}
                onChange={(e) => setSourceUrl(e.target.value)}
                placeholder="https://twitter.com/HYDTP/status/..."
                className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          <div className="flex justify-end">
            <button
              type="submit"
              disabled={ingesting}
              className="flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold shadow-md shadow-blue-500/20 transition-all disabled:opacity-50"
            >
              {ingesting ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Processing Through NLP Pipeline...</span>
                </>
              ) : (
                <>
                  <Send className="w-4 h-4" />
                  <span>Ingest & Process Text</span>
                </>
              )}
            </button>
          </div>
        </form>

        {/* Ingest Result Output */}
        {ingestResult && (
          <div className="mt-4 p-4 rounded-xl bg-blue-50 dark:bg-blue-950/40 border border-blue-200 dark:border-blue-800 animate-in fade-in duration-150">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold text-blue-900 dark:text-blue-200 flex items-center space-x-1.5">
                <Sparkles className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                <span>Pipeline Result: {ingestResult.message}</span>
              </span>
              <span className="text-xs font-mono px-2 py-0.5 rounded bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-300">
                Spam Score: {(ingestResult.spam_probability * 100).toFixed(1)}%
              </span>
            </div>

            {ingestResult.is_spam ? (
              <p className="text-xs text-rose-600 dark:text-rose-400">
                ⚠️ Filtered as spam/irrelevant news. Not converted to an alert card.
              </p>
            ) : (ingestResult.status === 'duplicate' || (ingestResult as any).is_duplicate) ? (
              <div className="space-y-2 text-xs text-slate-700 dark:text-slate-300">
                <div className="flex items-center space-x-1.5 text-amber-600 dark:text-amber-400 font-bold mb-1">
                  <AlertTriangle className="w-4 h-4 shrink-0" />
                  <span>Duplicate Report Detected — No Duplicate Alert Created</span>
                </div>
                <p className="text-slate-600 dark:text-slate-300">
                  {ingestResult.message}
                </p>
                {ingestResult.alert && (
                  <div className="p-3 rounded-xl bg-amber-50/70 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800 space-y-1">
                    <div><strong>Active Alert #{ingestResult.alert.id}:</strong> {ingestResult.alert.title}</div>
                    <div className="flex items-center space-x-3 text-[11px] text-slate-500 dark:text-slate-400 pt-0.5">
                      <span>Category: <strong className="uppercase text-blue-600 dark:text-blue-400">{ingestResult.alert.category}</strong></span>
                      <span>Severity: <strong className="uppercase text-orange-600 dark:text-orange-400">{ingestResult.alert.severity}</strong></span>
                      <span>Status: <strong className="text-emerald-600 dark:text-emerald-400 uppercase">{ingestResult.alert.status}</strong></span>
                    </div>
                  </div>
                )}
              </div>
            ) : (ingestResult.alert || (ingestResult as any).title) ? (
              <div className="space-y-1.5 text-xs text-slate-700 dark:text-slate-300">
                <div className="flex items-center space-x-1 text-emerald-600 dark:text-emerald-400 font-bold mb-1">
                  <CheckCircle className="w-4 h-4" />
                  <span>Alert Successfully Generated & Saved to Database!</span>
                </div>
                <div><strong>Extracted Title:</strong> {ingestResult.alert?.title || (ingestResult as any).title}</div>
                <div><strong>Classified Category:</strong> <span className="uppercase font-semibold text-blue-600">{ingestResult.alert?.category || (ingestResult as any).category}</span></div>
                <div><strong>Urgency/Severity:</strong> <span className="uppercase font-semibold text-orange-600">{ingestResult.alert?.severity || (ingestResult as any).severity}</span></div>
                <div><strong>Extracted Localities:</strong> {formatAffectedAreas(ingestResult.alert?.affected_areas || (ingestResult as any).affected_areas)}</div>
                <div><strong>Impact:</strong> {ingestResult.alert?.expected_impact || (ingestResult as any).expected_impact}</div>
              </div>
            ) : null}
          </div>
        )}
      </div>

      {/* Review Queue Section */}
      <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 shadow-sm border border-slate-200 dark:border-slate-700">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-xl bg-amber-100 dark:bg-amber-900/50 text-amber-600 dark:text-amber-400">
              <AlertTriangle className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900 dark:text-white">
                Human-in-the-Loop Moderation Queue ({reviewQueue.length})
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Alerts with confidence score &lt; 75% or flagged for municipal verification before publication.
              </p>
            </div>
          </div>

          <button
            onClick={fetchQueue}
            disabled={loading}
            className="p-2 rounded-xl border border-slate-200 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-300 text-xs flex items-center space-x-1"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
        </div>

        {reviewQueue.length === 0 ? (
          <div className="text-center py-10 text-slate-500 dark:text-slate-400 text-xs">
            <CheckCircle className="w-10 h-10 text-emerald-500 mx-auto mb-2" />
            Moderation queue is empty! All alerts have high confidence and are active.
          </div>
        ) : (
          <div className="space-y-3">
            {reviewQueue.map((item) => (
              <div
                key={item.id}
                className="p-4 rounded-xl bg-slate-50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-700 flex flex-col md:flex-row md:items-center justify-between gap-4"
              >
                <div className="space-y-1 max-w-xl">
                  <div className="flex items-center space-x-2">
                    <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-blue-100 dark:bg-blue-900/60 text-blue-700 dark:text-blue-300">
                      {item.category}
                    </span>
                    <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-amber-100 dark:bg-amber-900/60 text-amber-700 dark:text-amber-300">
                      {item.severity}
                    </span>
                    <span className="text-[10px] font-mono text-slate-400">
                      Conf: {(item.confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                  <h4 className="text-xs font-bold text-slate-900 dark:text-slate-100">
                    {item.title}
                  </h4>
                  <p className="text-[11px] text-slate-600 dark:text-slate-400 line-clamp-2">
                    {item.expected_impact}
                  </p>
                  <div className="text-[10px] text-slate-400">
                    Areas: {formatAffectedAreas(item.affected_areas)} • Source: {item.source_name}
                  </div>
                </div>

                <div className="flex items-center space-x-2 self-end md:self-center">
                  <button
                    onClick={() => setEditingAlert(item)}
                    className="p-2 rounded-lg bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-200 hover:bg-slate-300 dark:hover:bg-slate-600 transition-colors"
                    title="Edit alert"
                  >
                    <Edit3 className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => handleReject(item.id)}
                    className="p-2 rounded-lg bg-rose-100 dark:bg-rose-950/60 text-rose-700 dark:text-rose-300 hover:bg-rose-200 dark:hover:bg-rose-900 transition-colors"
                    title="Reject alert"
                  >
                    <XCircle className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => handleApprove(item.id)}
                    className="flex items-center space-x-1 px-3 py-1.5 rounded-lg bg-emerald-600 text-white hover:bg-emerald-700 text-xs font-medium transition-colors"
                  >
                    <CheckCircle className="w-4 h-4" />
                    <span>Approve</span>
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Edit Modal */}
      {editingAlert && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-in fade-in duration-150">
          <form 
            onSubmit={handleSaveEdit}
            className="bg-white dark:bg-slate-800 rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-slate-200 dark:border-slate-700 space-y-4"
          >
            <h3 className="text-base font-bold text-slate-900 dark:text-white">
              Edit Alert #{editingAlert.id}
            </h3>

            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                Title
              </label>
              <input
                type="text"
                value={editingAlert.title}
                onChange={(e) => setEditingAlert({ ...editingAlert, title: e.target.value })}
                className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 text-slate-900 dark:text-slate-100"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Category
                </label>
                <select
                  value={editingAlert.category}
                  onChange={(e) => setEditingAlert({ ...editingAlert, category: e.target.value as any })}
                  className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 text-slate-900 dark:text-slate-100"
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
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Severity
                </label>
                <select
                  value={editingAlert.severity}
                  onChange={(e) => setEditingAlert({ ...editingAlert, severity: e.target.value as any })}
                  className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 text-slate-900 dark:text-slate-100"
                >
                  <option value="critical">Critical</option>
                  <option value="warning">Warning</option>
                  <option value="advisory">Advisory</option>
                  <option value="info">Info</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                Expected Impact
              </label>
              <textarea
                rows={3}
                value={editingAlert.expected_impact || ''}
                onChange={(e) => setEditingAlert({ ...editingAlert, expected_impact: e.target.value })}
                className="w-full p-2.5 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 text-slate-900 dark:text-slate-100"
              />
            </div>

            <div className="flex justify-end space-x-2 pt-2 border-t border-slate-200 dark:border-slate-700">
              <button
                type="button"
                onClick={() => setEditingAlert(null)}
                className="px-4 py-2 rounded-xl text-xs font-medium text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 rounded-xl bg-blue-600 text-white text-xs font-semibold hover:bg-blue-700"
              >
                Save & Approve
              </button>
            </div>
          </form>
        </div>
      )}

    </div>
  );
};
