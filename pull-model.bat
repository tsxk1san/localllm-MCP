@echo off
chcp 65001 >nul
REM ===== AIモデルの取り込み（最初の1回だけ / Windows）=====
REM 既定モデル: qwen2.5:7b （数GBのダウンロードがあります）

set MODEL=%1
if "%MODEL%"=="" set MODEL=qwen2.5:7b

echo.
echo  AIモデル "%MODEL%" を取り込みます...（数GB・回線により時間がかかります）
echo.
docker compose exec ollama ollama pull %MODEL%
echo.
echo  完了しました。ブラウザ( http://localhost:3000 )でモデルに %MODEL% を選んで会話できます。
pause
