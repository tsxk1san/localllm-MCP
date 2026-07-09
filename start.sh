#!/usr/bin/env bash
# ===== ローカルAIチャット 起動（macOS / Linux）=====
set -e

echo ""
echo " ローカルAIチャットを起動しています...（初回は数分〜十数分かかります）"
echo ""

docker compose up -d

echo ""
echo " 起動しました。ブラウザで下のアドレスを開いてください:"
echo "     http://localhost:3000"
echo ""
echo " 初回だけ：AIモデルの取り込みが必要です（README の「3. 最初の1回だけの準備」を参照）。"
echo ""

# ブラウザを自動で開く（環境により無視されます）
if command -v open >/dev/null 2>&1; then open http://localhost:3000
elif command -v xdg-open >/dev/null 2>&1; then xdg-open http://localhost:3000
fi
