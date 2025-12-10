'use client';

import { useState, useEffect, useCallback } from 'react';
import dynamic from 'next/dynamic';
import { runPython, loadPyodide, isPyodideLoaded, RunResult } from '@/lib/pyodide';
import { examples, Example } from '@/lib/examples';
import OutputPanel from './OutputPanel';
import ExampleSelector from './ExampleSelector';

// Dynamically import Monaco to avoid SSR issues
const CodeEditor = dynamic(() => import('./CodeEditor'), {
  ssr: false,
  loading: () => (
    <div className="h-[400px] bg-gray-900 rounded-lg flex items-center justify-center">
      <span className="text-gray-500">Loading editor...</span>
    </div>
  ),
});

export default function Playground() {
  const [code, setCode] = useState(examples[0].code);
  const [selectedExample, setSelectedExample] = useState<Example>(examples[0]);
  const [result, setResult] = useState<RunResult | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [isPyodideReady, setIsPyodideReady] = useState(false);
  const [isLoadingPyodide, setIsLoadingPyodide] = useState(false);

  // Preload Pyodide on mount
  useEffect(() => {
    const preload = async () => {
      if (!isPyodideLoaded()) {
        setIsLoadingPyodide(true);
        try {
          await loadPyodide();
          setIsPyodideReady(true);
        } catch (e) {
          console.error('Failed to load Pyodide:', e);
        } finally {
          setIsLoadingPyodide(false);
        }
      } else {
        setIsPyodideReady(true);
      }
    };
    preload();
  }, []);

  const handleRun = useCallback(async () => {
    setIsRunning(true);
    setResult(null);

    try {
      const runResult = await runPython(code);
      setResult(runResult);
    } catch (e) {
      setResult({
        output: '',
        error: String(e),
        duration: 0,
      });
    } finally {
      setIsRunning(false);
    }
  }, [code]);

  const handleExampleSelect = (example: Example) => {
    setSelectedExample(example);
    setCode(example.code);
    setResult(null);
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
  };

  const handleShare = () => {
    // Encode code in URL for sharing
    const encoded = btoa(encodeURIComponent(code));
    const url = `${window.location.origin}${window.location.pathname}?code=${encoded}`;
    navigator.clipboard.writeText(url);
    alert('Link copied to clipboard!');
  };

  // Load code from URL on mount
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const encodedCode = params.get('code');
    if (encodedCode) {
      try {
        const decoded = decodeURIComponent(atob(encodedCode));
        setCode(decoded);
      } catch {
        // Invalid code in URL, ignore
      }
    }
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-900 to-gray-950">
      {/* Header */}
      <header className="border-b border-gray-800 bg-gray-900/80 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="text-2xl">🧭</div>
              <div>
                <h1 className="text-xl font-bold text-white">
                  Fabra Playground
                </h1>
                <p className="text-sm text-gray-400">
                  Try Context Infrastructure in your browser
                </p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              {isLoadingPyodide ? (
                <span className="text-sm text-yellow-500 flex items-center gap-2">
                  <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
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
                  Loading Python...
                </span>
              ) : isPyodideReady ? (
                <span className="text-sm text-green-500 flex items-center gap-1">
                  <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                    <path
                      fillRule="evenodd"
                      d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                      clipRule="evenodd"
                    />
                  </svg>
                  Python Ready
                </span>
              ) : null}
              <a
                href="https://davidahmann.github.io/fabra/"
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-gray-400 hover:text-white transition"
              >
                Documentation →
              </a>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Sidebar - Examples */}
          <aside className="lg:col-span-1">
            <ExampleSelector
              selectedId={selectedExample.id}
              onSelect={handleExampleSelect}
            />
          </aside>

          {/* Editor & Output */}
          <div className="lg:col-span-3 space-y-4">
            {/* Toolbar */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <button
                  onClick={handleRun}
                  disabled={isRunning || !isPyodideReady}
                  className={`px-4 py-2 rounded-lg font-medium flex items-center gap-2 transition ${
                    isRunning || !isPyodideReady
                      ? 'bg-gray-700 text-gray-400 cursor-not-allowed'
                      : 'bg-green-600 hover:bg-green-500 text-white'
                  }`}
                >
                  {isRunning ? (
                    <>
                      <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
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
                      Running...
                    </>
                  ) : (
                    <>
                      <svg
                        className="h-4 w-4"
                        fill="currentColor"
                        viewBox="0 0 20 20"
                      >
                        <path
                          fillRule="evenodd"
                          d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z"
                          clipRule="evenodd"
                        />
                      </svg>
                      Run
                    </>
                  )}
                </button>
                <span className="text-xs text-gray-500">
                  or press Ctrl/Cmd + Enter
                </span>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={handleCopy}
                  className="px-3 py-2 text-sm text-gray-400 hover:text-white transition flex items-center gap-1"
                >
                  <svg
                    className="h-4 w-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"
                    />
                  </svg>
                  Copy
                </button>
                <button
                  onClick={handleShare}
                  className="px-3 py-2 text-sm text-gray-400 hover:text-white transition flex items-center gap-1"
                >
                  <svg
                    className="h-4 w-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z"
                    />
                  </svg>
                  Share
                </button>
              </div>
            </div>

            {/* Code Editor */}
            <CodeEditor
              value={code}
              onChange={setCode}
              height="400px"
            />

            {/* Output */}
            <OutputPanel
              output={result?.output ?? ''}
              error={result?.error ?? null}
              duration={result?.duration ?? null}
              isRunning={isRunning}
            />
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-800 mt-12">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between text-sm text-gray-500">
            <div className="flex items-center gap-4">
              <span>Powered by Pyodide (Python in WebAssembly)</span>
              <span>•</span>
              <a
                href="https://github.com/davidahmann/fabra"
                target="_blank"
                rel="noopener noreferrer"
                className="hover:text-white transition"
              >
                GitHub
              </a>
            </div>
            <div>
              <span>Fabra © 2025</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
