'use client';

import { useState } from 'react';
import { ClipboardCheck, Send, Sparkles } from 'lucide-react';
import StarRating from '@/components/StarRating';
import { submitQualitativeScore } from '@/lib/api';
import type { QualitativeScoreInput, SummarizationResponse } from '@/lib/types';

const criteria = [
  { id: 'coherence', label: 'Coherence', description: 'Logical flow and structure' },
  { id: 'readability', label: 'Readability', description: 'Clarity and grammar' },
  { id: 'factual_consistency', label: 'Accuracy', description: 'Faithful to the source' },
  { id: 'semantic_relevance', label: 'Relevance', description: 'Captures the key meaning' },
];

export default function EvaluationPanel({ response }: { response: SummarizationResponse | null }) {
  const [selectedModel, setSelectedModel] = useState<string | null>(null);
  const [scores, setScores] = useState<Record<string, number>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSaved, setIsSaved] = useState(false);

  if (!response) {
    return (
      <section className="glass-card p-6 h-[430px] flex flex-col items-center justify-center text-center border-dashed border-white/20">
        <div className="w-12 h-12 rounded-2xl bg-white/[0.045] border border-white/[0.08] flex items-center justify-center">
          <ClipboardCheck className="w-6 h-6 text-white/35" />
        </div>
        <h2 className="font-bold text-white/80 mt-4">Human review waits here</h2>
        <p className="text-sm text-white/45 mt-2 max-w-xs">Run a summary first, then score the output against your editorial judgment.</p>
      </section>
    );
  }

  const models = response.summaries.filter((summary) => summary.status === 'success').map((summary) => summary.model);
  const activeModel = selectedModel || models[0];
  const canSubmit = Boolean(activeModel) && Object.keys(scores).length === criteria.length;

  const recordScore = async () => {
    if (!activeModel || !canSubmit) return;

    setIsSubmitting(true);
    setIsSaved(false);
    try {
      const score: QualitativeScoreInput = {
        model: activeModel,
        coherence: scores.coherence ?? 0,
        readability: scores.readability ?? 0,
        factual_consistency: scores.factual_consistency ?? 0,
        semantic_relevance: scores.semantic_relevance ?? 0,
      };
      await submitQualitativeScore(score);
      setIsSaved(true);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <section className="glass-card p-5 sm:p-6 flex flex-col gap-5">
      <div className="border-b border-white/[0.08] pb-5">
        <p className="section-label flex items-center gap-2"><ClipboardCheck className="w-3.5 h-3.5" /> Editorial review</p>
        <h2 className="text-xl font-bold text-white mt-2">Add your judgment</h2>
        <p className="text-sm text-white/50 mt-1">Score each quality dimension from one to five.</p>
      </div>

      <div>
        <p className="text-[11px] font-bold uppercase tracking-[0.14em] text-white/45 mb-2.5">Model under review</p>
        <div className="flex flex-wrap gap-2">
          {models.map((model) => (
            <button
              key={model}
              type="button"
              onClick={() => {
                setSelectedModel(model);
                setIsSaved(false);
              }}
              className={`px-3 py-2 rounded-lg text-xs font-bold uppercase tracking-wide transition-colors ${
                activeModel === model
                  ? 'bg-primary text-slate-950'
                  : 'bg-black/15 text-white/50 border border-white/[0.08] hover:text-white hover:bg-white/[0.06]'
              }`}
            >
              {model}
            </button>
          ))}
        </div>
      </div>

      <div className="flex flex-col gap-3">
        {criteria.map((criterion) => (
          <div key={criterion.id} className="rounded-xl bg-black/15 border border-white/[0.07] p-3.5">
            <div className="flex items-start justify-between gap-3 mb-3">
              <span className="text-sm font-bold text-white/90">{criterion.label}</span>
              <span className="text-[11px] text-white/40 text-right">{criterion.description}</span>
            </div>
            <StarRating
              label={`Rate ${criterion.label}`}
              value={scores[criterion.id] || 0}
              onChange={(value) => {
                setScores((current) => ({ ...current, [criterion.id]: value }));
                setIsSaved(false);
              }}
            />
          </div>
        ))}
      </div>

      {isSaved && (
        <p className="flex items-center gap-2 text-sm text-secondary"><Sparkles className="w-4 h-4" /> Evaluation saved for {activeModel?.toUpperCase()}.</p>
      )}

      <button
        type="button"
        onClick={recordScore}
        disabled={isSubmitting || !canSubmit}
        className="btn-primary w-full mt-1 disabled:opacity-40 disabled:grayscale disabled:cursor-not-allowed flex items-center justify-center gap-2"
      >
        <Send className="w-4 h-4" /> {isSubmitting ? 'Recording review...' : 'Record human score'}
      </button>
    </section>
  );
}
