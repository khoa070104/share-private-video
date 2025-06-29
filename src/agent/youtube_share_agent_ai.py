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

def get_page_info(page):
    """
    Lấy thông tin về trang hiện tại để AI có thể phân tích
    """
    # Lấy tất cả text hiển thị trên trang
    page_text = page.evaluate("""
        () => {
            const walker = document.createTreeWalker(
                document.body,
                NodeFilter.SHOW_TEXT,
                null,
                false
            );
            const texts = [];
            let node;
            while (node = walker.nextNode()) {
                const text = node.textContent.trim();
                if (text && text.length > 0) {
                    texts.push(text);
                }
            }
            return texts.join(' | ');
        }
    """)
    
    # Lấy thông tin về các button có thể click
    buttons_info = page.evaluate("""
        () => {
            const buttons = Array.from(document.querySelectorAll('button, [role="button"], ytcp-button, input[type="button"], input[type="submit"]'));
            return buttons.map(btn => ({
                text: btn.textContent?.trim() || btn.innerText?.trim() || '',
                tagName: btn.tagName,
                className: btn.className,
                id: btn.id,
                visible: btn.offsetParent !== null
            })).filter(btn => btn.visible && btn.text.length > 0);
        }
    """)
    
    # Lấy thông tin về các input field
    inputs_info = page.evaluate("""
        () => {
            const inputs = Array.from(document.querySelectorAll('input, textarea'));
            return inputs.map(input => ({
                type: input.type,
                placeholder: input.placeholder,
                value: input.value,
                className: input.className,
                id: input.id,
                visible: input.offsetParent !== null
            })).filter(input => input.visible);
        }
    """)
    
    return {
        "page_text": page_text,
        "buttons": buttons_info,
        "inputs": inputs_info
    }

def ask_ai_for_action(page_info, current_step, emails=None):
    """
    Hỏi AI để biết cần thực hiện thao tác gì tiếp theo
    """
    template = ChatPromptTemplate.from_messages([
        ("system", """Bạn là AI chuyên điều khiển trình duyệt để chia sẻ video YouTube riêng tư. 
        
        Dựa trên thông tin UI hiện tại, hãy cho biết cần thực hiện thao tác gì tiếp theo.
        
        Các bước cần thực hiện:
        1. Tìm và click vào nút "Chế độ hiển thị" hoặc "Visibility"
        2. Chọn "Riêng tư" hoặc "Private" 
        3. Click vào nút "Chia sẻ" hoặc "Chỉnh sửa" hoặc "Share" hoặc "Edit"
        4. Nhập email vào ô input
        5. Click nút "Xong" đầu tiên (trong dialog nhập email)
        6. Click nút "Xong" thứ hai (trong dialog popup chia sẻ)
        7. Click "Lưu" hoặc "Save"
        
        Lưu ý quan trọng:
        - Có 2 nút "Xong" khác nhau: 1 nút trong dialog nhập email, 1 nút trong dialog popup chia sẻ
        - Phải click đúng nút "Xong" tương ứng với từng bước
        - Chỉ sau khi click nút "Xong" thứ hai mới được click "Lưu/Save"
        
        Trả về JSON với format:
        {{
            "action": "click_button" | "fill_input" | "wait" | "done",
            "target": "mô tả element cần tương tác",
            "value": "giá trị cần nhập (nếu là fill_input)",
            "reason": "lý do thực hiện thao tác này"
        }}
        
        Nếu không tìm thấy element phù hợp, trả về:
        {{
            "action": "error",
            "message": "mô tả lỗi"
        }}"""),
        ("user", """Thông tin UI hiện tại:
        Text trên trang: {page_text}
        
        Các button có thể click:
        {buttons}
        
        Các input field:
        {inputs}
        
        Bước hiện tại: {current_step}
        Emails cần nhập: {emails}
        
        Hãy cho biết cần thực hiện thao tác gì tiếp theo.""")
    ])
    
    llm = ChatGoogleGenerativeAI(model=LLM_MODEL, google_api_key=GOOGLE_API_KEY)
    chain = template | llm
    
    result = chain.invoke({
        "page_text": page_info["page_text"],
        "buttons": json.dumps(page_info["buttons"], indent=2),
        "inputs": json.dumps(page_info["inputs"], indent=2),
        "current_step": current_step,
        "emails": emails or []
    })
    
    # Parse JSON response
    import re
    result_str = str(result.content) if hasattr(result, 'content') else str(result)
    
    # Tìm JSON trong response
    json_match = re.search(r'\{[\s\S]*?\}', result_str)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except:
            pass
    
    return {"action": "error", "message": "Không thể parse response từ AI"}

