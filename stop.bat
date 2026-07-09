@echo off
chcp 65001 >nul
REM ===== ローカルAIチャット 停止（Windows）=====
echo  停止しています...
docker compose down
echo  停止しました。（次回は start.bat で再開できます。会話履歴やモデルは保持されます）
pause
