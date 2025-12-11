'use client';

import { useState, useCallback } from 'react';
import type { ContextDefinition, ContextResult, ContextDiff } from '@/types/api';
import { assembleContext, getContextDiff } from '@/lib/api';
import ContextResultCard from './ContextResultCard';
import JsonViewer from './JsonViewer';
import LineagePanel from './LineagePanel';
import ContextDiffPanel from './ContextDiffPanel';

interface ContextTabProps {
  contexts: ContextDefinition[];
}

interface HistoryEntry {
  id: string;
  contextName: string;
  params: Record<string, string>;
  result: ContextResult;
  timestamp: Date;
}

// Helper to build initial params from context parameters
function buildInitialParams(ctx: ContextDefinition | undefined): Record<string, string> {
  if (!ctx) return {};
  const initial: Record<string, string> = {};
  for (const param of ctx.parameters) {
    initial[param.name] = param.default || '';
  }
  return initial;
}

// Copy to clipboard helper
function CopyButton({ text, label }: { text: string; label?: string }) {
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
      className="inline-flex items-center gap-1 px-2 py-1 text-xs bg-gray-700 hover:bg-gray-600 rounded transition text-gray-300"
      title={`Copy ${label || 'text'}`}
    >
      {copied ? (
        <>
          <svg className="w-3 h-3 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
          Copied!
        </>
      ) : (
        <>
          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
          </svg>
          {label || 'Copy'}
        </>
      )}
    </button>
  );
}

