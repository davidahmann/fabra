'use client';

import { useState } from 'react';
import type { ContextLineage, FeatureLineage, RetrieverLineage, DocumentChunkLineage } from '@/types/api';

interface LineagePanelProps {
  lineage: ContextLineage;
}

function formatMs(ms: number): string {
  if (ms < 1000) return `${ms}ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
  return `${(ms / 60000).toFixed(1)}m`;
}

function FreshnessIndicator({ ms, slaMs }: { ms: number; slaMs?: number }) {
  const isStale = slaMs !== undefined && ms > slaMs;
  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium ${
        isStale
          ? 'bg-red-500/20 text-red-400'
          : 'bg-green-500/20 text-green-400'
      }`}
    >
      {isStale ? '!' : '\u2713'} {formatMs(ms)}
    </span>
  );
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  return (
    <button
      onClick={handleCopy}
      className="p-1 text-gray-500 hover:text-gray-300 transition"
      title="Copy to clipboard"
    >
      {copied ? (
        <svg className="w-3.5 h-3.5 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
        </svg>
      ) : (
        <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
        </svg>
      )}
    </button>
  );
}

function FeatureCard({ feature }: { feature: FeatureLineage }) {
  return (
    <div className="bg-gray-900 border border-gray-700 rounded-lg p-3">
      <div className="flex items-center justify-between mb-2">
        <span className="font-mono text-green-400 text-sm">
          {feature.feature_name}
        </span>
        <FreshnessIndicator ms={feature.freshness_ms} />
      </div>
      <div className="grid grid-cols-2 gap-2 text-xs">
        <div>
          <span className="text-gray-500">Entity:</span>
          <span className="text-gray-300 ml-1">{feature.entity_id}</span>
        </div>
        <div>
          <span className="text-gray-500">Source:</span>
          <span
            className={`ml-1 ${
              feature.source === 'cache'
                ? 'text-blue-400'
                : feature.source === 'compute'
                ? 'text-green-400'
                : 'text-yellow-400'
            }`}
          >
            {feature.source}
          </span>
        </div>
        <div className="col-span-2">
          <span className="text-gray-500">Value:</span>
          <span className="text-gray-300 ml-1 font-mono">
            {JSON.stringify(feature.value)}
          </span>
        </div>
      </div>
    </div>
  );
}

function ChunkCard({ chunk }: { chunk: DocumentChunkLineage }) {
  return (
    <div className={`bg-gray-800 border rounded p-2 text-xs ${
      chunk.is_stale ? 'border-red-500/50' : 'border-gray-700'
    }`}>
      <div className="flex items-center justify-between mb-1">
        <div className="flex items-center gap-1">
          <span className="font-mono text-gray-400 truncate max-w-[120px]" title={chunk.chunk_id}>
            {chunk.chunk_id.slice(0, 12)}...
          </span>
          <CopyButton text={chunk.chunk_id} />
        </div>
        <span className={`px-1.5 py-0.5 rounded text-xs ${
          chunk.is_stale ? 'bg-red-500/20 text-red-400' : 'bg-green-500/20 text-green-400'
        }`}>
          {chunk.is_stale ? 'STALE' : 'FRESH'}
        </span>
      </div>
      <div className="grid grid-cols-2 gap-1 text-gray-500">
        <div>
          <span>Score:</span>
          <span className="text-blue-400 ml-1">{chunk.similarity_score.toFixed(3)}</span>
        </div>
        <div>
          <span>Age:</span>
          <span className={chunk.is_stale ? 'text-red-400' : 'text-gray-300'}> {formatMs(chunk.freshness_ms)}</span>
        </div>
        <div>
          <span>Pos:</span>
          <span className="text-gray-300 ml-1">#{chunk.position_in_results + 1}</span>
        </div>
        {chunk.source_url && (
          <div className="truncate" title={chunk.source_url}>
            <span>URL:</span>
            <span className="text-gray-400 ml-1">{chunk.source_url.split('/').pop()}</span>
          </div>
        )}
      </div>
    </div>
  );
}

