'use client';

import { useState } from 'react';
import { Check, Cloud, Cpu, FileText, Gauge, ListTree, Sparkles, WandSparkles } from 'lucide-react';
import { MODEL_OPTIONS, ModelName, SummarizationRequest } from '@/lib/types';

interface Props {
  onSubmit: (request: SummarizationRequest) => void;
  isLoading: boolean;
}

const sampleArticle = `The European Central Bank cut interest rates by a quarter point on Thursday, a widely expected move that offers some relief to consumers and businesses following a prolonged period of aggressive monetary tightening.

The ECB's Governing Council lowered its key deposit rate to 3.75% from a record high of 4.0%, marking its first rate cut in nearly five years. The decision comes as inflation across the 20-nation euro zone has cooled significantly, dropping from a peak of over 10% in late 2022 to 2.6% in May.

Based on an updated assessment of the inflation outlook, the dynamics of underlying inflation and the strength of monetary policy transmission, it is now appropriate to moderate the degree of monetary policy restriction, the ECB said in a statement.`;

export default function InputPanel({ onSubmit, isLoading }: Props) {
  const [articleText, setArticleText] = useState('');
  const [selectedModels, setSelectedModels] = useState<ModelName[]>(MODEL_OPTIONS.map((model) => model.name));
  const [maxLength, setMaxLength] = useState(150);
  const [minLength, setMinLength] = useState(30);

  const words = articleText.trim() ? articleText.trim().split(/\s+/).length : 0;
  const stats = {
    words,
    sentences: articleText.split(/[.!?]+/).filter((sentence) => sentence.trim().length > 0).length,
    tokens: Math.round(words * 1.3),
  };

  const toggleModel = (name: ModelName) => {
    setSelectedModels((current) => (
      current.includes(name) ? current.filter((model) => model !== name) : [...current, name]
    ));
  };

  return (
    <section className="glass-card p-5 sm:p-6 flex flex-col gap-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="section-label flex items-center gap-2"><FileText className="w-3.5 h-3.5" /> Source article</p>
          <h2 className="text-xl font-bold tracking-tight text-white mt-2">Set the brief</h2>
          <p className="text-sm leading-relaxed text-white/50 mt-1">Paste the reporting you want to distill.</p>
        </div>
        <button
          type="button"
          onClick={() => setArticleText(sampleArticle)}
          className="btn-secondary shrink-0 px-3 py-2 text-xs flex items-center gap-1.5"
        >
          <WandSparkles className="w-3.5 h-3.5 text-primary" /> Try sample
        </button>
      </div>

      <div className="relative">
        <label htmlFor="article-text" className="sr-only">Article text</label>
        <textarea
          id="article-text"
          value={articleText}
          onChange={(event) => setArticleText(event.target.value)}
          placeholder="Paste a news article, report, or transcript here..."
          className="w-full h-64 bg-black/20 border border-white/[0.1] rounded-2xl p-4 pr-6 text-white/90 leading-relaxed placeholder:text-white/30 outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary/60 transition-all resize-none"
        />
        <div className="absolute bottom-4 right-4 h-10 w-1 rounded-full bg-gradient-to-b from-primary to-secondary opacity-70 pointer-events-none" />
      </div>

      <div className="grid grid-cols-3 gap-2">
        <div className="metric-chip"><FileText className="w-3.5 h-3.5 text-primary" /><span><b className="text-white">{stats.words}</b> words</span></div>
        <div className="metric-chip"><ListTree className="w-3.5 h-3.5 text-secondary" /><span><b className="text-white">{stats.sentences}</b> sentences</span></div>
        <div className="metric-chip"><Gauge className="w-3.5 h-3.5 text-amber-200" /><span><b className="text-white">{stats.tokens}</b> tokens</span></div>
      </div>

      <div className="h-px bg-white/[0.08] w-full" />

      <div>
        <div className="flex items-end justify-between mb-4">
          <div>
            <p className="section-label flex items-center gap-2"><Cpu className="w-3.5 h-3.5" /> Model desk</p>
            <p className="text-sm text-white/60 mt-1">Pick the models to run in parallel.</p>
          </div>
          <span className="text-xs font-bold text-primary">{selectedModels.length}/4</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
          {MODEL_OPTIONS.map((model) => {
            const active = selectedModels.includes(model.name);
            const isCloud = model.name === 'llm';

            return (
              <button
                key={model.name}
                type="button"
                onClick={() => toggleModel(model.name)}
                aria-pressed={active}
                className={`p-3.5 rounded-xl border text-left transition-all ${
                  active
                    ? 'bg-primary/[0.12] border-primary/55 shadow-[0_8px_24px_rgba(242,182,84,0.08)]'
                    : 'bg-black/15 border-white/[0.08] hover:bg-white/[0.055] hover:border-white/20'
                }`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <span className={`font-bold text-sm block ${active ? 'text-white' : 'text-white/70'}`}>{model.display_name}</span>
                    <span className="mt-1 text-[11px] uppercase tracking-[0.12em] text-white/40 flex items-center gap-1">
                      {isCloud ? <Cloud className="w-3 h-3" /> : <Cpu className="w-3 h-3" />}
                      {isCloud ? 'Cloud' : 'Local'}
                    </span>
                  </div>
                  <span className={`w-5 h-5 rounded-full border flex items-center justify-center ${active ? 'bg-primary border-primary text-slate-950' : 'border-white/25'}`}>
                    {active && <Check className="w-3.5 h-3.5" strokeWidth={3} />}
                  </span>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      <div className="h-px bg-white/[0.08] w-full" />

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
        <label className="block">
          <span className="flex items-center justify-between text-[11px] font-bold uppercase tracking-[0.14em] text-white/45 mb-3">
            Minimum length <b className="text-secondary text-xs">{minLength} words</b>
          </span>
          <input
            type="range"
            min="10"
            max="100"
            value={minLength}
            onChange={(event) => setMinLength(+event.target.value)}
            className="w-full accent-secondary"
          />
        </label>
        <label className="block">
          <span className="flex items-center justify-between text-[11px] font-bold uppercase tracking-[0.14em] text-white/45 mb-3">
            Maximum length <b className="text-primary text-xs">{maxLength} words</b>
          </span>
          <input
            type="range"
            min="50"
            max="300"
            value={maxLength}
            onChange={(event) => setMaxLength(+event.target.value)}
            className="w-full accent-primary"
          />
        </label>
      </div>

      <button
        type="button"
        onClick={() => onSubmit({ article_text: articleText, models: selectedModels, max_length: maxLength, min_length: minLength, num_beams: 4 })}
        disabled={isLoading || articleText.length < 50 || selectedModels.length === 0}
        className="btn-primary w-full mt-1 disabled:opacity-40 disabled:grayscale disabled:cursor-not-allowed flex items-center justify-center gap-2"
      >
        <Sparkles className="w-4 h-4" />
        {isLoading ? 'Building summaries...' : 'Generate summaries'}
      </button>
    </section>
  );
}
