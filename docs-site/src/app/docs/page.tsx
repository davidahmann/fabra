import { getDocContent } from '@/lib/docs';
import { markdownToHtml } from '@/lib/markdown';
import { notFound } from 'next/navigation';
import { Metadata } from 'next';
import MarkdownRenderer from '@/components/MarkdownRenderer';

export const metadata: Metadata = {
  title: 'Documentation - Fabra',
  description: 'Fabra documentation - Context Infrastructure for AI Applications',
};

export default function DocsIndexPage() {
  const doc = getDocContent('index');

  if (!doc) {
    notFound();
  }

  const html = markdownToHtml(doc.content);

  return <MarkdownRenderer html={html} />;
}
