import type { Metadata } from 'next';
import './globals.css';
import Sidebar from '@/components/Sidebar';
import Header from '@/components/Header';

export const metadata: Metadata = {
  title: 'Fabra - Context Infrastructure for AI Applications',
  description: 'Know what your AI knew. Fabra stores, indexes, and serves the data your AI uses and tracks exactly what was retrieved for every decision.',
  keywords: 'context infrastructure, context store, rag pipeline, llm memory, feature store, python features, mlops, pgvector, vector search',
  openGraph: {
    title: 'Fabra - Context Infrastructure for AI Applications',
    description: 'Know what your AI knew. Fabra stores, indexes, and serves the data your AI uses.',
    url: 'https://davidahmann.github.io/fabra',
    siteName: 'Fabra',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Fabra - Context Infrastructure for AI Applications',
    description: 'Know what your AI knew. Fabra stores, indexes, and serves the data your AI uses.',
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
