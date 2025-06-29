#!/usr/bin/env python3
"""
Test phân biệt 2 nút Xong khác nhau:
1. Nút Xong trong phần nhập email (bước 3)
2. Nút Xong trong popup Chế độ hiển thị (bước 4)
"""

import os
import sys
sys.path.append('src')

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from src.agent.youtube_share_agent import (
    find_done_button_email_section,
    find_done_button_popup,
    find_and_fill_email_field
)

# Load biến môi trường
load_dotenv()

PROFILE_PATH = os.getenv("BROWSER_USER_DATA", "")

def test_two_done_buttons():
    """Test phân biệt 2 nút Xong"""
    
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
        print("🔍 TEST PHÂN BIỆT 2 NÚT XONG")
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
        
        # Test 2: Tìm nút Xong trong phần email (bước 3)
        print("\n--- Test 2: Nút Xong trong phần email (bước 3) ---")
        if find_done_button_email_section(page):
            print("✅ Test 2 PASSED: Click nút Xong email thành công")
        else:
            print("❌ Test 2 FAILED: Không tìm thấy nút Xong email")
        
        # Chờ popup xuất hiện
        print("\n⏳ Chờ popup xuất hiện...")
        page.wait_for_timeout(3000)
        
        # Test 3: Tìm nút Xong trong popup (bước 4)
        print("\n--- Test 3: Nút Xong trong popup (bước 4) ---")
        if find_done_button_popup(page):
            print("✅ Test 3 PASSED: Click nút Xong popup thành công")
        else:
            print("❌ Test 3 FAILED: Không tìm thấy nút Xong popup")
        
        # Test 4: Debug thông tin tất cả nút Xong
        print("\n--- Test 4: Debug tất cả nút Xong ---")
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
                                // Kiểm tra vị trí và context
                                let context = 'unknown';
                                let emailInputNearby = false;
                                
                                // Tìm input field gần nhất
                                const emailInputs = document.querySelectorAll('input[type="email"], input[type="text"], textarea, [contenteditable="true"]');
                                for (let input of emailInputs) {
                                    if (input.offsetParent !== null) {
                                        const rect1 = btn.getBoundingClientRect();
                                        const rect2 = input.getBoundingClientRect();
                                        const distance = Math.sqrt(
                                            Math.pow(rect1.left - rect2.left, 2) + 
                                            Math.pow(rect1.top - rect2.top, 2)
                                        );
                                        
                                        if (distance < 500) {
                                            emailInputNearby = true;
                                            context = 'email_section';
                                            break;
                                        }
                                    }
                                }
                                
                                // Kiểm tra có trong popup không
                                if (!emailInputNearby) {
                                    let parent = btn.parentElement;
                                    while (parent) {
                                        const parentClass = parent.getAttribute('class') || '';
                                        const parentRole = parent.getAttribute('role') || '';
                                        
                                        if (parentClass.includes('dialog') || parentClass.includes('modal') || 
                                            parentClass.includes('popup') || parentRole === 'dialog') {
                                            context = 'popup';
                                            break;
                                        }
                                        parent = parent.parentElement;
                                    }
                                }
                                
                                foundButtons.push({
                                    text: btn.textContent || btn.innerText || '',
                                    ariaLabel: btn.getAttribute('aria-label') || '',
                                    className: className,
                                    disabled: disabled,
                                    context: context,
                                    emailInputNearby: emailInputNearby,
                                    tagName: btn.tagName,
                                    id: btn.getAttribute('id') || '',
                                    rect: {
                                        left: btn.getBoundingClientRect().left,
                                        top: btn.getBoundingClientRect().top
                                    }
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
                context = btn.get('context', 'unknown')
                nearby = "gần email" if btn.get('emailInputNearby') else "không gần email"
                print(f"   {i+1}. Text: '{btn.get('text')}' | Status: {status}")
                print(f"      Context: {context} | {nearby}")
                print(f"      Class: {btn.get('className')}")
                print(f"      Tag: {btn.get('tagName')} | ID: {btn.get('id')}")
                print(f"      Position: ({btn.get('rect', {}).get('left', 0)}, {btn.get('rect', {}).get('top', 0)})")
        else:
            print("❌ Không tìm thấy nút Xong nào")
        
        print("\n" + "="*50)
        print("✅ HOÀN THÀNH TEST PHÂN BIỆT 2 NÚT XONG")
        print("="*50)
        
        input("Nhấn Enter để đóng browser...")
        browser.close()

if __name__ == "__main__":
    test_two_done_buttons() 