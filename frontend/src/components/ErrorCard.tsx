import { AlertCircle, RefreshCw } from 'lucide-react';

interface ErrorCardProps {
  title?: string;
  message: string;
  onRetry?: () => void;
}

export default function ErrorCard({ title = 'Error', message, onRetry }: ErrorCardProps) {
  return (
    <div className="card border-red-200 bg-red-50 p-4 rounded-lg shadow-sm">
      <div className="flex items-start gap-3">
        <AlertCircle className="w-5 h-5 text-red-500 mt-0.5 flex-shrink-0" />
        <div className="flex-1">
          <h3 className="font-medium text-red-800">{title}</h3>
          <p className="text-sm text-red-600 mt-1">{message}</p>
        </div>
        {onRetry && (
          <button onClick={onRetry} className="flex items-center gap-1 px-3 py-1 bg-white border border-red-200 text-red-600 rounded text-sm hover:bg-red-50 transition-colors">
            <RefreshCw className="w-4 h-4" /> Retry
          </button>
        )}
      </div>
    </div>
  );
}
