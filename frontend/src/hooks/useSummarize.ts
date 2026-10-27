import { useState, useMemo } from 'react';
import type { SummarizationRequest, SummarizationResponse } from '@/lib/types';

export function useSummarize() {
  const [response, setResponse] = useState<SummarizationResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submitArticle = async (request: SummarizationRequest) => {
    setIsLoading(true);
    setError(null);
    setResponse(null);
    try {
      const res = await fetch('/api/summarize', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.error || data.detail || 'An error occurred during summarization');
      }
      const data: SummarizationResponse = await res.json();
      setResponse(data);
    } catch (err: any) {
      setError(err.message || 'An error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  const reset = () => {
    setResponse(null);
    setError(null);
    setIsLoading(false);
  };

  return {
    response,
    isLoading,
    error,
    submitArticle,
    reset
  };
}
