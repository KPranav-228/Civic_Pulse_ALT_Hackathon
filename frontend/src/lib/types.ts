// Enums
export type ModelName = 't5' | 'bart' | 'pegasus' | 'llm';
export type SummaryStatus = 'success' | 'error' | 'skipped';
export type ExperimentStatusType = 'pending' | 'running' | 'completed' | 'failed';

// Request types
export interface SummarizationRequest {
  article_text: string;
  models: ModelName[];
  max_length: number;
  min_length: number;
  num_beams: number;
  reference_summary?: string | null;
}

export interface ExperimentRequest {
  dataset: 'cnn_dailymail' | 'xsum';
  num_samples: number;
  models: ModelName[];
  include_llm: boolean;
  max_length: number;
  min_length: number;
}

export interface EvaluationRequest {
  summary: string;
  reference_summary: string;
  model_name?: string | null;
}

export interface QualitativeScoreInput {
  model: string;
  coherence: number;
  readability: number;
  factual_consistency: number;
  semantic_relevance: number;
  notes?: string | null;
}

// Response types
export interface ArticleStats {
  char_count: number;
  word_count: number;
  sentence_count: number;
  estimated_tokens: number;
}

export interface PreprocessingInfo {
  original_length: number;
  cleaned_length: number;
  was_chunked: boolean;
  num_chunks: number;
  cleaning_steps: string[];
}

export interface SummaryResult {
  model: string;
  summary: string | null;
  word_count: number | null;
  compression_ratio: number | null;
  generation_time_seconds: number | null;
  status: SummaryStatus;
  error?: string | null;
}

export interface RougeScores {
  rouge_1: number;
  rouge_2: number;
  rouge_l: number;
}

export interface QualitativeScore {
  coherence: number;
  readability: number;
  factual_consistency: number;
  semantic_relevance: number;
  notes?: string | null;
}

export interface EvaluationResult {
  model: string;
  rouge: RougeScores | null;
  qualitative: QualitativeScore | null;
  message?: string | null;
}

export interface ComparisonResult {
  rankings: Record<string, any>[];
  best_model: string | null;
  analysis: string;
}

export interface SummarizationResponse {
  request_id: string;
  article_stats: ArticleStats;
  preprocessing_info: PreprocessingInfo;
  summaries: SummaryResult[];
  evaluation: EvaluationResult[] | null;
  comparison: ComparisonResult | null;
  timestamp: string;
}

export interface EvaluationResponse {
  rouge: RougeScores;
  model_name?: string | null;
}

export interface ModelInfo {
  name: string;
  display_name: string;
  checkpoint: string;
  status: 'available' | 'loaded' | 'error' | 'unavailable';
  description: string;
  max_input_tokens: number;
  is_local: boolean;
}

export interface HealthResponse {
  status: string;
  app_name: string;
  version: string;
  device: string;
  loaded_models: string[];
  available_models: string[];
  groq_configured: boolean;
}

export interface ExperimentStatus {
  experiment_id: string;
  status: ExperimentStatusType;
  progress: number;
  current_step: string;
  total_samples: number;
  completed_samples: number;
  errors: string[];
}

export interface ExperimentResult {
  experiment_id: string;
  dataset: string;
  num_samples: number;
  models: string[];
  results: Record<string, any>[];
  aggregate_scores: Record<string, any>;
  timestamp: string;
  execution_time_seconds: number;
  device: string;
}

export interface ErrorResponse {
  error: string;
  detail?: string | null;
  status_code: number;
}

// UI state types
export interface ModelSelection {
  name: ModelName;
  display_name: string;
  selected: boolean;
  checkpoint: string;
}

export const MODEL_OPTIONS: ModelSelection[] = [
  { name: 't5', display_name: 'T5-Small', selected: true, checkpoint: 't5-small' },
  { name: 'bart', display_name: 'DistilBART-CNN', selected: true, checkpoint: 'sshleifer/distilbart-cnn-12-6' },
  { name: 'pegasus', display_name: 'PEGASUS-XSum', selected: true, checkpoint: 'google/pegasus-xsum' },
  { name: 'llm', display_name: 'Llama 3.3 70B (Groq)', selected: true, checkpoint: 'llama-3.3-70b-versatile' },
];
