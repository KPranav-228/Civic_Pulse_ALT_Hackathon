import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Newsroom | AI Summarizer',
  description: 'A focused workspace for multi-model news summarization.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-background relative overflow-x-hidden">
        <div className="bg-orb-1" />
        <div className="bg-orb-2" />
        <div className="relative z-10">{children}</div>
      </body>
    </html>
  );
}
