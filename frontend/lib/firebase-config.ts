// Firebase Configuration
// このファイルは Firebase Console で取得した設定情報を使用します
// セットアップガイド: .steering/20251231-multitenancy/FIREBASE_SETUP_GUIDE.md

import { initializeApp } from 'firebase/app';
import { getAuth } from 'firebase/auth';

// TODO: Firebase Console から取得した firebaseConfig をここに貼り付けてください
// ステップ5（Web アプリの設定）で取得したコードを使用します
//
// 例:
// const firebaseConfig = {
//   apiKey: "AIzaSy...",
//   authDomain: "jikkennote-search.firebaseapp.com",
//   projectId: "jikkennote-search",
//   storageBucket: "jikkennote-search.appspot.com",
//   messagingSenderId: "123456789012",
//   appId: "1:123456789012:web:abcdef..."
// };

const firebaseConfig = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY || '',
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN || '',
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID || '',
  storageBucket: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET || '',
  messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID || '',
  appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID || ''
};

// Firebase 初期化
const app = initializeApp(firebaseConfig);

// Firebase Authentication
export const auth = getAuth(app);

export default app;
