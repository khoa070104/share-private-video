#!/usr/bin/env python3
"""
Test bước 2: Tìm nút Chỉnh sửa khi video đã chia sẻ
"""

import os
import sys
sys.path.append('src')

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from src.agent.youtube_share_agent import find_share_button

# Load biến môi trường
load_dotenv()

PROFILE_PATH = os.getenv("BROWSER_USER_DATA", "")

def test_step2_edit_button():
    """Test bước 2: Tìm nút Chỉnh sửa"""
    
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
        video_id = input("Nhập video ID đã chia sẻ để test: ")
        if not video_id:
            print("❌ Không có video ID")
            browser.close()
            return
        
        # Truy cập trang edit video
        print(f"🌐 Truy cập: https://studio.youtube.com/video/{video_id}/edit")
        page.goto(f"https://studio.youtube.com/video/{video_id}/edit")
        page.wait_for_timeout(5000)
        
        # Chờ trang load
        try:
            page.wait_for_load_state("domcontentloaded", timeout=15000)
            print("✅ Trang đã load xong")
        except Exception as e:
            print(f"⚠️ Timeout chờ trang load: {e}")
            print("Tiếp tục với trang hiện tại...")
        
        # Chờ thêm một chút để JavaScript chạy xong
        page.wait_for_timeout(3000)
        
        print("\n" + "="*50)
        print("🔍 TEST BƯỚC 2: NÚT CHỈNH SỬA")
        print("="*50)
        
        # Test tìm nút Chỉnh sửa
        print("\n--- Test: Tìm nút Chỉnh sửa ---")
        if find_share_button(page):
            print("✅ Test PASSED: Click nút Chỉnh sửa thành công")
        else:
            print("❌ Test FAILED: Không tìm thấy nút Chỉnh sửa")
        
        # Debug thông tin tất cả element có thể là nút Chỉnh sửa
        print("\n--- Debug: Tất cả element có thể là nút Chỉnh sửa ---")
        result = page.evaluate("""
            () => {
                const keywords = ['chỉnh sửa', 'edit', 'sửa', 'modify'];
                const elements = document.querySelectorAll('button, [role="button"], div, span, a, ytcp-button');
                const foundElements = [];
                
                for (let el of elements) {
                    if (el.offsetParent !== null) {
                        const text = (el.textContent || el.innerText || '').toLowerCase();
                        const ariaLabel = (el.getAttribute('aria-label') || '').toLowerCase();
                        
                        for (let keyword of keywords) {
                            if (text.includes(keyword) || ariaLabel.includes(keyword)) {
                                foundElements.push({
                                    text: el.textContent || el.innerText || '',
                                    ariaLabel: el.getAttribute('aria-label') || '',
                                    tagName: el.tagName,
                                    className: el.getAttribute('class') || '',
                                    id: el.getAttribute('id') || '',
                                    role: el.getAttribute('role') || '',
                                    onclick: el.onclick !== null,
                                    tabindex: el.getAttribute('tabindex'),
                                    rect: {
                                        left: el.getBoundingClientRect().left,
                                        top: el.getBoundingClientRect().top,
                                        width: el.getBoundingClientRect().width,
                                        height: el.getBoundingClientRect().height
                                    }
                                });
                                break;
                            }
                        }
                    }
                }
                
                return foundElements;
            }
        """)
        
        if result:
            print(f"🔍 Tìm thấy {len(result)} element có thể là nút Chỉnh sửa:")
            for i, elem in enumerate(result):
                print(f"   {i+1}. Text: '{elem.get('text', '').strip()}'")
                print(f"      Tag: {elem.get('tagName')} | Role: {elem.get('role')}")
                print(f"      Class: {elem.get('className')}")
                print(f"      ID: {elem.get('id')}")
                print(f"      OnClick: {elem.get('onclick')} | TabIndex: {elem.get('tabindex')}")
                print(f"      Position: ({elem.get('rect', {}).get('left', 0)}, {elem.get('rect', {}).get('top', 0)})")
                print(f"      Size: {elem.get('rect', {}).get('width', 0)}x{elem.get('rect', {}).get('height', 0)}")
        else:
            print("❌ Không tìm thấy element nào có thể là nút Chỉnh sửa")
        
        print("\n" + "="*50)
        print("✅ HOÀN THÀNH TEST BƯỚC 2")
        print("="*50)
        
        input("Nhấn Enter để đóng browser...")
        browser.close()

if __name__ == "__main__":
    test_step2_edit_button() 