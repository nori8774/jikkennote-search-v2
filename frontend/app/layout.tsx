import type { Metadata } from 'next';
import './globals.css';
import Header from '@/components/Header';
import { Providers } from './providers';

export const metadata: Metadata = {
  title: '実験ノート検索システム',
  description: 'LangChainを活用した高精度な実験ノート検索システム',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ja">
      <body>
        <Providers>
          <Header />
          {children}
        </Providers>
      </body>
    </html>
  );
}
