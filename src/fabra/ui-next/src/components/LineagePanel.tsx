'use client';

import type { ContextLineage, FeatureLineage, RetrieverLineage } from '@/types/api';

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
      {isStale ? '⚠️' : '✓'} {formatMs(ms)}
    </span>
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

function RetrieverCard({ retriever }: { retriever: RetrieverLineage }) {
  return (
    <div className="bg-gray-900 border border-gray-700 rounded-lg p-3">
      <div className="flex items-center justify-between mb-2">
        <span className="font-mono text-blue-400 text-sm">
          {retriever.retriever_name}
        </span>
        <span className="text-xs text-gray-400">
          {retriever.latency_ms.toFixed(1)}ms
        </span>
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
        <div className="col-span-2">
          <span className="text-gray-500">Query:</span>
          <span className="text-gray-300 ml-1 truncate block">
            {retriever.query}
          </span>
        </div>
      </div>
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
          <h4 className="text-gray-200 font-semibold">Context Lineage</h4>
          <span
            className={`px-2 py-1 rounded text-xs font-medium ${statusBg} ${statusColor}`}
          >
            {lineage.freshness_status.toUpperCase()}
          </span>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div className="bg-gray-900 rounded p-3">
            <div className="text-gray-500 text-xs mb-1">Context ID</div>
            <div className="text-gray-300 font-mono text-xs truncate">
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
