'use client';

import { AlertCircle, Clock3, Scissors, Type } from 'lucide-react';
import type { SummaryResult } from '@/lib/types';

interface ModelCardProps {
  result: SummaryResult;
  articleWordCount: number;
  index: number;
}

const modelMeta: Record<string, { label: string; color: string }> = {
  t5: { label: 'T5-Small', color: '#49a7ff' },
  bart: { label: 'DistilBART-CNN', color: '#23b6a8' },
  pegasus: { label: 'PEGASUS-XSum', color: '#f2b654' },
  llm: { label: 'Llama 3.3 70B', color: '#ef735f' },
};

export default function ModelCard({ result, articleWordCount, index }: ModelCardProps) {
  const meta = modelMeta[result.model] ?? { label: result.model, color: '#9bb1b6' };
  const isError = result.status === 'error';
  const compression = result.compression_ratio != null ? Math.round(result.compression_ratio * 100) : null;
  const reduction = result.word_count != null && articleWordCount > 0
    ? Math.max(0, Math.round((1 - result.word_count / articleWordCount) * 100))
    : null;

  return (
    <article
      className="glow-card flex flex-col h-full animate-slide-up hover:border-white/20 transition-colors"
      style={{ animationDelay: `${index * 80}ms`, animationFillMode: 'both' }}
    >
      <div className="h-1 w-full" style={{ background: `linear-gradient(90deg, ${meta.color}, transparent 78%)` }} />

      <div className="flex items-center justify-between gap-3 px-5 pt-5 pb-4">
        <div className="flex items-center gap-2.5 min-w-0">
          <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ background: meta.color, boxShadow: `0 0 10px ${meta.color}` }} />
          <span className="font-bold text-sm text-white truncate">{meta.label}</span>
        </div>
        <span className={isError ? 'badge-error text-[10px]' : 'badge-success text-[10px]'}>{isError ? 'Failed' : 'Ready'}</span>
      </div>

      <div className="flex-1 px-5 pb-5">
        {isError ? (
          <div className="flex items-start gap-3 p-3.5 rounded-xl bg-red-400/[0.08] border border-red-400/20">
            <AlertCircle className="w-4 h-4 text-red-300 shrink-0 mt-0.5" />
            <p className="text-sm text-red-100/80 leading-relaxed">{result.error || 'This model could not generate a summary.'}</p>
          </div>
        ) : (
          <p className="text-[14px] text-white/75 leading-[1.75]">{result.summary || 'No summary was returned for this model.'}</p>
        )}
      </div>

      {!isError && (
        <footer className="border-t border-white/[0.07] px-4 py-3.5 grid grid-cols-3 gap-1">
          <div className="flex flex-col items-center gap-1">
            <Type className="w-3.5 h-3.5 text-white/35" />
            <span className="text-sm font-bold text-white/85">{result.word_count ?? '-'}</span>
            <span className="text-[10px] uppercase tracking-wide text-white/35">words</span>
          </div>
          <div className="flex flex-col items-center gap-1 border-x border-white/[0.07]">
            <Scissors className="w-3.5 h-3.5 text-primary/80" />
            <span className="text-sm font-bold text-white/85">{reduction != null ? `${reduction}%` : compression != null ? `${compression}%` : '-'}</span>
            <span className="text-[10px] uppercase tracking-wide text-white/35">shorter</span>
          </div>
          <div className="flex flex-col items-center gap-1">
            <Clock3 className="w-3.5 h-3.5 text-secondary/80" />
            <span className="text-sm font-bold text-white/85">{result.generation_time_seconds != null ? `${result.generation_time_seconds.toFixed(2)}s` : '-'}</span>
            <span className="text-[10px] uppercase tracking-wide text-white/35">latency</span>
          </div>
        </footer>
      )}
    </article>
  );
}
