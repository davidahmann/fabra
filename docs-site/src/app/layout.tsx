import type { Metadata } from 'next';
import './globals.css';
import Sidebar from '@/components/Sidebar';
import Header from '@/components/Header';

export const metadata: Metadata = {
  title: 'Fabra - Record → Replay → Diff',
  description:
    "Fabra makes AI context durable. Every request becomes a replayable Context Record, so you can answer: what did it see, and what changed? Record → replay → diff. Turn 'the AI was wrong' into a fixable ticket.",
  keywords:
    'context record, context_id, ai debugging, incident response, llm replay, rag audit trail, prompt provenance, context diff, feature store, context lineage, mlops, pgvector, vector search',
  openGraph: {
    title: 'Fabra - Record → Replay → Diff',
    description:
      "Fabra makes AI context durable. Every request becomes a replayable Context Record, so incidents stop being vibes and screenshots.",
    url: 'https://davidahmann.github.io/fabra',
    siteName: 'Fabra',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Fabra - Record → Replay → Diff',
    description:
      "Fabra makes AI context durable. Every request becomes a replayable Context Record. Record → replay → diff.",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="antialiased">
        <Header />
        <div className="flex max-w-7xl mx-auto px-4 lg:px-8">
          <Sidebar />
          <main className="flex-1 min-w-0 py-8 lg:pl-8">
            <article className="prose prose-invert max-w-none">
              {children}
            </article>
          </main>
        </div>
      </body>
    </html>
  );
}
