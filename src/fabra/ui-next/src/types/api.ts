// API response types matching Python backend

export interface Entity {
  name: string;
  id_column: string;
  description?: string;
}

export interface Feature {
  name: string;
  entity: string;
  refresh?: string;
  ttl?: string;
  materialize: boolean;
}

export interface Retriever {
  name: string;
  backend: string;
  cache_ttl: string;
}

export interface ContextDefinition {
  name: string;
  description?: string;
  parameters: ContextParameter[];
}

export interface ContextParameter {
  name: string;
  type: string;
  default?: string;
  required: boolean;
}

export interface FeatureLineage {
  feature_name: string;
  entity_id: string;
  value: unknown;
  timestamp: string;
  freshness_ms: number;
  source: 'cache' | 'compute' | 'fallback';
}

export interface RetrieverLineage {
  retriever_name: string;
  query: string;
  results_count: number;
  latency_ms: number;
  index_name?: string;
  chunks_returned?: DocumentChunkLineage[];
  stale_chunks_count?: number;
  oldest_chunk_ms?: number;
}

export interface ContextLineage {
  context_id: string;
  timestamp: string;
  features_used: FeatureLineage[];
  retrievers_used: RetrieverLineage[];
  items_provided: number;
  items_included: number;
  items_dropped: number;
  freshness_status: 'guaranteed' | 'degraded' | 'unknown';
  stalest_feature_ms: number;
  token_usage: number;
  max_tokens?: number;
  estimated_cost_usd: number;
}

export interface ContextResult {
  id: string;
  items: ContextItem[];
  meta: {
    token_usage?: number;
    cost_usd?: number;
    latency_ms?: number;
    freshness_status?: string;
  };
  lineage?: ContextLineage;
}

export interface ContextItem {
  content: string;
  priority: number;
  source?: string;
}

export interface StoreInfo {
  file_name: string;
  entities: Entity[];
  features: Feature[];
  contexts: ContextDefinition[];
  retrievers: Retriever[];
  online_store_type: string;
}

export interface FeatureValues {
  [key: string]: unknown;
}

export interface MermaidGraph {
  code: string;
}

// Context diff types
export interface FeatureDiff {
  feature_name: string;
  entity_id: string;
  old_value: unknown;
  new_value: unknown;
  change_type: 'added' | 'removed' | 'modified' | 'unchanged';
  old_freshness_ms?: number;
  new_freshness_ms?: number;
}

export interface RetrieverDiff {
  retriever_name: string;
  query_changed: boolean;
  old_query?: string;
  new_query?: string;
  old_results_count: number;
  new_results_count: number;
  chunks_added: string[];
  chunks_removed: string[];
  change_type: 'added' | 'removed' | 'modified' | 'unchanged';
}

export interface ContentDiff {
  lines_added: number;
  lines_removed: number;
  lines_changed: number;
  similarity_score: number;
  diff_summary: string;
}

export interface ContextDiff {
  base_context_id: string;
  comparison_context_id: string;
  timestamp: string;
  time_delta_ms: number;
  feature_diffs: FeatureDiff[];
  features_added: number;
  features_removed: number;
  features_modified: number;
  retriever_diffs: RetrieverDiff[];
  retrievers_added: number;
  retrievers_removed: number;
  retrievers_modified: number;
  content_diff?: ContentDiff;
  token_delta: number;
  cost_delta_usd: number;
  base_freshness_status: string;
  comparison_freshness_status: string;
  freshness_improved: boolean;
  has_changes: boolean;
  change_summary: string;
}

// Document chunk lineage with freshness
export interface DocumentChunkLineage {
  chunk_id: string;
  document_id: string;
  content_hash: string;
  source_url?: string;
  indexed_at: string;
  document_modified_at?: string;
  freshness_ms: number;
  is_stale: boolean;
  similarity_score: number;
  retriever_name: string;
  position_in_results: number;
}
