# Python 3.12ベースイメージ
FROM python:3.12-slim

# 作業ディレクトリを設定
WORKDIR /app

# システムパッケージの更新とビルドツールのインストール
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# requirements.txtをコピーして依存関係をインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードをコピー
COPY . .

# データ永続化用のディレクトリを作成（マルチテナント対応）
RUN mkdir -p /app/chroma_db /app/notes/new /app/notes/processed /app/notes/archived /app/teams /app/data

# ポート8000を公開
EXPOSE 8000

# Uvicornでサーバーを起動
CMD ["python", "server.py"]
