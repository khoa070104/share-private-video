#!/usr/bin/env python3
"""
Test đặc biệt cho bước 3: Nhập email và click Xong
"""

import os
import sys
sys.path.append('src')

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from src.agent.youtube_share_agent import (
    find_and_fill_email_field,
    find_done_button,
    find_done_button_enabled
)

# Load biến môi trường
load_dotenv()

PROFILE_PATH = os.getenv("BROWSER_USER_DATA", "")

def test_step3_email():
    """Test bước 3: Nhập email và click Xong"""
    
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
        print("📧 TEST BƯỚC 3: NHẬP EMAIL VÀ CLICK XONG")
        print("="*50)
        
        # Test nhập email
        test_email = input("Nhập email để test (hoặc Enter để dùng test@example.com): ")
        if not test_email:
            test_email = "test@example.com"
        
        print(f"\n🔍 Test nhập email: {test_email}")
        
        # Test 1: Nhập email
        print("\n--- Test 1: Nhập email ---")
        if find_and_fill_email_field(page, test_email):
            print("✅ Test 1 PASSED: Nhập email thành công")
        else:
            print("❌ Test 1 FAILED: Không thể nhập email")
            input("Nhấn Enter để tiếp tục...")
        
        # Chờ UI cập nhật
        print("\n⏳ Chờ UI cập nhật...")
        page.wait_for_timeout(3000)
        
        # Test 2: Tìm nút Xong enabled
        print("\n--- Test 2: Tìm nút Xong enabled ---")
        if find_done_button_enabled(page):
            print("✅ Test 2 PASSED: Click nút Xong enabled thành công")
        else:
            print("❌ Test 2 FAILED: Không tìm thấy nút Xong enabled")
        
        # Chờ thêm
        page.wait_for_timeout(2000)
        
        # Test 3: Tìm nút Xong thông thường (có thể disabled)
        print("\n--- Test 3: Tìm nút Xong thông thường ---")
        if find_done_button(page):
            print("✅ Test 3 PASSED: Click nút Xong thành công")
        else:
            print("❌ Test 3 FAILED: Không tìm thấy nút Xong")
        
        # Test 4: Debug thông tin nút
        print("\n--- Test 4: Debug thông tin nút ---")
        result = page.evaluate("""
            () => {
                const keywords = ['xong', 'done', 'ok', 'confirm', 'apply'];
                const buttons = document.querySelectorAll('button, [role="button"], ytcp-button');
                const foundButtons = [];
                
                for (let btn of buttons) {
                    if (btn.offsetParent !== null) {
                        const text = (btn.textContent || btn.innerText || '').toLowerCase();
                        const ariaLabel = (btn.getAttribute('aria-label') || '').toLowerCase();
                        const className = (btn.getAttribute('class') || '').toLowerCase();
                        const disabled = btn.disabled;
                        
                        for (let keyword of keywords) {
                            if (text.includes(keyword) || ariaLabel.includes(keyword)) {
                                foundButtons.push({
                                    text: btn.textContent || btn.innerText || '',
                                    ariaLabel: btn.getAttribute('aria-label') || '',
                                    className: className,
                                    disabled: disabled,
                                    tagName: btn.tagName,
                                    id: btn.getAttribute('id') || ''
                                });
                                break;
                            }
                        }
                    }
                }
                
                return foundButtons;
            }
        """)
        
        if result:
            print(f"🔍 Tìm thấy {len(result)} nút Xong:")
            for i, btn in enumerate(result):
                status = "enabled" if not btn.get('disabled') else "disabled"
                print(f"   {i+1}. Text: '{btn.get('text')}' | Status: {status}")
                print(f"      Class: {btn.get('className')}")
                print(f"      Tag: {btn.get('tagName')} | ID: {btn.get('id')}")
        else:
            print("❌ Không tìm thấy nút Xong nào")
        
        print("\n" + "="*50)
        print("✅ HOÀN THÀNH TEST BƯỚC 3")
        print("="*50)
        
        input("Nhấn Enter để đóng browser...")
        browser.close()

if __name__ == "__main__":
    test_step3_email() 