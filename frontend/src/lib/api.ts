import axios, { AxiosError } from 'axios';
import type {
  SummarizationRequest,
  SummarizationResponse,
  EvaluationRequest,
  EvaluationResponse,
  ExperimentRequest,
  ExperimentStatus,
  ExperimentResult,
  ModelInfo,
  HealthResponse,
  ErrorResponse,
  QualitativeScoreInput,
  EvaluationResult,
} from './types';

const API_BASE = '/api';

const client = axios.create({
  baseURL: API_BASE,
  timeout: 300000, // 5 min — summarization can be slow on CPU
  headers: { 'Content-Type': 'application/json' },
});

client.interceptors.response.use(
  (response) => response,
  (error: AxiosError<ErrorResponse>) => {
    const message =
      error.response?.data?.error ||
      error.response?.data?.detail ||
      error.message ||
      'An unexpected error occurred';
    return Promise.reject(new Error(message));
  }
);

export async function healthCheck(): Promise<HealthResponse> {
  const { data } = await client.get<HealthResponse>('/health');
  return data;
}

export async function getModels(): Promise<ModelInfo[]> {
  const { data } = await client.get<ModelInfo[]>('/models');
  return data;
}

export async function summarize(request: SummarizationRequest): Promise<SummarizationResponse> {
  const { data } = await client.post<SummarizationResponse>('/summarize', request);
  return data;
}

export async function evaluate(request: EvaluationRequest): Promise<EvaluationResponse> {
  const { data } = await client.post<EvaluationResponse>('/evaluate', request);
  return data;
}

export async function submitQualitativeScore(score: QualitativeScoreInput): Promise<EvaluationResult> {
  const { data } = await client.post<EvaluationResult>('/qualitative-score', score);
  return data;
}

export async function startExperiment(request: ExperimentRequest): Promise<ExperimentStatus> {
  const { data } = await client.post<ExperimentStatus>('/experiment', request);
  return data;
}

export async function getExperimentStatus(experimentId: string): Promise<ExperimentStatus> {
  const { data } = await client.get<ExperimentStatus>(`/experiment/${experimentId}/status`);
  return data;
}

export async function getExperimentResults(experimentId: string): Promise<ExperimentResult> {
  const { data } = await client.get<ExperimentResult>(`/experiment/${experimentId}/results`);
  return data;
}
