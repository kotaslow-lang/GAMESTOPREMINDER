:: build.bat
:: Windows用Game Stop Reminderビルドスクリプト

@echo off
echo ===== Game Stop Reminder ビルド開始 =====

:: PyInstallerの確認
python -m PyInstaller --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] PyInstaller が見つかりません。pip install pyinstaller を実行してください。
    pause
    exit /b 1
)

:: 古いビルドフォルダの削除
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist GameStopReminder.spec del /q GameStopReminder.spec

echo [INFO] ビルドを実行しています...
:: PyInstaller実行
:: --noconfirm: 上書き確認をスキップ
:: --onedir: フォルダ形式で出力（起動が速い）
:: --windowed: コンソールウィンドウを表示しない
:: --name: 出力ファイル・フォルダ名
:: --icon: （アイコンファイルがある場合は --icon=resources/icons/icon.ico を追加）
:: --add-data: QSSや内部リソースの同梱
python -m PyInstaller ^
    --noconfirm ^
    --onedir ^
    --windowed ^
    --name "GameStopReminder" ^
    --icon "resources\icons\app_icon.ico" ^
    --add-data "style.qss;." ^
    --add-data "resources;resources" ^
    main.py

if %errorlevel% neq 0 (
    echo [ERROR] ビルドに失敗しました。
    pause
    exit /b 1
)

echo.
echo ===== ビルド完了 =====
echo dist\GameStopReminder フォルダ内に実行可能ファイルが生成されました。
pause
