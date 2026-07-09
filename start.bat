@echo off
chcp 65001 >nul
REM ===== ローカルAIチャット 起動（Windows）=====
REM このファイルをダブルクリックするだけでOKです。

echo.
echo  ローカルAIチャットを起動しています...（初回は数分〜十数分かかります）
echo.

docker compose up -d
if errorlevel 1 (
  echo.
  echo  [エラー] 起動に失敗しました。Docker Desktop が起動しているか確認してください。
  pause
  exit /b 1
)

echo.
echo  起動しました。ブラウザで下のアドレスを開きます:
echo      http://localhost:3000
echo.
echo  初回だけ：AIモデルの取り込みが必要です（README の「3. 最初の1回だけの準備」を参照）。
echo.
timeout /t 3 >nul
start http://localhost:3000
pause
