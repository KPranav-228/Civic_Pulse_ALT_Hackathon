'use client';

import { CheckCircle2, LoaderCircle, Newspaper, Sparkles } from 'lucide-react';
import ModelCard from '@/components/ModelCard';
import type { SummarizationResponse } from '@/lib/types';

interface ResultsPanelProps {
  response: SummarizationResponse | null;
  isLoading: boolean;
}

export default function ResultsPanel({ response, isLoading }: ResultsPanelProps) {
  if (isLoading) {
    return (
      <section className="glass-card min-h-[560px] p-6 flex flex-col items-center justify-center text-center">
        <div className="w-14 h-14 rounded-2xl bg-primary/10 border border-primary/20 flex items-center justify-center mb-5">
          <LoaderCircle className="w-7 h-7 text-primary animate-spin" />
        </div>
        <h2 className="text-xl font-bold text-white">Models are reading</h2>
        <p className="text-sm text-white/50 mt-2 max-w-xs leading-relaxed">Generating summaries and measuring each model&apos;s output. This can take a moment on local hardware.</p>
        <div className="mt-7 w-44 h-1 rounded-full overflow-hidden bg-white/[0.08]">
          <div className="h-full w-2/3 bg-gradient-to-r from-secondary via-primary to-secondary animate-pulse" />
        </div>
      </section>
    );
  }

  if (!response) {
    return (
      <section className="glass-card min-h-[560px] p-6 flex flex-col items-center justify-center text-center border-dashed border-white/20">
        <div className="w-14 h-14 rounded-2xl bg-white/[0.045] border border-white/[0.08] flex items-center justify-center mb-5">
          <Newspaper className="w-7 h-7 text-white/35" />
        </div>
        <h2 className="text-lg font-bold text-white/80">Your summaries will land here</h2>
        <p className="text-sm text-white/45 mt-2 max-w-xs leading-relaxed">Add a source article, choose your models, then generate a side-by-side readout.</p>
        <div className="mt-6 flex items-center gap-2 text-[11px] font-bold uppercase tracking-[0.16em] text-secondary/75">
          <Sparkles className="w-3.5 h-3.5" /> Ready when you are
        </div>
      </section>
    );
  }

  return (
    <section className="flex flex-col gap-5">
      <div className="glass-card p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center gap-4 sm:justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-secondary/10 border border-secondary/25 flex items-center justify-center">
            <CheckCircle2 className="w-5 h-5 text-secondary" />
          </div>
          <div>
            <p className="font-bold text-white">Summary run complete</p>
            <p className="text-xs text-white/45 mt-0.5">{response.summaries.length} models responded to this article.</p>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <span className="metric-chip"><b className="text-white">{response.article_stats.word_count}</b> source words</span>
          <span className="metric-chip"><b className="text-white">{response.preprocessing_info.cleaning_steps.length}</b> clean-up steps</span>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-5">
        {response.summaries.map((summary, index) => (
          <ModelCard
            key={summary.model}
            result={summary}
            articleWordCount={response.article_stats.word_count}
            index={index}
          />
        ))}
      </div>
    </section>
  );
}
