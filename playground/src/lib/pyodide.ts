// Pyodide integration for running Python in the browser

declare global {
  interface Window {
    loadPyodide: (config?: { indexURL?: string }) => Promise<PyodideInterface>;
  }
}

export interface PyodideInterface {
  runPythonAsync: (code: string) => Promise<unknown>;
  loadPackage: (packages: string | string[]) => Promise<void>;
  globals: Map<string, unknown>;
}

let pyodideInstance: PyodideInterface | null = null;
let loadingPromise: Promise<PyodideInterface> | null = null;

export async function loadPyodide(): Promise<PyodideInterface> {
  // Return existing instance if already loaded
  if (pyodideInstance) {
    return pyodideInstance;
  }

  // Return existing loading promise if in progress
  if (loadingPromise) {
    return loadingPromise;
  }

  // Start loading
  loadingPromise = (async () => {
    // Load Pyodide script from CDN
    if (typeof window !== 'undefined' && !window.loadPyodide) {
      await new Promise<void>((resolve, reject) => {
        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/pyodide/v0.26.0/full/pyodide.js';
        script.onload = () => resolve();
        script.onerror = () => reject(new Error('Failed to load Pyodide'));
        document.head.appendChild(script);
      });
    }

    // Initialize Pyodide
    pyodideInstance = await window.loadPyodide({
      indexURL: 'https://cdn.jsdelivr.net/pyodide/v0.26.0/full/',
    });

    return pyodideInstance;
  })();

  return loadingPromise;
}

export interface RunResult {
  output: string;
  error: string | null;
  duration: number;
}

export async function runPython(code: string): Promise<RunResult> {
  const startTime = performance.now();
  let output = '';
  let error: string | null = null;

  try {
    const pyodide = await loadPyodide();

    // Capture stdout/stderr
    await pyodide.runPythonAsync(`
import sys
from io import StringIO

# Capture output
_stdout_buffer = StringIO()
_stderr_buffer = StringIO()
sys.stdout = _stdout_buffer
sys.stderr = _stderr_buffer
`);

    // Run the user's code
    try {
      await pyodide.runPythonAsync(code);
    } catch (e) {
      // Python runtime error
      error = String(e);
    }

    // Get captured output
    const getOutput = await pyodide.runPythonAsync(`
_stdout_buffer.getvalue() + _stderr_buffer.getvalue()
`);
    output = String(getOutput);

    // Reset stdout/stderr
    await pyodide.runPythonAsync(`
sys.stdout = sys.__stdout__
sys.stderr = sys.__stderr__
`);
  } catch (e) {
    // Pyodide loading/initialization error
    error = String(e);
  }

  const duration = performance.now() - startTime;

  return {
    output,
    error,
    duration,
  };
}

export function isPyodideLoaded(): boolean {
  return pyodideInstance !== null;
}
