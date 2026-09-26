import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'flowst8 — Proof of Flow',
  description: 'Physical desktop productivity suite bridging biometrics, telemetry, and Web3 milestones.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
