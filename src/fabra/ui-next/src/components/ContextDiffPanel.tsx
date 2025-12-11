'use client';

import type { ContextDiff, FeatureDiff, RetrieverDiff } from '@/types/api';

interface ContextDiffPanelProps {
  diff: ContextDiff;
}

function formatMs(ms: number): string {
  if (Math.abs(ms) < 1000) return `${ms}ms`;
  if (Math.abs(ms) < 60000) return `${(ms / 1000).toFixed(1)}s`;
  return `${(ms / 60000).toFixed(1)}m`;
}

function ChangeTypeBadge({ type }: { type: string }) {
  const colors = {
    added: 'bg-green-500/20 text-green-400',
    removed: 'bg-red-500/20 text-red-400',
    modified: 'bg-yellow-500/20 text-yellow-400',
    unchanged: 'bg-gray-500/20 text-gray-400',
  };

  const icons = {
    added: '+',
    removed: '-',
    modified: '~',
    unchanged: '=',
  };

  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium ${
        colors[type as keyof typeof colors] || colors.unchanged
      }`}
    >
      {icons[type as keyof typeof icons] || '='} {type}
    </span>
  );
}

function FeatureDiffCard({ diff }: { diff: FeatureDiff }) {
  return (
    <div className="bg-gray-900 border border-gray-700 rounded-lg p-3">
      <div className="flex items-center justify-between mb-2">
        <span className="font-mono text-green-400 text-sm">{diff.feature_name}</span>
        <ChangeTypeBadge type={diff.change_type} />
      </div>
      <div className="grid grid-cols-2 gap-2 text-xs">
        <div>
          <span className="text-gray-500">Entity:</span>
          <span className="text-gray-300 ml-1">{diff.entity_id}</span>
        </div>
        {diff.change_type === 'modified' && (
          <>
            <div className="col-span-2 mt-2">
              <span className="text-gray-500">Old:</span>
              <span className="text-red-400 ml-1 font-mono">
                {JSON.stringify(diff.old_value)}
              </span>
            </div>
            <div className="col-span-2">
              <span className="text-gray-500">New:</span>
              <span className="text-green-400 ml-1 font-mono">
                {JSON.stringify(diff.new_value)}
              </span>
            </div>
          </>
        )}
        {diff.change_type === 'added' && (
          <div className="col-span-2">
            <span className="text-gray-500">Value:</span>
            <span className="text-green-400 ml-1 font-mono">
              {JSON.stringify(diff.new_value)}
            </span>
          </div>
        )}
        {diff.change_type === 'removed' && (
          <div className="col-span-2">
            <span className="text-gray-500">Value:</span>
            <span className="text-red-400 ml-1 font-mono line-through">
              {JSON.stringify(diff.old_value)}
            </span>
          </div>
        )}
        {(diff.old_freshness_ms !== undefined || diff.new_freshness_ms !== undefined) && (
          <div className="col-span-2 mt-1">
            <span className="text-gray-500">Freshness:</span>
            {diff.old_freshness_ms !== undefined && (
              <span className="text-gray-400 ml-1">{formatMs(diff.old_freshness_ms)}</span>
            )}
            {diff.old_freshness_ms !== undefined && diff.new_freshness_ms !== undefined && (
              <span className="text-gray-500 mx-1">-&gt;</span>
            )}
            {diff.new_freshness_ms !== undefined && (
              <span className="text-gray-300">{formatMs(diff.new_freshness_ms)}</span>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function RetrieverDiffCard({ diff }: { diff: RetrieverDiff }) {
  return (
    <div className="bg-gray-900 border border-gray-700 rounded-lg p-3">
      <div className="flex items-center justify-between mb-2">
        <span className="font-mono text-blue-400 text-sm">{diff.retriever_name}</span>
        <ChangeTypeBadge type={diff.change_type} />
      </div>
      <div className="grid grid-cols-2 gap-2 text-xs">
        <div>
          <span className="text-gray-500">Results:</span>
          <span className="text-gray-300 ml-1">
            {diff.old_results_count}
            <span className="text-gray-500 mx-1">-&gt;</span>
            {diff.new_results_count}
          </span>
        </div>
        {diff.query_changed && (
          <div className="col-span-2 text-yellow-400">Query changed</div>
        )}
        {diff.chunks_added.length > 0 && (
          <div className="col-span-2 mt-1">
            <span className="text-green-400">+{diff.chunks_added.length} chunks</span>
            {diff.chunks_added.length <= 3 && (
              <span className="text-gray-500 ml-2 truncate">
                {diff.chunks_added.join(', ')}
              </span>
            )}
          </div>
        )}
        {diff.chunks_removed.length > 0 && (
          <div className="col-span-2">
            <span className="text-red-400">-{diff.chunks_removed.length} chunks</span>
            {diff.chunks_removed.length <= 3 && (
              <span className="text-gray-500 ml-2 truncate">
                {diff.chunks_removed.join(', ')}
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default function ContextDiffPanel({ diff }: ContextDiffPanelProps) {
  const hasFeatureChanges = diff.feature_diffs.some((f) => f.change_type !== 'unchanged');
  const hasRetrieverChanges = diff.retriever_diffs.some((r) => r.change_type !== 'unchanged');

  return (
    <div className="space-y-4">
      {/* Summary Header */}
      <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
        <div className="flex items-center justify-between mb-4">
          <h4 className="text-gray-200 font-semibold">Context Diff</h4>
          <span
            className={`px-2 py-1 rounded text-xs font-medium ${
              diff.has_changes
                ? 'bg-yellow-500/20 text-yellow-400'
                : 'bg-green-500/20 text-green-400'
            }`}
          >
            {diff.has_changes ? 'CHANGES DETECTED' : 'NO CHANGES'}
          </span>
        </div>

        {/* Summary Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm mb-4">
          <div className="bg-gray-900 rounded p-3">
            <div className="text-gray-500 text-xs mb-1">Time Delta</div>
            <div className="text-gray-300">{formatMs(diff.time_delta_ms)}</div>
          </div>
          <div className="bg-gray-900 rounded p-3">
            <div className="text-gray-500 text-xs mb-1">Token Delta</div>
            <div
              className={
                diff.token_delta > 0
                  ? 'text-red-400'
                  : diff.token_delta < 0
                  ? 'text-green-400'
                  : 'text-gray-300'
              }
            >
              {diff.token_delta > 0 ? '+' : ''}
              {diff.token_delta.toLocaleString()}
            </div>
          </div>
          <div className="bg-gray-900 rounded p-3">
            <div className="text-gray-500 text-xs mb-1">Cost Delta</div>
            <div
              className={
                diff.cost_delta_usd > 0
                  ? 'text-red-400'
                  : diff.cost_delta_usd < 0
                  ? 'text-green-400'
                  : 'text-gray-300'
              }
            >
              {diff.cost_delta_usd > 0 ? '+' : ''}${diff.cost_delta_usd.toFixed(6)}
            </div>
          </div>
          <div className="bg-gray-900 rounded p-3">
            <div className="text-gray-500 text-xs mb-1">Freshness</div>
            <div className="text-gray-300 flex items-center gap-1">
              <span
                className={
                  diff.base_freshness_status === 'guaranteed'
                    ? 'text-green-400'
                    : 'text-yellow-400'
                }
              >
                {diff.base_freshness_status}
              </span>
              <span className="text-gray-500">-&gt;</span>
              <span
                className={
                  diff.comparison_freshness_status === 'guaranteed'
                    ? 'text-green-400'
                    : 'text-yellow-400'
                }
              >
                {diff.comparison_freshness_status}
              </span>
              {diff.freshness_improved && (
                <span className="text-green-400 ml-1" title="Improved">
                  &#x2191;
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Change Summary */}
        <div className="text-sm text-gray-400 bg-gray-900 rounded p-3">
          {diff.change_summary || 'No changes detected'}
        </div>
      </div>

      {/* Content Diff */}
      {diff.content_diff && (
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
          <h5 className="text-gray-400 text-sm font-medium mb-3">Content Changes</h5>
          <div className="grid grid-cols-4 gap-4 text-sm">
            <div className="bg-gray-900 rounded p-3 text-center">
              <div className="text-green-400 text-lg font-bold">
                +{diff.content_diff.lines_added}
              </div>
              <div className="text-gray-500 text-xs">lines added</div>
            </div>
            <div className="bg-gray-900 rounded p-3 text-center">
              <div className="text-red-400 text-lg font-bold">
                -{diff.content_diff.lines_removed}
              </div>
              <div className="text-gray-500 text-xs">lines removed</div>
            </div>
            <div className="bg-gray-900 rounded p-3 text-center">
              <div className="text-yellow-400 text-lg font-bold">
                ~{diff.content_diff.lines_changed}
              </div>
              <div className="text-gray-500 text-xs">lines changed</div>
            </div>
            <div className="bg-gray-900 rounded p-3 text-center">
              <div className="text-blue-400 text-lg font-bold">
                {(diff.content_diff.similarity_score * 100).toFixed(1)}%
              </div>
              <div className="text-gray-500 text-xs">similarity</div>
            </div>
          </div>
          {diff.content_diff.diff_summary && (
            <div className="mt-3 text-xs text-gray-500">
              {diff.content_diff.diff_summary}
            </div>
          )}
        </div>
      )}

      {/* Feature Diffs */}
      {hasFeatureChanges && (
        <div>
          <h5 className="text-gray-400 text-sm font-medium mb-2 flex items-center gap-2">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4"
              />
            </svg>
            Feature Changes
            <span className="text-xs text-gray-500">
              (+{diff.features_added} / -{diff.features_removed} / ~{diff.features_modified})
            </span>
          </h5>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            {diff.feature_diffs
              .filter((f) => f.change_type !== 'unchanged')
              .map((feature, idx) => (
                <FeatureDiffCard key={idx} diff={feature} />
              ))}
          </div>
        </div>
      )}

      {/* Retriever Diffs */}
      {hasRetrieverChanges && (
        <div>
          <h5 className="text-gray-400 text-sm font-medium mb-2 flex items-center gap-2">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
            Retriever Changes
            <span className="text-xs text-gray-500">
              (+{diff.retrievers_added} / -{diff.retrievers_removed} / ~
              {diff.retrievers_modified})
            </span>
          </h5>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            {diff.retriever_diffs
              .filter((r) => r.change_type !== 'unchanged')
              .map((retriever, idx) => (
                <RetrieverDiffCard key={idx} diff={retriever} />
              ))}
          </div>
        </div>
      )}

      {/* No Changes Message */}
      {!diff.has_changes && (
        <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-6 text-center">
          <div className="text-green-400 text-sm">
            No meaningful changes detected between these contexts.
          </div>
        </div>
      )}
    </div>
  );
}
