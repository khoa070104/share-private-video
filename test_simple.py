#!/usr/bin/env python3
"""
Test đơn giản để kiểm tra việc tìm nút Chế độ hiển thị
"""

import os
import sys
from dotenv import load_dotenv

# Thêm thư mục src vào path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_visibility_button():
    """Test tìm nút Chế độ hiển thị"""
    print("=== TEST TÌM NÚT CHẾ ĐỘ HIỂN THỊ ===")
    
    # Kiểm tra các biến môi trường
    load_dotenv()
    required_vars = ['BROWSER_USER_DATA', 'GOOGLE_API_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Thiếu các biến môi trường: {missing_vars}")
        return False
    
    print("✅ Các biến môi trường đã được cấu hình")
    
    # Test với video ID thực
    video_id = "9-hAmy3PDJk"
    print(f"🎥 Test với video ID: {video_id}")
    
    try:
        from playwright.sync_api import sync_playwright
        from agent.youtube_share_agent import find_visibility_button, debug_page_elements
        
        with sync_playwright() as p:
            browser = p.chromium.launch_persistent_context(
                user_data_dir=os.getenv("BROWSER_USER_DATA"),
                headless=False,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-web-security',
                    '--no-sandbox',
                    '--window-size=1280,800',
                ]
            )
            page = browser.new_page()
            
            # Truy cập trang edit video
            print("🌐 Truy cập trang edit video...")
            page.goto(f"https://studio.youtube.com/video/{video_id}/edit")
            page.wait_for_timeout(5000)
            
            # Chờ trang load
            page.wait_for_load_state("networkidle")
            
            # Debug thông tin trang
            debug_page_elements(page)
            
            # Test tìm nút Chế độ hiển thị
            print("\n🔍 Test tìm nút Chế độ hiển thị...")
            success = find_visibility_button(page)
            
            if success:
                print("✅ Test thành công!")
            else:
                print("❌ Test thất bại!")
            
            input("Nhấn Enter để đóng browser...")
            browser.close()
            
            return success
            
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_visibility_button()
    if success:
        print("\n🎉 Test hoàn tất thành công!")
    else:
        print("\n�� Test thất bại!") 