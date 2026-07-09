# unified-mcp + Ollama エージェント用イメージ
FROM python:3.12-slim

# PyMuPDF 等のビルド/実行に必要な最小ライブラリ
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 依存を先に入れてレイヤキャッシュを効かせる
COPY requirements.txt .
# CPU 版 torch を明示（sentence-transformers 用。GPU が要るなら別途調整）
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir -r requirements.txt

# アプリ本体
COPY unified_mcp_server.py ollama_agent.py ./
COPY workspace ./workspace

# 既定は Ollama 対話ホスト。docker compose run で --once も渡せる。
ENV OLLAMA_HOST=http://ollama:11434
ENV WORKSPACE_ROOT=/app/workspace
CMD ["python", "ollama_agent.py"]
