'use client';

import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';

export default function Header() {
  const pathname = usePathname();
  const router = useRouter();
  const { user, currentTeamId, teams, logout, switchTeam } = useAuth();

  const navItems = [
    { href: '/search', label: '検索' },
    { href: '/viewer', label: 'ビューワー' },
    { href: '/ingest', label: 'ノート管理' },
    { href: '/dictionary', label: '辞書管理' },
    { href: '/teams', label: 'チーム管理' },
    { href: '/settings', label: '設定' },
  ];

  const handleLogout = async () => {
    try {
      await logout();
      router.push('/login');
    } catch (error) {
      console.error('Logout error:', error);
    }
  };

  const handleTeamChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newTeamId = e.target.value;
    switchTeam(newTeamId);
    // チーム切り替え時、ページをリロードしてデータを再取得
    window.location.reload();
  };

  return (
    <header className="bg-primary text-white shadow-md">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <Link href="/" className="text-base font-bold hover:opacity-80 whitespace-nowrap">
            実験ノート検索システム
          </Link>

          <nav className="flex items-center space-x-4">
            {navItems.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={`text-sm whitespace-nowrap hover:opacity-80 transition-opacity ${
                  pathname === item.href ? 'border-b-2 border-white' : ''
                }`}
              >
                {item.label}
              </Link>
            ))}

            {/* チーム選択ドロップダウン（ログイン時のみ） */}
            {user && teams.length > 0 && (
              <div className="flex items-center space-x-1 whitespace-nowrap">
                <span className="text-xs">チーム:</span>
                <select
                  value={currentTeamId || ''}
                  onChange={handleTeamChange}
                  className="bg-white text-gray-900 rounded px-2 py-1 text-xs"
                >
                  {teams.map((team) => (
                    <option key={team.id} value={team.id}>
                      {team.name}
                    </option>
                  ))}
                </select>
              </div>
            )}

            {/* ユーザー情報とログアウトボタン */}
            {user ? (
              <div className="flex items-center space-x-3 whitespace-nowrap">
                <div className="flex items-center space-x-2">
                  {user.photoURL && (
                    <img
                      src={user.photoURL}
                      alt={user.displayName || 'User'}
                      className="w-6 h-6 rounded-full"
                    />
                  )}
                  <span className="text-xs max-w-[80px] truncate">{user.displayName || user.email}</span>
                </div>
                <button
                  onClick={handleLogout}
                  className="text-xs hover:opacity-80 transition-opacity border border-white px-2 py-1 rounded whitespace-nowrap"
                >
                  ログアウト
                </button>
              </div>
            ) : (
              <Link
                href="/login"
                className="text-xs hover:opacity-80 transition-opacity border border-white px-2 py-1 rounded whitespace-nowrap"
              >
                ログイン
              </Link>
            )}
          </nav>
        </div>
      </div>
    </header>
  );
}
