@echo off
chcp 65001 >nul
echo ========================================
echo    Browser Use WebUI - Setup Script
echo ========================================
echo.

echo 🚀 Bắt đầu cấu hình Chrome Profile...
echo.

REM Kiểm tra Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python không được cài đặt hoặc không có trong PATH
    echo 💡 Vui lòng cài đặt Python từ https://python.org
    pause
    exit /b 1
)

echo ✅ Python đã được cài đặt

REM Chạy script setup
echo.
echo 📦 Chạy script cấu hình tự động...
python setup_chrome_profile.py

if errorlevel 1 (
    echo.
    echo ❌ Có lỗi trong quá trình cấu hình
    pause
    exit /b 1
)

echo.
echo ========================================
echo 🎉 Cấu hình hoàn tất!
echo ========================================
echo.
echo 📋 Bước tiếp theo:
echo 1. Chỉnh sửa file .env và thêm API key của bạn
echo 2. Đóng tất cả Chrome windows
echo 3. Chạy: python webui.py --ip 127.0.0.1 --port 7788
echo 4. Truy cập: http://127.0.0.1:7788
echo.
echo 📖 Xem file README_VIETNAMESE.md để biết thêm chi tiết
echo.
pause 