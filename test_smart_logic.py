#!/usr/bin/env python3
"""
Test logic thông minh kết hợp AI và logic thủ công
"""

import os
import sys
sys.path.append('src')

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from src.agent.youtube_share_agent import (
    smart_find_element, 
    find_visibility_button, 
    find_share_button, 
    find_done_button, 
    find_save_button,
    handle_popup_done,
    find_and_fill_email_field
)

# Load biến môi trường
load_dotenv()

PROFILE_PATH = os.getenv("BROWSER_USER_DATA", "")

def test_smart_logic():
    """Test logic thông minh"""
    
    if not os.path.exists(PROFILE_PATH):
        print(f"❌ Không tìm thấy profile: {PROFILE_PATH}")
        return
    
    print(f"✅ Sử dụng profile: {PROFILE_PATH}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=PROFILE_PATH,
            headless=False,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-web-security',
                '--no-sandbox',
                '--window-size=1280,800',
            ]
        )
        page = browser.new_page()
        
        # Test với video ID mẫu
        video_id = input("Nhập video ID để test: ")
        if not video_id:
            print("❌ Không có video ID")
            browser.close()
            return
        
        # Truy cập trang edit video
        print(f"🌐 Truy cập: https://studio.youtube.com/video/{video_id}/edit")
        page.goto(f"https://studio.youtube.com/video/{video_id}/edit")
        page.wait_for_timeout(5000)
        
        # Chờ trang load
        page.wait_for_load_state("networkidle")
        
        print("\n" + "="*50)
        print("🧠 TEST LOGIC THÔNG MINH")
        print("="*50)
        
        # Test 1: Tìm nút Chế độ hiển thị
        print("\n🔍 Test 1: Tìm nút Chế độ hiển thị")
        if find_visibility_button(page):
            print("✅ Test 1 PASSED")
        else:
            print("❌ Test 1 FAILED")
        
        page.wait_for_timeout(2000)
        
        # Test 2: Tìm nút Chia sẻ riêng tư
        print("\n🔍 Test 2: Tìm nút Chia sẻ riêng tư")
        if find_share_button(page):
            print("✅ Test 2 PASSED")
        else:
            print("❌ Test 2 FAILED")
        
        page.wait_for_timeout(2000)
        
        # Test 3: Nhập email
        print("\n🔍 Test 3: Nhập email")
        test_email = "test@example.com"
        if find_and_fill_email_field(page, test_email):
            print("✅ Test 3 PASSED")
        else:
            print("❌ Test 3 FAILED")
        
        page.wait_for_timeout(2000)
        
        # Test 4: Tìm nút Xong
        print("\n🔍 Test 4: Tìm nút Xong")
        if find_done_button(page):
            print("✅ Test 4 PASSED")
        else:
            print("❌ Test 4 FAILED")
        
        page.wait_for_timeout(2000)
        
        # Test 5: Xử lý popup
        print("\n🔍 Test 5: Xử lý popup")
        if handle_popup_done(page):
            print("✅ Test 5 PASSED")
        else:
            print("❌ Test 5 FAILED")
        
        page.wait_for_timeout(2000)
        
        # Test 6: Tìm nút Lưu
        print("\n🔍 Test 6: Tìm nút Lưu")
        if find_save_button(page):
            print("✅ Test 6 PASSED")
        else:
            print("❌ Test 6 FAILED")
        
        print("\n" + "="*50)
        print("🎯 TEST SMART_FIND_ELEMENT")
        print("="*50)
        
        # Test smart_find_element với các target khác nhau
        test_targets = [
            "Chế độ hiển thị",
            "Chia sẻ riêng tư", 
            "Xong",
            "Lưu",
            "Cancel",
            "Close"
        ]
        
        for target in test_targets:
            print(f"\n🔍 Test smart_find_element: {target}")
            if smart_find_element(page, target):
                print(f"✅ Smart find PASSED cho: {target}")
            else:
                print(f"❌ Smart find FAILED cho: {target}")
            page.wait_for_timeout(1000)
        
        print("\n" + "="*50)
        print("✅ HOÀN THÀNH TEST")
        print("="*50)
        
        input("Nhấn Enter để đóng browser...")
        browser.close()

if __name__ == "__main__":
    test_smart_logic() 