'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';
import Button from '@/components/Button';
import Loading from '@/components/Loading';

export default function LoginPage() {
  const { user, login, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    console.log('🔍 LoginPage useEffect:', { user: user?.email, loading });
    // すでにログイン済みの場合は検索ページにリダイレクト
    if (user && !loading) {
      console.log('✅ Redirecting to /search...');
      router.push('/search');
    }
  }, [user, loading, router]);

  const handleLogin = async () => {
    try {
      await login();
      // ログイン成功後、useEffectでリダイレクトされる
    } catch (error) {
      console.error('Login failed:', error);
      alert('ログインに失敗しました。もう一度お試しください。');
    }
  };

  if (loading) {
    return <Loading message="読み込み中..." />;
  }

  // ログイン済みの場合は何も表示しない（リダイレクト中）
  if (user) {
    return null;
  }

  return (
    <div className="min-h-screen bg-background flex items-center justify-center">
      <div className="bg-white rounded-lg shadow-lg p-8 max-w-md w-full">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold mb-2">実験ノート検索システム</h1>
          <p className="text-text-secondary">v3.0 - マルチテナント対応</p>
        </div>

        <div className="mb-8">
          <p className="text-text-secondary mb-4">
            この実験ノート検索システムを使用するには、Googleアカウントでログインしてください。
          </p>
          <ul className="text-sm text-text-secondary list-disc list-inside space-y-2">
            <li>チーム単位でノートを管理</li>
            <li>高精度な検索と比較分析</li>
            <li>正規化辞書の共有</li>
          </ul>
        </div>

        <Button
          onClick={handleLogin}
          className="w-full flex items-center justify-center space-x-2"
        >
          <svg className="w-5 h-5" viewBox="0 0 24 24">
            <path
              fill="currentColor"
              d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
            />
            <path
              fill="currentColor"
              d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
            />
            <path
              fill="currentColor"
              d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
            />
            <path
              fill="currentColor"
              d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
            />
          </svg>
          <span>Googleでログイン</span>
        </Button>

        <div className="mt-6 text-center text-sm text-text-secondary">
          <p>
            ログインすることで、
            <a href="#" className="text-primary hover:underline">
              利用規約
            </a>
            と
            <a href="#" className="text-primary hover:underline">
              プライバシーポリシー
            </a>
            に同意したものとみなされます。
          </p>
        </div>
      </div>
    </div>
  );
}
