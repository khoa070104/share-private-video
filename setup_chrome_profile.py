#!/usr/bin/env python3
"""
Script tự động cấu hình Chrome profile đã đăng nhập Gmail
"""

import os
import platform
import shutil
import subprocess
from pathlib import Path

def get_system_info():
    """Lấy thông tin hệ thống"""
    system = platform.system()
    username = os.getenv('USERNAME') or os.getenv('USER')
    return system, username

def get_chrome_paths(system, username):
    """Lấy đường dẫn Chrome và User Data theo hệ điều hành"""
    if system == "Windows":
        chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        user_data = rf"C:\Users\{username}\AppData\Local\Google\Chrome\User Data"
    elif system == "Darwin":  # macOS
        chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        user_data = f"/Users/{username}/Library/Application Support/Google/Chrome"
    else:  # Linux
        chrome_path = "/usr/bin/google-chrome"
        user_data = f"/home/{username}/.config/google-chrome"
    
    return chrome_path, user_data

def check_chrome_installation(chrome_path):
    """Kiểm tra Chrome đã được cài đặt chưa"""
    if os.path.exists(chrome_path):
        print(f"✅ Chrome found at: {chrome_path}")
        return True
    else:
        print(f"❌ Chrome not found at: {chrome_path}")
        return False

def check_user_data_directory(user_data):
    """Kiểm tra thư mục User Data"""
    if os.path.exists(user_data):
        print(f"✅ Chrome User Data found at: {user_data}")
        return True
    else:
        print(f"❌ Chrome User Data not found at: {user_data}")
        return False

def create_env_file(chrome_path, user_data):
    """Tạo file .env với cấu hình Chrome profile"""
    env_content = f"""# Browser Configuration
# Đường dẫn đến Chrome executable
BROWSER_PATH="{chrome_path}"
# Đường dẫn đến Chrome user data directory (profile đã đăng nhập Gmail)
BROWSER_USER_DATA="{user_data}"
# Sử dụng browser riêng (bắt buộc để sử dụng profile đã đăng nhập)
USE_OWN_BROWSER=true
# Giữ browser mở giữa các task
KEEP_BROWSER_OPEN=true
# Chế độ headless (false để xem browser)
HEADLESS=false
# Tắt bảo mật nếu cần
DISABLE_SECURITY=false

# Window size
WINDOW_WIDTH=1280
WINDOW_HEIGHT=1100

# LLM Configuration
# Chọn provider: openai, anthropic, deepseek, google, ollama, etc.
LLM_PROVIDER=google
# API Key cho Google Gemini
GOOGLE_API_KEY=AIzaSyBHrBIrs6R_-z4U18jR2Ius5a9QZbwRFX0
# Model name cho Gemini
LLM_MODEL=gemini-2.5-flash

# Recording and Tracing
SAVE_RECORDING_PATH=./tmp/record_videos
SAVE_TRACE_PATH=./tmp/traces
SAVE_AGENT_HISTORY_PATH=./tmp/agent_history
SAVE_DOWNLOAD_PATH=./tmp/downloads

# VNC Configuration (for Docker)
VNC_PASSWORD=youvncpassword

# Optional: Skip LLM API key verification
SKIP_LLM_API_KEY_VERIFICATION=false
"""
    
    with open('.env', 'w', encoding='utf-8') as f:
        f.write(env_content)
    
    print("✅ File .env đã được tạo thành công!")
    print("🔑 Đã cấu hình Google Gemini API với model gemini-2.5-flash")

def install_dependencies():
    """Cài đặt dependencies"""
    print("\n📦 Cài đặt dependencies...")
    
    # Cài đặt Python packages
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True, capture_output=True)
        print("✅ Python packages đã được cài đặt!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Lỗi cài đặt Python packages: {e}")
        return False
    
    # Cài đặt Playwright browsers
    try:
        subprocess.run([sys.executable, "-m", "playwright", "install", "--with-deps"], 
                      check=True, capture_output=True)
        print("✅ Playwright browsers đã được cài đặt!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Lỗi cài đặt Playwright browsers: {e}")
        return False
    
    return True

def create_directories():
    """Tạo các thư mục cần thiết"""
    directories = [
        "./tmp/record_videos",
        "./tmp/traces", 
        "./tmp/agent_history",
        "./tmp/downloads"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Tạo thư mục: {directory}")

def main():
    """Hàm chính"""
    print("🚀 Bắt đầu cấu hình Chrome Profile cho Browser Use WebUI")
    print("=" * 60)
    
    # Lấy thông tin hệ thống
    system, username = get_system_info()
    print(f"💻 Hệ điều hành: {system}")
    print(f"👤 Username: {username}")
    
    # Lấy đường dẫn Chrome
    chrome_path, user_data = get_chrome_paths(system, username)
    
    # Kiểm tra Chrome installation
    if not check_chrome_installation(chrome_path):
        print("\n❌ Vui lòng cài đặt Google Chrome trước!")
        return
    
    # Kiểm tra User Data directory
    if not check_user_data_directory(user_data):
        print("\n❌ Không tìm thấy Chrome User Data!")
        print("💡 Hãy mở Chrome ít nhất một lần để tạo User Data directory")
        return
    
    # Tạo file .env
    print("\n📝 Tạo file .env...")
    create_env_file(chrome_path, user_data)
    
    # Tạo thư mục
    print("\n📁 Tạo thư mục...")
    create_directories()
    
    # Cài đặt dependencies
    if not install_dependencies():
        print("\n❌ Có lỗi trong quá trình cài đặt dependencies!")
        return
    
    print("\n" + "=" * 60)
    print("🎉 Cấu hình hoàn tất!")
    print("\n📋 Bước tiếp theo:")
    print("1. File .env đã được tạo với Google Gemini API key")
    print("2. Đóng tất cả Chrome windows")
    print("3. Chạy: python webui.py --ip 127.0.0.1 --port 7788")
    print("4. Truy cập: http://127.0.0.1:7788")
    print("\n🤖 AI Agent sẽ sử dụng Google Gemini 2.5 Flash")
    print("\n📖 Xem file SETUP_CHROME_PROFILE.md để biết thêm chi tiết")

if __name__ == "__main__":
    import sys
    main() 