export default function ContextTab({ contexts }: ContextTabProps) {
  const [selectedContext, setSelectedContext] = useState<string>(
    contexts[0]?.name || ''
  );
  const selectedContextObj = contexts.find((c) => c.name === selectedContext);
  const [params, setParams] = useState<Record<string, string>>(() =>
    buildInitialParams(selectedContextObj)
  );
  const [result, setResult] = useState<ContextResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showRawJson, setShowRawJson] = useState(false);
  const [showLineage, setShowLineage] = useState(true);

  // History tracking
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [showHistory, setShowHistory] = useState(false);

  // Diff comparison
  const [selectedForCompare, setSelectedForCompare] = useState<string | null>(null);
  const [diffResult, setDiffResult] = useState<ContextDiff | null>(null);
  const [isLoadingDiff, setIsLoadingDiff] = useState(false);
  const [showDiff, setShowDiff] = useState(false);

  const handleParamChange = (paramName: string, value: string) => {
    setParams((prev) => ({ ...prev, [paramName]: value }));
  };

  const handleAssemble = async () => {
    setIsLoading(true);
    setError(null);
    setDiffResult(null);
    setShowDiff(false);
    try {
      const contextResult = await assembleContext(selectedContext, params);
      setResult(contextResult);

      // Add to history
      const entry: HistoryEntry = {
        id: contextResult.id,
        contextName: selectedContext,
        params: { ...params },
        result: contextResult,
        timestamp: new Date(),
      };
      setHistory((prev) => [entry, ...prev.slice(0, 9)]); // Keep last 10
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to assemble context');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCompare = useCallback(async (baseId: string, comparisonId: string) => {
    setIsLoadingDiff(true);
    try {
      const diff = await getContextDiff(baseId, comparisonId);
      setDiffResult(diff);
      setShowDiff(true);
    } catch (e) {
      console.error('Failed to load diff:', e);
    } finally {
      setIsLoadingDiff(false);
    }
  }, []);

  const handleSelectForCompare = (id: string) => {
    if (selectedForCompare === id) {
      setSelectedForCompare(null);
    } else if (selectedForCompare) {
      // Compare with selected
      handleCompare(selectedForCompare, id);
      setSelectedForCompare(null);
    } else {
      setSelectedForCompare(id);
    }
  };

  if (contexts.length === 0) {
    return (
      <div className="bg-blue-500/10 border border-blue-500 rounded-lg p-6 text-blue-400">
        <div className="font-semibold mb-2">No @context functions found</div>
        <p className="text-sm text-gray-400 mb-3">
          This file doesn&apos;t define any context assemblies. To use the Context tab, add a
          <code className="mx-1 px-1.5 py-0.5 bg-gray-800 rounded text-green-400">@context</code>
          decorated function to your feature file.
        </p>
        <p className="text-xs text-gray-500">
          Try: <code className="px-1.5 py-0.5 bg-gray-800 rounded">fabra ui examples/rag_chatbot.py</code>
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h3 className="text-xl font-semibold text-gray-100">Context Assembly</h3>

      {/* Context Selector */}
      <div>
        <label className="block text-sm font-medium text-gray-400 mb-2">
          Select Context Definition
        </label>
        <select
          value={selectedContext}
          onChange={(e) => {
            const newCtx = contexts.find((c) => c.name === e.target.value);
            setSelectedContext(e.target.value);
            setParams(buildInitialParams(newCtx));
            setResult(null);
            setError(null);
            setDiffResult(null);
            setShowDiff(false);
          }}
          className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-2 text-gray-100 focus:border-green-500 focus:ring-1 focus:ring-green-500 outline-none"
        >
          {contexts.map((ctx) => (
            <option key={ctx.name} value={ctx.name}>
              {ctx.name}
            </option>
          ))}
        </select>
      </div>

      {/* Context Info */}
      {selectedContextObj && (
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
          <span className="text-green-500 font-mono font-semibold">
            {selectedContextObj.name}
          </span>
          <span className="text-gray-500 ml-2 text-sm">
            {selectedContextObj.description || 'No description'}
          </span>
        </div>
      )}

      {/* Parameter Form */}
      {selectedContextObj && selectedContextObj.parameters.length > 0 && (
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
          <div className="text-sm font-medium text-gray-400 mb-4">Inputs</div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {selectedContextObj.parameters.map((param) => (
              <div key={param.name}>
                <label className="block text-sm text-gray-400 mb-1">
                  {param.name}
                  <span className="text-gray-600 ml-1">({param.type})</span>
                </label>
                <input
                  type="text"
                  value={params[param.name] ?? ''}
                  onChange={(e) => handleParamChange(param.name, e.target.value)}
                  className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-2 text-gray-100 focus:border-green-500 focus:ring-1 focus:ring-green-500 outline-none"
                  placeholder={`Enter ${param.name}...`}
                />
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Assemble Button */}
      <div className="flex items-center gap-4">
        <button
          onClick={handleAssemble}
          disabled={isLoading}
          className={`px-6 py-3 rounded-lg font-semibold flex items-center gap-2 transition ${
            isLoading
              ? 'bg-gray-700 text-gray-400 cursor-not-allowed'
              : 'bg-green-600 hover:bg-green-500 text-white'
          }`}
        >
          {isLoading ? (
            <>
              <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                  fill="none"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                />
              </svg>
              Assembling...
            </>
          ) : (
            <>
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              Assemble Context
            </>
          )}
        </button>

        {/* History Toggle */}
        {history.length > 0 && (
          <button
            onClick={() => setShowHistory(!showHistory)}
            className="px-4 py-3 rounded-lg font-medium flex items-center gap-2 bg-gray-700 hover:bg-gray-600 text-gray-300 transition"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            History ({history.length})
          </button>
        )}
      </div>

      {/* History Panel */}
      {showHistory && history.length > 0 && (
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
          <div className="flex items-center justify-between mb-3">
            <h4 className="text-gray-200 font-medium">Recent Assemblies</h4>
            {selectedForCompare && (
              <span className="text-xs text-blue-400 bg-blue-500/20 px-2 py-1 rounded">
                Select another to compare
              </span>
            )}
          </div>
          <div className="space-y-2 max-h-[200px] overflow-y-auto">
            {history.map((entry) => (
              <div
                key={entry.id}
                className={`bg-gray-900 border rounded-lg p-3 flex items-center justify-between ${
                  selectedForCompare === entry.id
                    ? 'border-blue-500'
                    : 'border-gray-700'
                }`}
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-green-400 text-sm">{entry.contextName}</span>
                    <span className="text-xs text-gray-500">
                      {entry.timestamp.toLocaleTimeString()}
                    </span>
                  </div>
                  <div className="text-xs text-gray-500 truncate">
                    ID: {entry.id.slice(0, 12)}...
                  </div>
                </div>
                <div className="flex items-center gap-2 ml-2">
                  <CopyButton text={entry.id} label="ID" />
                  <button
                    onClick={() => handleSelectForCompare(entry.id)}
                    className={`px-2 py-1 text-xs rounded transition ${
                      selectedForCompare === entry.id
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-700 hover:bg-gray-600 text-gray-300'
                    }`}
                  >
                    {selectedForCompare === entry.id ? 'Cancel' : 'Compare'}
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="bg-red-500/10 border border-red-500 rounded-lg p-4 text-red-500">
          Assembly Failed: {error}
        </div>
      )}

      {/* Success Message */}
      {result && (
        <div className="bg-green-500/10 border border-green-500 rounded-lg p-4 flex items-center justify-between">
          <span className="text-green-500">Context assembled successfully!</span>
          <div className="flex items-center gap-2">
            <CopyButton text={result.id} label="ID" />
            <CopyButton
              text={JSON.stringify(result, null, 2)}
              label="JSON"
            />
          </div>
        </div>
      )}

      {/* Diff Panel */}
      {showDiff && diffResult && (
        <div className="bg-gray-800 border border-gray-700 rounded-lg overflow-hidden">
          <button
            onClick={() => setShowDiff(!showDiff)}
            className="w-full px-4 py-3 flex items-center justify-between text-left hover:bg-gray-700/50 transition"
          >
            <span className="text-gray-200 font-medium flex items-center gap-2">
              <svg className="w-4 h-4 text-yellow-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
              </svg>
              Context Comparison
            </span>
            <svg
              className={`w-5 h-5 text-gray-400 transform transition-transform ${
                showDiff ? 'rotate-180' : ''
              }`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          {showDiff && (
            <div className="border-t border-gray-700 p-4">
              <ContextDiffPanel diff={diffResult} />
            </div>
          )}
        </div>
      )}

      {/* Loading Diff */}
      {isLoadingDiff && (
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-6 flex items-center justify-center gap-2 text-gray-400">
          <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          Loading comparison...
        </div>
      )}

      {/* Result Card */}
      {result && (
        <>
          <ContextResultCard result={result} />

          {/* Lineage Panel */}
          {result.lineage && (
            <div className="bg-gray-800 border border-gray-700 rounded-lg overflow-hidden">
              <button
                onClick={() => setShowLineage(!showLineage)}
                className="w-full px-4 py-3 flex items-center justify-between text-left hover:bg-gray-700/50 transition"
              >
                <span className="text-gray-200 font-medium flex items-center gap-2">
                  <svg
                    className="w-4 h-4 text-green-500"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
                    />
                  </svg>
                  Lineage & Traceability
                </span>
                <svg
                  className={`w-5 h-5 text-gray-400 transform transition-transform ${
                    showLineage ? 'rotate-180' : ''
                  }`}
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M19 9l-7 7-7-7"
                  />
                </svg>
              </button>
              {showLineage && (
                <div className="border-t border-gray-700 p-4">
                  <LineagePanel lineage={result.lineage} />
                </div>
              )}
            </div>
          )}

          {/* Raw JSON Expander */}
          <div className="bg-gray-800 border border-gray-700 rounded-lg overflow-hidden">
            <button
              onClick={() => setShowRawJson(!showRawJson)}
              className="w-full px-4 py-3 flex items-center justify-between text-left hover:bg-gray-700/50 transition"
            >
              <span className="text-gray-200 font-medium">Raw JSON</span>
              <svg
                className={`w-5 h-5 text-gray-400 transform transition-transform ${
                  showRawJson ? 'rotate-180' : ''
                }`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M19 9l-7 7-7-7"
                />
              </svg>
            </button>
            {showRawJson && (
              <div className="border-t border-gray-700 p-4">
                <JsonViewer data={result} maxHeight="400px" />
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