function RetrieverCard({ retriever }: { retriever: RetrieverLineage }) {
  const [showChunks, setShowChunks] = useState(false);
  const hasChunks = retriever.chunks_returned && retriever.chunks_returned.length > 0;
  const staleCount = retriever.stale_chunks_count || 0;

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-lg p-3">
      <div className="flex items-center justify-between mb-2">
        <span className="font-mono text-blue-400 text-sm">
          {retriever.retriever_name}
        </span>
        <div className="flex items-center gap-2">
          {staleCount > 0 && (
            <span className="text-xs bg-red-500/20 text-red-400 px-1.5 py-0.5 rounded">
              {staleCount} stale
            </span>
          )}
          <span className="text-xs text-gray-400">
            {retriever.latency_ms.toFixed(1)}ms
          </span>
        </div>
      </div>
      <div className="grid grid-cols-2 gap-2 text-xs">
        <div>
          <span className="text-gray-500">Results:</span>
          <span className="text-gray-300 ml-1">{retriever.results_count}</span>
        </div>
        {retriever.index_name && (
          <div>
            <span className="text-gray-500">Index:</span>
            <span className="text-gray-300 ml-1">{retriever.index_name}</span>
          </div>
        )}
        {retriever.oldest_chunk_ms !== undefined && retriever.oldest_chunk_ms > 0 && (
          <div>
            <span className="text-gray-500">Oldest:</span>
            <span className="text-gray-300 ml-1">{formatMs(retriever.oldest_chunk_ms)}</span>
          </div>
        )}
        <div className="col-span-2">
          <span className="text-gray-500">Query:</span>
          <span className="text-gray-300 ml-1 truncate block">
            {retriever.query}
          </span>
        </div>
      </div>

      {/* Expandable Chunks Section */}
      {hasChunks && (
        <div className="mt-3 pt-3 border-t border-gray-700">
          <button
            onClick={() => setShowChunks(!showChunks)}
            className="flex items-center gap-1 text-xs text-gray-400 hover:text-gray-300 transition"
          >
            <svg
              className={`w-3 h-3 transform transition-transform ${showChunks ? 'rotate-90' : ''}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
            {retriever.chunks_returned!.length} chunks returned
          </button>
          {showChunks && (
            <div className="mt-2 space-y-2">
              {retriever.chunks_returned!.map((chunk, idx) => (
                <ChunkCard key={idx} chunk={chunk} />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function LineagePanel({ lineage }: LineagePanelProps) {
  const statusColor =
    lineage.freshness_status === 'guaranteed'
      ? 'text-green-400'
      : lineage.freshness_status === 'degraded'
      ? 'text-yellow-400'
      : 'text-gray-400';

  const statusBg =
    lineage.freshness_status === 'guaranteed'
      ? 'bg-green-500/20'
      : lineage.freshness_status === 'degraded'
      ? 'bg-yellow-500/20'
      : 'bg-gray-500/20';

  return (
    <div className="space-y-4">
      {/* Header Stats */}
      <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <h4 className="text-gray-200 font-semibold">Context Lineage</h4>
            <CopyButton text={lineage.context_id} />
          </div>
          <span
            className={`px-2 py-1 rounded text-xs font-medium ${statusBg} ${statusColor}`}
          >
            {lineage.freshness_status.toUpperCase()}
          </span>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div className="bg-gray-900 rounded p-3">
            <div className="text-gray-500 text-xs mb-1">Context ID</div>
            <div className="text-gray-300 font-mono text-xs truncate flex items-center gap-1">
              {lineage.context_id.slice(0, 12)}...
            </div>
          </div>
          <div className="bg-gray-900 rounded p-3">
            <div className="text-gray-500 text-xs mb-1">Token Usage</div>
            <div className="text-gray-300">
              {lineage.token_usage.toLocaleString()}
              {lineage.max_tokens && (
                <span className="text-gray-500">
                  {' '}
                  / {lineage.max_tokens.toLocaleString()}
                </span>
              )}
            </div>
          </div>
          <div className="bg-gray-900 rounded p-3">
            <div className="text-gray-500 text-xs mb-1">Items</div>
            <div className="text-gray-300">
              {lineage.items_included} included
              {lineage.items_dropped > 0 && (
                <span className="text-yellow-400">
                  {' '}
                  ({lineage.items_dropped} dropped)
                </span>
              )}
            </div>
          </div>
          <div className="bg-gray-900 rounded p-3">
            <div className="text-gray-500 text-xs mb-1">Est. Cost</div>
            <div className="text-gray-300">
              ${lineage.estimated_cost_usd.toFixed(6)}
            </div>
          </div>
        </div>

        {lineage.stalest_feature_ms > 0 && (
          <div className="mt-3 text-xs text-gray-400">
            Stalest feature: {formatMs(lineage.stalest_feature_ms)} old
          </div>
        )}
      </div>

      {/* Features Used */}
      {lineage.features_used.length > 0 && (
        <div>
          <h5 className="text-gray-400 text-sm font-medium mb-2 flex items-center gap-2">
            <svg
              className="w-4 h-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4"
              />
            </svg>
            Features Used ({lineage.features_used.length})
          </h5>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            {lineage.features_used.map((feature, idx) => (
              <FeatureCard key={idx} feature={feature} />
            ))}
          </div>
        </div>
      )}

      {/* Retrievers Used */}
      {lineage.retrievers_used.length > 0 && (
        <div>
          <h5 className="text-gray-400 text-sm font-medium mb-2 flex items-center gap-2">
            <svg
              className="w-4 h-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
            Retrievers Used ({lineage.retrievers_used.length})
          </h5>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            {lineage.retrievers_used.map((retriever, idx) => (
              <RetrieverCard key={idx} retriever={retriever} />
            ))}
          </div>
        </div>
      )}

      {/* Empty state */}
      {lineage.features_used.length === 0 &&
        lineage.retrievers_used.length === 0 && (
          <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-6 text-center">
            <div className="text-gray-500 text-sm">
              No features or retrievers were tracked during this context
              assembly.
            </div>
            <div className="text-gray-600 text-xs mt-2">
              Tip: Use store.get_feature() or @retriever within your @context
              function to track lineage.
            </div>
          </div>
        )}
    </div>
  );
}
