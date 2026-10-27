'use client';
import { useState, useEffect } from 'react';
import { Activity, Bot } from 'lucide-react';
import { healthCheck } from '@/lib/api';

export default function Header() {
  const [isOnline, setIsOnline] = useState(false);

  useEffect(() => {
    healthCheck().then(() => setIsOnline(true)).catch(() => setIsOnline(false));
  }, []);

  return (
    <header className="w-full border-b border-white/[0.08] bg-background/75 backdrop-blur-xl sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-5 sm:px-6 h-[72px] flex items-center justify-between">
        <div className="flex items-center gap-3.5">
          <div className="w-10 h-10 rounded-xl bg-primary text-slate-950 flex items-center justify-center shadow-[0_8px_22px_rgba(242,182,84,0.2)]">
            <Bot className="w-5 h-5" strokeWidth={2.25} />
          </div>
          <div>
            <span className="font-bold tracking-tight text-white block leading-none">Newsroom</span>
            <span className="text-[10px] uppercase tracking-[0.18em] text-white/40 mt-1 block">AI summary lab</span>
          </div>
        </div>
        
        <div className="flex items-center gap-2.5 bg-white/[0.045] px-3 py-2 rounded-full border border-white/[0.08]">
          <Activity className={`w-3.5 h-3.5 ${isOnline ? 'text-secondary' : 'text-amber-300'}`} />
          <span className="text-[11px] font-bold text-white/70 uppercase tracking-[0.12em]">
            {isOnline ? 'Ready' : 'Connecting'}
          </span>
        </div>
      </div>
    </header>
  );
}
