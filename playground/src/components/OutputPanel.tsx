'use client';

interface OutputPanelProps {
  output: string;
  error: string | null;
  duration: number | null;
  isRunning: boolean;
}

export default function OutputPanel({
  output,
  error,
  duration,
  isRunning,
}: OutputPanelProps) {
  return (
    <div className="rounded-lg border border-gray-700 bg-gray-900 overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2 bg-gray-800 border-b border-gray-700">
        <span className="text-sm font-medium text-gray-300">Output</span>
        {duration !== null && (
          <span className="text-xs text-gray-500">
            Executed in {duration.toFixed(0)}ms
          </span>
        )}
      </div>

      {/* Content */}
      <div className="p-4 min-h-[200px] max-h-[400px] overflow-auto">
        {isRunning ? (
          <div className="flex items-center gap-2 text-gray-400">
            <svg
              className="animate-spin h-4 w-4"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
            <span>Running Python...</span>
          </div>
        ) : error ? (
          <div className="text-red-400 font-mono text-sm whitespace-pre-wrap">
            <div className="flex items-center gap-2 mb-2 text-red-500">
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
                  d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              <span className="font-semibold">Error</span>
            </div>
            {error}
          </div>
        ) : output ? (
          <pre className="text-green-400 font-mono text-sm whitespace-pre-wrap">
            {output}
          </pre>
        ) : (
          <div className="text-gray-500 text-sm">
            Click &quot;Run&quot; to execute the code
          </div>
        )}
      </div>
    </div>
  );
}
