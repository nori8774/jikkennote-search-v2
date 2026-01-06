# 実験ノート検索システム

LangChain + ChromaDBを活用した高精度な実験ノート検索システム

## 概要

研究者がブラウザから過去の実験ノートを検索・比較できるWebアプリケーションです。

### 主要機能

- **3軸分離検索** - 材料・方法・総合の3軸で独立検索し、結果を統合
- **同義語辞書** - 表記揺れを自動正規化、クエリ展開
- **Cohereリランキング** - 検索精度の向上
- **チーム機能** - チーム単位でのデータ管理

---

## クイックスタート

### 前提条件

| ソフトウェア | バージョン |
|------------|----------|
| Node.js | 18以上 |
| Python | 3.12以上 |

### セットアップ

```bash
# 1. リポジトリのクローン
git clone https://github.com/nori8774/jikkennote-search.git
cd jikkennote-search

# 2. バックエンドのセットアップ
cd backend
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python server.py  # 起動したまま

# 3. フロントエンドのセットアップ（別ターミナル）
cd frontend
npm install
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
npm run dev
```

### 初期設定

1. http://localhost:3000 にアクセス → Googleでログイン
2. 「チーム管理」でチームを作成
3. 「設定」でOpenAI/Cohere APIキーを入力

**詳細なセットアップ手順は [SETUP_LOCAL.md](SETUP_LOCAL.md) を参照**

---

## 使い方

### ノート取り込み

1. http://localhost:3000/ingest にアクセス
2. Markdownファイル（.md）をドラッグ&ドロップ
3. 「取り込み実行」をクリック

### 検索

1. http://localhost:3000/search にアクセス
2. 目的・材料・方法を入力
3. 「検索」ボタンをクリック

詳細は [USER_MANUAL.md](USER_MANUAL.md) を参照

---

## ドキュメント

| ドキュメント | 説明 |
|------------|------|
| [SETUP_LOCAL.md](SETUP_LOCAL.md) | ローカル環境セットアップガイド |
| [USER_MANUAL.md](USER_MANUAL.md) | ユーザーマニュアル |
| [CLAUDE.md](CLAUDE.md) | 開発者向け技術情報 |
| [docs/](docs/) | 設計ドキュメント一式 |

---

## 技術スタック

**フロントエンド**: Next.js 15 | React 19 | TypeScript | Tailwind CSS

**バックエンド**: Python 3.12+ | FastAPI | LangChain + LangGraph | ChromaDB | Cohere

---

## トラブルシューティング

### バックエンドが起動しない

```bash
# 仮想環境が有効か確認
which python  # .venv/bin/python が表示されるべき
pip install -r requirements.txt
```

### フロントエンドが起動しない

```bash
rm -rf node_modules package-lock.json
npm install
```

### 検索時にAPIキーエラー

1. http://localhost:3000/settings にアクセス
2. OpenAI API Key と Cohere API Key を入力
3. 「設定を保存」をクリック

---

## ライセンス

MIT License

---

**最終更新**: 2026-01-04
