import os
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
import json
import time

# Load biến môi trường từ file .env
load_dotenv()

PROFILE_PATH = os.getenv("BROWSER_USER_DATA", "")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-2.5-flash")

def extract_share_info(prompt: str):
    """
    Sử dụng LLM để phân tích prompt và trích xuất video_id, email cần chia sẻ.
    """
    template = ChatPromptTemplate.from_messages([
        ("system", "Bạn là AI chuyên phân tích lệnh chia sẻ video YouTube riêng tư. Hãy trích xuất video_id và email từ lệnh người dùng. Trả về JSON với format: {{\"video_id\": \"...\", \"emails\": [\"...\"]}}. Nếu không đủ thông tin, trả về lỗi rõ ràng."),
        ("user", "{prompt}")
    ])
    llm = ChatGoogleGenerativeAI(model=LLM_MODEL, google_api_key=GOOGLE_API_KEY)
    chain = template | llm
    result = chain.invoke({"prompt": prompt})
    
    # Tìm JSON trong kết quả (xử lý cả markdown code block và JSON thường)
    import re, json
    
    # Lấy content từ result
    result_str = str(result.content) if hasattr(result, 'content') else str(result)
    
    # Thử tìm JSON trong markdown code block trước
    markdown_pattern = r'```(?:json)?\s*(\{[\s\S]*?\})\s*```'
    markdown_match = re.search(markdown_pattern, result_str)
    if markdown_match:
        try:
            json_str = markdown_match.group(1)
            data = json.loads(json_str)
            return data
        except Exception as e:
            pass
    
    # Nếu không tìm thấy trong markdown, thử tìm JSON thường
    json_pattern = r'\{[\s\S]*?\}'
    json_match = re.search(json_pattern, result_str)
    if json_match:
        try:
            json_str = json_match.group(0)
            data = json.loads(json_str)
            return data
        except Exception as e:
            pass
    
    raise ValueError(f"Không thể phân tích prompt: {result}")

def share_video_with_ai(prompt: str):
    info = extract_share_info(prompt)
    video_id = info.get("video_id")
    emails = info.get("emails", [])
    
    if not video_id or not emails:
        print("Không đủ thông tin video_id hoặc emails!")
        return
    
    if not os.path.exists(PROFILE_PATH):
        print(f"Không tìm thấy profile: {PROFILE_PATH}")
        return
    
    print(f"Sử dụng profile: {PROFILE_PATH}")
    print(f"Video ID: {video_id}")
    print(f"Emails: {emails}")
    
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
        
        # Truy cập trang edit video
        print("Truy cập trang edit video...")
        page.goto(f"https://studio.youtube.com/video/{video_id}/edit")
        page.wait_for_timeout(5000)

        # 1. Click vào "Chế độ hiển thị"/"Visibility"
        print("Tìm và click vào Chế độ hiển thị/Visibility...")
        visibility_selectors = [
            'text="Chế độ hiển thị"',
            'text="Visibility"',
        ]
        found = False
        for selector in visibility_selectors:
            try:
                el = page.locator(selector)
                if el.is_visible():
                    el.click()
                    found = True
                    print(f"Đã click vào: {selector}")
                    break
            except Exception as e:
                continue
        if not found:
            print("Không tìm thấy nút Chế độ hiển thị/Visibility!")
            return
        page.wait_for_timeout(2000)

        # 2. Click vào radio "Riêng tư"/"Private"
        print("Chọn Riêng tư/Private...")
        private_radio_selectors = [
            '#private-radio-button',
            'input[value="private"]',
            'label:has-text("Riêng tư")',
            'label:has-text("Private")',
        ]
        found = False
        for selector in private_radio_selectors:
            try:
                el = page.locator(selector)
                if el.is_visible():
                    el.click()
                    found = True
                    print(f"Đã click vào: {selector}")
                    break
            except Exception as e:
                continue
        if not found:
            print("Không tìm thấy radio Riêng tư/Private!")
            return
        page.wait_for_timeout(2000)

        # 3. Click vào nút Chia sẻ/Chỉnh sửa/Share/Edit
        print("Tìm và click vào nút Chia sẻ/Chỉnh sửa...")
        share_btn_selectors = [
            'ytcp-button:has-text("Chia sẻ")',
            'ytcp-button:has-text("Chia sẻ riêng tư")',
            'ytcp-button:has-text("Chỉnh sửa")',
            'ytcp-button:has-text("Edit")',
            'ytcp-button:has-text("Share")',
            'ytcp-button:has-text("Private share")',
            '.private-share-edit-button',
        ]
        found = False
        for selector in share_btn_selectors:
            try:
                el = page.locator(selector)
                if el.is_visible():
                    el.click()
                    found = True
                    print(f"Đã click vào: {selector}")
                    break
            except Exception as e:
                continue
        if not found:
            print("Không tìm thấy nút Chia sẻ/Chỉnh sửa!")
            return
        page.wait_for_timeout(2000)

        # 4. Nhập email vào ô nhập
        print("Nhập email vào ô nhập...")
        for email in emails:
            try:
                input_box = page.locator('input[type="email"], input.text-input')
                if input_box.is_visible():
                    input_box.fill(email)
                    page.wait_for_timeout(1000)
                    page.keyboard.press('Enter')
                    print(f"Đã nhập email: {email}")
            except Exception as e:
                print(f"Không nhập được email: {email}")
        page.wait_for_timeout(1000)

        # 5. Click nút Xong đầu tiên (trong dialog nhập email)
        print("Click nút Xong đầu tiên (trong dialog nhập email)...")
        done_btn_selectors = [
            'button:has-text("Xong")',
            'button:has-text("Done")',
            '#done-button',
        ]
        found = False
        for selector in done_btn_selectors:
            try:
                el = page.locator(selector)
                if el.is_visible():
                    el.click()
                    found = True
                    print(f"Đã click vào: {selector}")
                    break
            except Exception as e:
                continue
        if not found:
            print("Không tìm thấy nút Xong đầu tiên!")
        page.wait_for_timeout(2000)

        # 6. Click nút Xong thứ hai (trong dialog popup chia sẻ)
        print("Click nút Xong thứ hai (trong dialog popup chia sẻ)...")
        done_btn_selectors = [
            'button:has-text("Xong")',
            'button:has-text("Done")',
            '#save-button',
        ]
        found = False
        for selector in done_btn_selectors:
            try:
                el = page.locator(selector)
                if el.is_visible():
                    el.click()
                    found = True
                    print(f"Đã click vào: {selector}")
                    break
            except Exception as e:
                continue
        if not found:
            print("Không tìm thấy nút Xong thứ hai!")
        page.wait_for_timeout(2000)

        # 7. Click nút Lưu/Save
        print("Click nút Lưu/Save...")
        save_btn_selectors = [
            'ytcp-button#save',
            'button:has-text("Lưu")',
            'button:has-text("Save")',
        ]
        found = False
        for selector in save_btn_selectors:
            try:
                el = page.locator(selector)
                if el.is_visible():
                    el.click()
                    found = True
                    print(f"Đã click vào: {selector}")
                    break
            except Exception as e:
                continue
        if not found:
            print("Không tìm thấy nút Lưu/Save!")
        page.wait_for_timeout(3000)

        print("Đã hoàn tất thao tác chia sẻ video!")
        input("Nhấn Enter để đóng browser...")
        browser.close()

if __name__ == "__main__":
    user_prompt = input("Nhập lệnh AI (ví dụ: 'Chia sẻ video abc123 cho email test@gmail.com'): ")
    share_video_with_ai(user_prompt) 