def execute_ai_action(page, action_info):
    """
    Thực hiện thao tác dựa trên hướng dẫn của AI
    """
    action = action_info.get("action")
    target = action_info.get("target", "")
    
    if action == "click_button":
        # Tìm button dựa trên text
        try:
            # Thử tìm button bằng text (không phân biệt hoa thường)
            button = page.get_by_text(target, exact=False)
            if button.is_visible():
                button.click()
                print(f"Đã click: {target}")
                return True
            
            # Thử tìm button bằng role
            button = page.get_by_role("button", name=target)
            if button.is_visible():
                button.click()
                print(f"Đã click: {target}")
                return True
            
            # Thử tìm button bằng CSS selector nếu có
            if "button" in target.lower() or "nút" in target.lower():
                buttons = page.locator('button, [role="button"], ytcp-button')
                count = buttons.count()
                for i in range(count):
                    btn = buttons.nth(i)
                    if btn.is_visible():
                        text = btn.text_content()
                        if target.lower() in text.lower():
                            btn.click()
                            print(f"Đã click: {target}")
                            return True
                
        except Exception as e:
            print(f"Không thể click {target}: {e}")
            return False
    
    elif action == "fill_input":
        value = action_info.get("value", "")
        try:
            # Tìm input field
            input_selectors = [
                'input[type="email"]',
                'input[type="text"]', 
                'input.text-input',
                'textarea',
                'input[placeholder*="email"]',
                'input[placeholder*="Email"]'
            ]
            
            for selector in input_selectors:
                try:
                    input_field = page.locator(selector)
                    if input_field.is_visible():
                        input_field.fill(value)
                        page.keyboard.press('Enter')
                        print(f"Đã nhập: {value}")
                        return True
                except:
                    continue
                    
        except Exception as e:
            print(f"Không thể nhập {value}: {e}")
            return False
    
    elif action == "wait":
        time.sleep(2)
        print("Đang chờ...")
        return True
    
    elif action == "done":
        print("Hoàn tất!")
        return True
    
    elif action == "error":
        print(f"Lỗi: {action_info.get('message', 'Unknown error')}")
        return False
    
    return False

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
        
        # Thực hiện các bước tự động với AI
        steps = [
            "Tìm và click vào nút Chế độ hiển thị/Visibility",
            "Chọn Riêng tư/Private",
            "Click vào nút Chia sẻ/Chỉnh sửa/Share/Edit",
            "Nhập email vào ô input",
            "Click nút Xong đầu tiên (trong dialog nhập email)",
            "Click nút Xong thứ hai (trong dialog popup chia sẻ)",
            "Click Lưu/Save"
        ]
        
        for i, step in enumerate(steps):
            print(f"\n--- Bước {i+1}: {step} ---")
            
            # Lấy thông tin trang hiện tại
            page_info = get_page_info(page)
            
            # Hỏi AI cần làm gì
            action_info = ask_ai_for_action(page_info, step, emails if "email" in step.lower() else None)
            print(f"AI đề xuất: {action_info}")
            
            # Thực hiện thao tác
            success = execute_ai_action(page, action_info)
            if not success:
                print(f"Không thể thực hiện bước: {step}")
                break
            
            # Chờ một chút
            page.wait_for_timeout(2000)
        
        print("\nHoàn tất quy trình chia sẻ video!")
        input("Nhấn Enter để đóng browser...")
        browser.close()

if __name__ == "__main__":
    user_prompt = input("Nhập lệnh AI (ví dụ: 'Chia sẻ video abc123 cho email test@gmail.com'): ")
    share_video_with_ai(user_prompt) 