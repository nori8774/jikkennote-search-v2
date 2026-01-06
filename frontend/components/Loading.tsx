/**
 * Loading Component
 * ローディング表示用コンポーネント
 */

interface LoadingProps {
  message?: string;
  size?: 'small' | 'medium' | 'large';
}

export default function Loading({ message = '読み込み中...', size = 'medium' }: LoadingProps) {
  const sizeClasses = {
    small: 'h-8 w-8',
    medium: 'h-12 w-12',
    large: 'h-16 w-16',
  };

  return (
    <div className="flex flex-col items-center justify-center py-8">
      <div className={`${sizeClasses[size]} animate-spin rounded-full border-4 border-gray-300 border-t-primary`} />
      {message && <p className="mt-4 text-text-secondary">{message}</p>}
    </div>
  );
}
