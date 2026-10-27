'use client';

import { useState } from 'react';
import { Star } from 'lucide-react';

interface StarRatingProps {
  value: number;
  onChange: (v: number) => void;
  label: string;
}

export default function StarRating({ value, onChange, label }: StarRatingProps) {
  const [hover, setHover] = useState(0);
  const effective = hover || value;

  return (
    <div className="flex flex-col gap-1.5">
      <span className="text-[11px] text-white/40 font-medium">{label}</span>
      <div className="flex gap-1">
        {[1, 2, 3, 4, 5].map(i => (
          <button
            key={i}
            type="button"
            onClick={() => onChange(i)}
            onMouseEnter={() => setHover(i)}
            onMouseLeave={() => setHover(0)}
            aria-label={`${label}: ${i} out of 5`}
            aria-pressed={i === value}
            className="transition-transform hover:scale-110 active:scale-95"
          >
            <Star
              className={`w-5 h-5 transition-colors duration-150 ${
                i <= effective
                  ? 'text-amber-400 fill-amber-400'
                  : 'text-white/15 fill-transparent'
              }`}
            />
          </button>
        ))}
        {value > 0 && (
          <span className="ml-1.5 text-[11px] text-white/35 self-center">{value}/5</span>
        )}
      </div>
    </div>
  );
}
