export type TaskType = "exploration" | "modeling" | "prediction";

export interface TaskProgress {
  task_id: string;
  phase: string;
  progress_pct: number;
  current_step: string;
  message: string;
  status?: string;
}

export interface Task {
  task_id: string;
  task_type: TaskType;
  data_source: string;
  requirements: Record<string, string>;
  status: string;
  phase: string;
  progress?: TaskProgress;
  results?: AnalysisResults;
  report?: Report;
  created_at: string;
  updated_at: string;
  error?: string;
}

export interface AnalysisResults {
  eda: EDAResults;
  basic_info: BasicInfo;
  quality_analysis: QualityAnalysis;
  statistical_analysis: Record<string, StatItem>;
  correlation_analysis: CorrelationAnalysis;
  outlier_analysis: Record<string, OutlierItem>;
  visualizations: Record<string, string>;
  problem_type?: string;
  model_results?: Record<string, ModelResult>;
  best_model_name?: string;
  feature_importance?: Record<string, number>;
  insights: Insight[];
  report: Report;
}

export interface BasicInfo {
  row_count: number;
  column_count: number;
  memory_usage_mb: number;
  dtypes: Record<string, string>;
}

export interface QualityAnalysis {
  missing_analysis: Record<string, { missing_count: number; missing_percentage: number }>;
  duplicate_count: number;
  duplicate_percentage: number;
  total_cells: number;
  missing_cells: number;
}

export interface StatItem {
  mean: number;
  std: number;
  min: number;
  q25: number;
  median: number;
  q75: number;
  max: number;
  skewness: number;
  kurtosis: number;
}

export interface CorrelationAnalysis {
  pairs: Array<{ var1: string; var2: string; correlation: number }>;
  matrix: Record<string, Record<string, number>>;
}

export interface OutlierItem {
  outlier_count: number;
  outlier_percentage: number;
  lower_bound: number;
  upper_bound: number;
}

export interface ModelResult {
  r2_score?: number;
  rmse?: number;
  accuracy?: number;
  f1_score?: number;
  cv_mean: number;
  cv_std: number;
  error?: string;
}

export interface Insight {
  type: string;
  title: string;
  description: string;
  importance_score: number;
  confidence: number;
}

export interface EDAResults extends Record<string, unknown> {
  basic_info: BasicInfo;
  quality_analysis: QualityAnalysis;
  statistical_analysis: Record<string, StatItem>;
  outlier_analysis: Record<string, OutlierItem>;
  correlation_analysis: CorrelationAnalysis;
}

export interface Report {
  executive_summary: string;
  key_insights: string[];
  recommendations: Array<{ title: string; detail: string; action: string }>;
  metadata: { generated_at: string; analysis_type: string; data_shape: { rows: number; cols: number } };
}

export interface UploadResult {
  task_id: string;
  filename: string;
  headers: string[];
  col_types: Record<string, string>;
  preview: string[][];
  total_rows: number;
}

export interface DatasetItem {
  name: string;
  description: string;
  row_count: number;
}
