# Meridian Playground

Interactive playground to try Meridian Feature Store & Context Store in your browser using Pyodide (Python compiled to WebAssembly).

## Features

- **No Installation Required**: Run Python code directly in your browser
- **Interactive Examples**: Pre-built examples for Feature Store, Context Store, and RAG
- **Monaco Editor**: VS Code-like editing experience
- **Shareable Links**: Share your code via URL

## Development

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build
```

## Deployment

This playground is designed for static deployment on Vercel:

```bash
# Deploy to Vercel
vercel deploy
```

Or push to GitHub and connect to Vercel for automatic deployments.

## How It Works

1. **Pyodide**: Python interpreter compiled to WebAssembly, runs in the browser
2. **Monaco Editor**: The same editor that powers VS Code
3. **Next.js**: React framework with static export for Vercel

## Limitations

- No network access from Python code (browser sandbox)
- No file system access
- Some Python packages may not be available in Pyodide
- The examples use simulated Meridian code (not the actual library)

## Examples Included

- **Basic Feature**: Define features with `@feature` decorator
- **Context Assembly**: Token budgeting for LLM prompts
- **Retriever Pattern**: Semantic search with caching
- **Hybrid Features**: Mix Python logic and SQL queries
- **Event-Driven Features**: Real-time updates via events
