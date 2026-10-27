'use client';

import { useState } from 'react';
import { AlertTriangle, BarChart3, FlaskConical, Sparkles } from 'lucide-react';
import Header from '@/components/Header';
import InputPanel from '@/components/InputPanel';
import ResultsPanel from '@/components/ResultsPanel';
import ComparisonPanel from '@/components/ComparisonPanel';
import EvaluationPanel from '@/components/EvaluationPanel';
import ExperimentPanel from '@/components/ExperimentPanel';
import { useSummarize } from '@/hooks/useSummarize';

const tabs = [
  { id: 'summarize', label: 'Summarize', icon: Sparkles },
  { id: 'compare', label: 'Compare', icon: BarChart3 },
  { id: 'experiment', label: 'Experiment', icon: FlaskConical },
] as const;

export default function Home() {
  const [activeTab, setActiveTab] = useState<'summarize' | 'compare' | 'experiment'>('summarize');
  const { response, isLoading, error, submitArticle } = useSummarize();

  return (
    <div className="flex flex-col min-h-screen">
      <Header />

      <main className="flex-1 max-w-7xl mx-auto w-full px-5 sm:px-6 py-9 sm:py-12 flex flex-col gap-8 animate-fade-in">
        <section className="relative overflow-hidden rounded-[2rem] border border-white/[0.08] bg-surface/55 px-6 py-10 sm:px-10 sm:py-12">
          <div className="hero-grid absolute inset-0 opacity-60 pointer-events-none" />
          <div className="relative grid grid-cols-1 lg:grid-cols-[1.45fr_0.8fr] gap-8 lg:gap-16 items-end">
            <div className="max-w-3xl">
              <p className="eyebrow flex items-center gap-2 mb-5">
                <Sparkles className="w-3.5 h-3.5" /> Multi-model analysis workspace
              </p>
              <h1 className="display-font text-4xl sm:text-5xl lg:text-[3.8rem] font-semibold leading-[1.02] tracking-tight text-white">
                Make every long read <span className="gradient-text">worth the time.</span>
              </h1>
              <p className="text-base sm:text-lg text-white/60 leading-relaxed mt-6 max-w-2xl">
                Test leading NLP models side by side, inspect their output, and retain the signal from the noise.
              </p>
            </div>

            <div className="grid grid-cols-3 gap-3">
              {[
                ['04', 'models'],
                ['03', 'views'],
                ['01', 'workspace'],
              ].map(([value, label]) => (
                <div key={label} className="rounded-2xl border border-white/[0.08] bg-black/15 px-3 py-4 sm:px-4">
                  <span className="display-font text-2xl sm:text-3xl text-primary block">{value}</span>
                  <span className="text-[10px] sm:text-[11px] font-bold tracking-[0.14em] uppercase text-white/45 block mt-1">{label}</span>
                </div>
              ))}
            </div>
          </div>
        </section>

        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="section-label">Workspace</p>
            <p className="text-sm text-white/55 mt-1">Choose a view to prepare, compare, or benchmark summaries.</p>
          </div>
          <div className="w-full sm:w-auto bg-black/20 p-1.5 rounded-2xl border border-white/[0.08] flex gap-1.5 overflow-x-auto">
            {tabs.map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                onClick={() => setActiveTab(id)}
                className={`flex items-center justify-center gap-2 whitespace-nowrap px-4 sm:px-5 py-2.5 rounded-xl text-sm font-bold transition-all ${
                  activeTab === id
                    ? 'bg-primary text-slate-950 shadow-[0_8px_22px_rgba(242,182,84,0.18)]'
                    : 'text-white/55 hover:text-white hover:bg-white/[0.06]'
                }`}
              >
                <Icon className="w-4 h-4" /> {label}
              </button>
            ))}
          </div>
        </div>

        {error && (
          <div className="rounded-2xl border border-red-400/25 bg-red-400/[0.09] p-4 flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 text-red-300 flex-shrink-0" />
            <p className="text-red-100/90 text-sm">{error}</p>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 lg:gap-8">
          {activeTab === 'summarize' && (
            <>
              <div className="col-span-1 lg:col-span-5 animate-slide-up" style={{ animationDelay: '0.1s' }}>
                <InputPanel onSubmit={submitArticle} isLoading={isLoading} />
              </div>
              <div className="col-span-1 lg:col-span-7 animate-slide-up" style={{ animationDelay: '0.2s' }}>
                <ResultsPanel response={response} isLoading={isLoading} />
              </div>
            </>
          )}

          {activeTab === 'compare' && (
            <>
              <div className="col-span-1 lg:col-span-8 animate-slide-up">
                <ComparisonPanel response={response} />
              </div>
              <div className="col-span-1 lg:col-span-4 animate-slide-up" style={{ animationDelay: '0.1s' }}>
                <EvaluationPanel response={response} />
              </div>
            </>
          )}

          {activeTab === 'experiment' && (
            <div className="col-span-1 lg:col-span-12 animate-slide-up">
              <ExperimentPanel />
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
