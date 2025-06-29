#!/usr/bin/env python3
"""
Test script để kiểm tra việc nhập email vào các loại field khác nhau
"""

import os
import sys
from dotenv import load_dotenv

# Thêm thư mục src vào path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_email_input():
    """Test nhập email vào các loại field khác nhau"""
    print("=== TEST NHẬP EMAIL VÀO CÁC LOẠI FIELD ===")
    
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
    email = "accffao011@gmail.com"
    print(f"🎥 Test với video ID: {video_id}")
    print(f"📧 Test với email: {email}")
    
    try:
        from playwright.sync_api import sync_playwright
        from agent.youtube_share_agent import find_visibility_button, find_share_button, find_and_fill_email_field, debug_page_elements
        
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
            
            # Test bước 1: Tìm nút Chế độ hiển thị
            print("\n🔍 Test bước 1: Tìm nút Chế độ hiển thị...")
            if find_visibility_button(page):
                print("✅ Bước 1 thành công!")
                page.wait_for_timeout(2000)
            else:
                print("❌ Bước 1 thất bại!")
                return False
            
            # Test bước 2: Tìm nút Chia sẻ riêng tư
            print("\n🔍 Test bước 2: Tìm nút Chia sẻ riêng tư...")
            if find_share_button(page):
                print("✅ Bước 2 thành công!")
                page.wait_for_timeout(2000)
            else:
                print("❌ Bước 2 thất bại!")
                return False
            
            # Test bước 3: Nhập email
            print("\n🔍 Test bước 3: Nhập email...")
            if find_and_fill_email_field(page, email):
                print("✅ Bước 3 thành công!")
            else:
                print("❌ Bước 3 thất bại!")
            
            input("Nhấn Enter để đóng browser...")
            browser.close()
            
            return True
            
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_email_input()
    if success:
        print("\n🎉 Test nhập email hoàn tất thành công!")
    else:
        print("\n💥 Test nhập email thất bại!") 