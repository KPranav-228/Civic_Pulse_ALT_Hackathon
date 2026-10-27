'use client';

import { useState } from 'react';
import { CheckCircle2, Database, FlaskConical, Layers3, Play, Timer } from 'lucide-react';
import { startExperiment } from '@/lib/api';
import type { ExperimentStatus } from '@/lib/types';

export default function ExperimentPanel() {
  const [dataset, setDataset] = useState<'cnn_dailymail' | 'xsum'>('cnn_dailymail');
  const [numSamples, setNumSamples] = useState(5);
  const [status, setStatus] = useState<ExperimentStatus | null>(null);
  const [isRunning, setIsRunning] = useState(false);

  const handleStart = async () => {
    setIsRunning(true);
    setStatus(null);
    try {
      const response = await startExperiment({
        dataset,
        num_samples: numSamples,
        models: ['t5', 'bart', 'pegasus'],
        include_llm: false,
        max_length: 150,
        min_length: 30,
      });
      setStatus(response);

      const poll = setInterval(async () => {
        try {
          const { getExperimentStatus } = await import('@/lib/api');
          const currentStatus = await getExperimentStatus(response.experiment_id);
          setStatus(currentStatus);

          if (currentStatus.status === 'completed' || currentStatus.status === 'failed') {
            clearInterval(poll);
            setIsRunning(false);
          }
        } catch {
          clearInterval(poll);
          setIsRunning(false);
        }
      }, 1000);
    } catch {
      setIsRunning(false);
    }
  };

  return (
    <section className="glass-card overflow-hidden">
      <div className="relative px-6 py-10 sm:px-10 sm:py-12 border-b border-white/[0.08] bg-gradient-to-br from-secondary/[0.12] via-surface/40 to-primary/[0.08]">
        <div className="max-w-2xl">
          <div className="w-12 h-12 rounded-2xl bg-primary text-slate-950 flex items-center justify-center shadow-[0_10px_28px_rgba(242,182,84,0.2)] mb-6">
            <FlaskConical className="w-6 h-6" />
          </div>
          <p className="eyebrow">Benchmark studio</p>
          <h2 className="display-font text-3xl sm:text-4xl font-semibold text-white mt-3">Put your models through their paces.</h2>
          <p className="text-white/60 leading-relaxed mt-4 max-w-xl">Run a controlled batch against a standard dataset, then use the results to balance quality, speed, and summary length.</p>
        </div>
      </div>

      <div className="p-6 sm:p-10 grid grid-cols-1 lg:grid-cols-[1fr_0.8fr] gap-8 lg:gap-12">
        <div className="space-y-7">
          <div>
            <p className="section-label flex items-center gap-2"><Database className="w-3.5 h-3.5" /> Dataset</p>
            <p className="text-sm text-white/50 mt-1">Choose the editorial style for this run.</p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-4">
              {[
                { id: 'cnn_dailymail', title: 'CNN / DailyMail', detail: 'Long-form, extractive reporting' },
                { id: 'xsum', title: 'XSum', detail: 'Concise, single-sentence briefs' },
              ].map((option) => (
                <button
                  key={option.id}
                  type="button"
                  onClick={() => setDataset(option.id as typeof dataset)}
                  className={`rounded-xl p-4 border text-left transition-all ${
                    dataset === option.id
                      ? 'bg-primary/[0.12] border-primary/55 shadow-[0_8px_22px_rgba(242,182,84,0.08)]'
                      : 'bg-black/15 border-white/[0.08] hover:bg-white/[0.05] hover:border-white/20'
                  }`}
                >
                  <span className="font-bold text-sm text-white block">{option.title}</span>
                  <span className="text-xs text-white/45 block mt-1.5">{option.detail}</span>
                </button>
              ))}
            </div>
          </div>

          <div>
            <div className="flex items-end justify-between gap-4">
              <div>
                <p className="section-label flex items-center gap-2"><Layers3 className="w-3.5 h-3.5" /> Evaluation set</p>
                <p className="text-sm text-white/50 mt-1">Scale the run to the confidence you need.</p>
              </div>
              <span className="display-font text-3xl text-primary">{numSamples}</span>
            </div>
            <input
              aria-label="Number of evaluation samples"
              type="range"
              min="1"
              max="100"
              value={numSamples}
              onChange={(event) => setNumSamples(+event.target.value)}
              className="w-full mt-5 accent-primary"
            />
            <div className="flex justify-between text-[11px] text-white/35 mt-2"><span>1 sample</span><span>100 samples</span></div>
          </div>
        </div>

        <aside className="rounded-2xl bg-black/15 border border-white/[0.08] p-5 sm:p-6 flex flex-col">
          <p className="section-label flex items-center gap-2"><Timer className="w-3.5 h-3.5" /> Run configuration</p>
          <div className="mt-5 space-y-4 text-sm">
            <div className="flex items-center justify-between gap-4"><span className="text-white/50">Models</span><span className="font-bold text-white/85">T5, BART, PEGASUS</span></div>
            <div className="h-px bg-white/[0.08]" />
            <div className="flex items-center justify-between gap-4"><span className="text-white/50">Dataset</span><span className="font-bold text-white/85">{dataset === 'cnn_dailymail' ? 'CNN / DailyMail' : 'XSum'}</span></div>
            <div className="h-px bg-white/[0.08]" />
            <div className="flex items-center justify-between gap-4"><span className="text-white/50">Sample count</span><span className="font-bold text-white/85">{numSamples}</span></div>
          </div>
          <button
            type="button"
            onClick={handleStart}
            disabled={isRunning}
            className="btn-primary w-full mt-auto pt-3.5 pb-3.5 disabled:opacity-40 disabled:grayscale flex items-center justify-center gap-2"
          >
            <Play className="w-4 h-4 fill-current" /> {isRunning ? 'Benchmark in progress...' : 'Launch benchmark'}
          </button>
        </aside>
      </div>

      {status && (
        <div className="mx-6 mb-6 sm:mx-10 sm:mb-10 rounded-2xl border border-secondary/20 bg-secondary/[0.07] p-5 sm:p-6">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
            <div className="flex items-center gap-3">
              <CheckCircle2 className={`w-5 h-5 ${status.status === 'failed' ? 'text-red-300' : 'text-secondary'}`} />
              <div>
                <p className="font-bold text-white/90 capitalize">{status.status}</p>
                <p className="text-xs text-white/45 mt-0.5">{status.current_step || 'Preparing experiment'}</p>
              </div>
            </div>
            <span className="text-primary font-bold">{Math.round(status.progress * 100)}%</span>
          </div>
          <div className="h-2.5 bg-black/30 rounded-full overflow-hidden border border-white/[0.05]">
            <div className="h-full bg-gradient-to-r from-secondary to-primary transition-all duration-500 ease-out" style={{ width: `${status.progress * 100}%` }} />
          </div>
          <p className="text-xs text-white/45 mt-3">{status.completed_samples} of {status.total_samples} samples complete</p>
        </div>
      )}
    </section>
  );
}
