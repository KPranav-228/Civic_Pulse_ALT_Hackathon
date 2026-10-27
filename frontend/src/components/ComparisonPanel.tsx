'use client';

import { useState } from 'react';
import { Bar, BarChart, CartesianGrid, Radar, RadarChart, ResponsiveContainer, Tooltip, XAxis, YAxis, PolarAngleAxis, PolarGrid, PolarRadiusAxis } from 'recharts';
import { BarChart3, Gauge, Radar as RadarIcon, Timer } from 'lucide-react';
import type { SummarizationResponse } from '@/lib/types';

type View = 'rouge' | 'radar' | 'speed' | 'compression';

const views: { id: View; label: string; icon: typeof BarChart3 }[] = [
  { id: 'rouge', label: 'ROUGE', icon: BarChart3 },
  { id: 'radar', label: 'Shape', icon: RadarIcon },
  { id: 'speed', label: 'Speed', icon: Timer },
  { id: 'compression', label: 'Length', icon: Gauge },
];

const colors = ['#f2b654', '#23b6a8', '#49a7ff', '#ef735f'];

const chartTooltip = {
  cursor: { fill: 'rgba(255,255,255,0.035)' },
  contentStyle: {
    backgroundColor: '#0c2029',
    borderColor: 'rgba(255,255,255,0.12)',
    borderRadius: '12px',
    color: '#e7f0ef',
    fontSize: '12px',
  },
};

export default function ComparisonPanel({ response }: { response: SummarizationResponse | null }) {
  const [view, setView] = useState<View>('rouge');

  if (!response) {
    return (
      <section className="glass-card h-[430px] p-6 flex flex-col items-center justify-center text-center border-dashed border-white/20">
        <div className="w-12 h-12 rounded-2xl bg-white/[0.045] flex items-center justify-center border border-white/[0.08]">
          <BarChart3 className="w-6 h-6 text-white/35" />
        </div>
        <h2 className="font-bold text-white/80 mt-4">Nothing to compare yet</h2>
        <p className="text-sm text-white/45 mt-2 max-w-xs">Generate at least one summary to turn this into an evidence board.</p>
      </section>
    );
  }

  const successful = response.summaries.filter((summary) => summary.status === 'success');
  const chartData = successful.map((summary) => {
    const evaluation = response.evaluation?.find((entry) => entry.model === summary.model);

    return {
      name: summary.model.toUpperCase(),
      time: summary.generation_time_seconds ?? 0,
      compression: summary.compression_ratio != null ? summary.compression_ratio * 100 : 0,
      rouge1: evaluation?.rouge?.rouge_1 != null ? evaluation.rouge.rouge_1 * 100 : 0,
      rouge2: evaluation?.rouge?.rouge_2 != null ? evaluation.rouge.rouge_2 * 100 : 0,
      rougeL: evaluation?.rouge?.rouge_l != null ? evaluation.rouge.rouge_l * 100 : 0,
    };
  });

  const radarData = [
    { metric: 'ROUGE-1', ...Object.fromEntries(chartData.map((item) => [item.name, item.rouge1])) },
    { metric: 'ROUGE-2', ...Object.fromEntries(chartData.map((item) => [item.name, item.rouge2])) },
    { metric: 'ROUGE-L', ...Object.fromEntries(chartData.map((item) => [item.name, item.rougeL])) },
    { metric: 'Length', ...Object.fromEntries(chartData.map((item) => [item.name, item.compression])) },
  ];

  const activeView = views.find((item) => item.id === view);

  return (
    <section className="glass-card p-5 sm:p-6 flex flex-col gap-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between border-b border-white/[0.08] pb-5">
        <div>
          <p className="section-label flex items-center gap-2"><BarChart3 className="w-3.5 h-3.5" /> Evidence board</p>
          <h2 className="text-xl font-bold text-white mt-2">Compare the trade-offs</h2>
          <p className="text-sm text-white/50 mt-1">{successful.length} successful model runs in this readout.</p>
        </div>
        <div className="flex gap-1 overflow-x-auto bg-black/20 p-1.5 rounded-xl border border-white/[0.08]">
          {views.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              type="button"
              onClick={() => setView(id)}
              className={`flex items-center gap-1.5 whitespace-nowrap px-3 py-2 rounded-lg text-xs font-bold transition-colors ${
                view === id ? 'bg-primary text-slate-950' : 'text-white/50 hover:text-white hover:bg-white/[0.06]'
              }`}
            >
              <Icon className="w-3.5 h-3.5" /> {label}
            </button>
          ))}
        </div>
      </div>

      <div className="flex items-center justify-between text-xs text-white/45">
        <span>{activeView?.label} view</span>
        <span>Values shown as percentages except speed.</span>
      </div>

      <div className="h-[330px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          {view === 'rouge' ? (
            <BarChart data={chartData} margin={{ top: 16, right: 10, left: -15, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 4" stroke="rgba(255,255,255,0.09)" vertical={false} />
              <XAxis dataKey="name" tick={{ fill: 'rgba(231,240,239,0.55)', fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: 'rgba(231,240,239,0.45)', fontSize: 11 }} axisLine={false} tickLine={false} />
              <Tooltip {...chartTooltip} />
              <Bar dataKey="rouge1" name="ROUGE-1" fill="#f2b654" radius={[5, 5, 0, 0]} />
              <Bar dataKey="rouge2" name="ROUGE-2" fill="#23b6a8" radius={[5, 5, 0, 0]} />
              <Bar dataKey="rougeL" name="ROUGE-L" fill="#49a7ff" radius={[5, 5, 0, 0]} />
            </BarChart>
          ) : view === 'speed' ? (
            <BarChart data={chartData} layout="vertical" margin={{ top: 16, right: 10, left: 8, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 4" stroke="rgba(255,255,255,0.09)" horizontal={false} />
              <XAxis type="number" tick={{ fill: 'rgba(231,240,239,0.45)', fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis type="category" dataKey="name" tick={{ fill: 'rgba(231,240,239,0.55)', fontSize: 11 }} axisLine={false} tickLine={false} />
              <Tooltip {...chartTooltip} />
              <Bar dataKey="time" name="Latency (seconds)" fill="#23b6a8" radius={[0, 5, 5, 0]} />
            </BarChart>
          ) : view === 'compression' ? (
            <BarChart data={chartData} margin={{ top: 16, right: 10, left: -15, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 4" stroke="rgba(255,255,255,0.09)" vertical={false} />
              <XAxis dataKey="name" tick={{ fill: 'rgba(231,240,239,0.55)', fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: 'rgba(231,240,239,0.45)', fontSize: 11 }} axisLine={false} tickLine={false} />
              <Tooltip {...chartTooltip} />
              <Bar dataKey="compression" name="Summary length (%)" fill="#f2b654" radius={[5, 5, 0, 0]} />
            </BarChart>
          ) : (
            <RadarChart data={radarData} outerRadius="72%">
              <PolarGrid stroke="rgba(255,255,255,0.12)" />
              <PolarAngleAxis dataKey="metric" tick={{ fill: 'rgba(231,240,239,0.65)', fontSize: 11 }} />
              <PolarRadiusAxis tick={false} axisLine={false} />
              <Tooltip {...chartTooltip} />
              {chartData.map((item, index) => (
                <Radar
                  key={item.name}
                  name={item.name}
                  dataKey={item.name}
                  stroke={colors[index % colors.length]}
                  fill={colors[index % colors.length]}
                  fillOpacity={0.11}
                />
              ))}
            </RadarChart>
          )}
        </ResponsiveContainer>
      </div>
    </section>
  );
}
