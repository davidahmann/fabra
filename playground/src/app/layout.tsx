import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Fabra Playground - Try Feature Store & Context Store in Browser',
  description:
    'Interactive playground to try Fabra feature store and context store. Write Python code, run it in your browser with Pyodide. No installation required.',
  keywords:
    'fabra playground, feature store demo, context store demo, python in browser, pyodide, interactive tutorial',
  openGraph: {
    title: 'Fabra Playground',
    description: 'Try Fabra Feature Store & Context Store in your browser',
    type: 'website',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>{children}</body>
    </html>
  );
}
