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
    Hỗ trợ nhiều video_id cùng lúc.
    """
    template = ChatPromptTemplate.from_messages([
        ("system", "Bạn là AI chuyên phân tích lệnh chia sẻ video YouTube riêng tư. Hãy trích xuất video_id và email từ lệnh người dùng. Hỗ trợ nhiều video_id cùng lúc. Trả về JSON với format: {{\"video_ids\": [\"...\", \"...\"], \"emails\": [\"...\"]}}. Nếu không đủ thông tin, trả về lỗi rõ ràng."),
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
    
    # Lấy thông tin về các element có thể click (mở rộng tìm kiếm)
    clickable_elements = page.evaluate("""
        () => {
            // Tìm tất cả các element có thể click
            const selectors = [
                'button', '[role="button"]', 'ytcp-button', 
                'input[type="button"]', 'input[type="submit"]',
                'div[onclick]', 'span[onclick]', 'a[onclick]',
                'div[tabindex]', 'span[tabindex]', 'a[tabindex]',
                '[data-testid*="visibility"]', '[data-testid*="share"]',
                '[aria-label*="visibility"]', '[aria-label*="share"]',
                '.ytcp-button', '.ytcp-dropdown-trigger',
                '[class*="visibility"]', '[class*="share"]',
                '[class*="dropdown"]', '[class*="menu"]'
            ];
            
            const elements = [];
            selectors.forEach(selector => {
                try {
                    const found = document.querySelectorAll(selector);
                    found.forEach(el => {
                        if (el.offsetParent !== null) { // Chỉ lấy element visible
                            const text = el.textContent?.trim() || el.innerText?.trim() || '';
                            const ariaLabel = el.getAttribute('aria-label') || '';
                            const title = el.getAttribute('title') || '';
                            const dataTestId = el.getAttribute('data-testid') || '';
                            
                            if (text || ariaLabel || title || dataTestId) {
                                elements.push({
                                    text: text,
                                    ariaLabel: ariaLabel,
                                    title: title,
                                    dataTestId: dataTestId,
                                    tagName: el.tagName,
                                    className: el.className,
                                    id: el.id,
                                    selector: selector,
                                    visible: true
                                });
                            }
                        }
                    });
                } catch (e) {
                    // Bỏ qua selector không hợp lệ
                }
            });
            
            // Loại bỏ duplicate
            const unique = elements.filter((el, index, self) => 
                index === self.findIndex(t => 
                    t.text === el.text && t.tagName === el.tagName
                )
            );
            
            return unique;
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
        "clickable_elements": clickable_elements,
        "inputs": inputs_info
    }

def ask_ai_for_action(page_info, current_step, emails=None):
    """
    Hỏi AI để biết cần thực hiện thao tác gì tiếp theo
    """
    template = ChatPromptTemplate.from_messages([
        ("system", """Bạn là AI chuyên điều khiển trình duyệt để chia sẻ video YouTube riêng tư. 
        
        Dựa trên thông tin UI hiện tại, hãy cho biết cần thực hiện thao tác gì tiếp theo.
        
        Các bước cần thực hiện theo thứ tự:
        1. Tìm và click vào nút "Chế độ hiển thị" hoặc "Visibility" (có thể là button, div, span có thể click)
        2. Click vào nút "Chia sẻ riêng tư" hoặc "Chia sẻ" hoặc "Chỉnh sửa" (nút này xuất hiện sau khi chọn chế độ riêng tư)
        3. Nhập email vào ô input và click "Xong" hoặc "Done"
        4. Click "Xong" của popup Chế độ hiển thị
        5. Click "Lưu" hoặc "Save"
        
        Lưu ý quan trọng:
        - Element có thể click không chỉ là button mà còn có thể là div, span với onclick, tabindex, hoặc các thuộc tính khác
        - Tìm kiếm theo text, aria-label, title, data-testid, hoặc class name
        - Nếu không tìm thấy element chính xác, thử tìm element có text tương tự
        - Bước 2: Tìm nút "Chia sẻ riêng tư", "Chia sẻ", hoặc "Chỉnh sửa" (radio button Riêng tư đã được chọn sẵn)
        - Bước 3: Nhập email vào ô input và click "Xong" ngay sau đó
        - Bước 4: Click "Xong" trong popup của Chế độ hiển thị (có thể là popup/modal)
        - Đảm bảo thực hiện đúng thứ tự các bước
        
        Trả về JSON với format:
        {{
            "action": "click_button" | "fill_input" | "wait" | "done",
            "target": "mô tả element cần tương tác (có thể là text, aria-label, hoặc mô tả khác)",
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
        
        Các element có thể click:
        {clickable_elements}
        
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
        "clickable_elements": json.dumps(page_info["clickable_elements"], indent=2),
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

def execute_ai_action(page, action_info, current_step):
    """
    Thực hiện thao tác dựa trên hướng dẫn của AI
    """
    action = action_info.get("action")
    target = action_info.get("target", "")
    
    # Xử lý đặc biệt cho bước 4 (popup) - đã được xử lý ở trên
    if "popup" in current_step.lower() or "bước 4" in current_step.lower():
        print("Bước 4 đã được xử lý ở trên, bỏ qua...")
        return True
    
    if action == "click_button":
        # Tìm element để click với nhiều phương pháp khác nhau
        try:
            # Phương pháp 1: Tìm bằng text
            try:
                element = page.get_by_text(target, exact=False)
                if element.is_visible():
                    element.click()
                    print(f"Đã click (text): {target}")
                    return True
            except:
                pass
            
            # Phương pháp 2: Tìm bằng role button
            try:
                element = page.get_by_role("button", name=target)
                if element.is_visible():
                    element.click()
                    print(f"Đã click (role): {target}")
                    return True
            except:
                pass
            
            # Phương pháp 3: Tìm bằng aria-label
            try:
                element = page.locator(f'[aria-label*="{target}"]')
                if element.is_visible():
                    element.click()
                    print(f"Đã click (aria-label): {target}")
                    return True
            except:
                pass
            
            # Phương pháp 4: Tìm bằng data-testid
            try:
                element = page.locator(f'[data-testid*="{target.lower()}"]')
                if element.is_visible():
                    element.click()
                    print(f"Đã click (data-testid): {target}")
                    return True
            except:
                pass
            
            # Phương pháp 5: Tìm bằng class name chứa từ khóa
            try:
                element = page.locator(f'[class*="{target.lower()}"]')
                if element.is_visible():
                    element.click()
                    print(f"Đã click (class): {target}")
                    return True
            except:
                pass
            
            # Phương pháp 6: Tìm bằng title
            try:
                element = page.locator(f'[title*="{target}"]')
                if element.is_visible():
                    element.click()
                    print(f"Đã click (title): {target}")
                    return True
            except:
                pass
            
            # Phương pháp 7: Tìm bằng selector tổng quát
            try:
                selectors = [
                    f'button:has-text("{target}")',
                    f'[role="button"]:has-text("{target}")',
                    f'div:has-text("{target}")',
                    f'span:has-text("{target}")',
                    f'a:has-text("{target}")',
                    f'ytcp-button:has-text("{target}")'
                ]
                
                for selector in selectors:
                    try:
                        element = page.locator(selector)
                        if element.is_visible():
                            element.click()
                            print(f"Đã click (selector): {target}")
                            return True
                    except:
                        continue
            except:
                pass
            
            # Phương pháp 8: Click bằng JavaScript trực tiếp
            if click_element_by_javascript(page, target):
                return True
            
            # Phương pháp 9: Tìm element tương tự
            print(f"Thử tìm element tương tự với '{target}'...")
            if find_similar_element(page, target):
                return True
                
        except Exception as e:
            print(f"Không thể click {target}: {e}")
            return False
    
    elif action == "fill_input":
        value = action_info.get("value", "")
        try:
            # Tìm input field
            input_field = page.locator('input[type="email"], input[type="text"], textarea')
            if input_field.is_visible():
                input_field.fill(value)
                page.keyboard.press('Enter')
                print(f"Đã nhập: {value}")
                return True
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

def debug_page_elements(page):
    """
    Debug: In ra thông tin chi tiết về các element trên trang
    """
    print("\n=== DEBUG: THÔNG TIN ELEMENT TRÊN TRANG ===")
    
    # Lấy tất cả text
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
                if (text && text.length > 0 && text.length < 100) {
                    texts.push(text);
                }
            }
            return texts.slice(0, 20); // Chỉ lấy 20 text đầu tiên
        }
    """)
    print(f"Text trên trang: {page_text}")
    
    # Lấy tất cả element có thể click
    clickable = page.evaluate("""
        () => {
            const selectors = [
                'button', '[role="button"]', 'ytcp-button', 
                'div[onclick]', 'span[onclick]', 'a[onclick]',
                'div[tabindex]', 'span[tabindex]', 'a[tabindex]',
                '[data-testid*="visibility"]', '[data-testid*="share"]',
                '[aria-label*="visibility"]', '[aria-label*="share"]',
                '.ytcp-button', '.ytcp-dropdown-trigger',
                '[class*="visibility"]', '[class*="share"]',
                '[class*="dropdown"]', '[class*="menu"]'
            ];
            
            const elements = [];
            selectors.forEach(selector => {
                try {
                    const found = document.querySelectorAll(selector);
                    found.forEach(el => {
                        if (el.offsetParent !== null) {
                            const text = el.textContent?.trim() || el.innerText?.trim() || '';
                            const ariaLabel = el.getAttribute('aria-label') || '';
                            const title = el.getAttribute('title') || '';
                            const dataTestId = el.getAttribute('data-testid') || '';
                            
                            if (text || ariaLabel || title || dataTestId) {
                                elements.push({
                                    text: text,
                                    ariaLabel: ariaLabel,
                                    title: title,
                                    dataTestId: dataTestId,
                                    tagName: el.tagName,
                                    className: el.className,
                                    id: el.id,
                                    selector: selector
                                });
                            }
                        }
                    });
                } catch (e) {
                    // Bỏ qua selector không hợp lệ
                }
            });
            
            return elements.slice(0, 10); // Chỉ lấy 10 element đầu tiên
        }
    """)
    
    print(f"\nElement có thể click:")
    for i, elem in enumerate(clickable):
        print(f"  {i+1}. Text: '{elem['text']}' | Aria: '{elem['ariaLabel']}' | Title: '{elem['title']}' | Tag: {elem['tagName']} | Class: {elem['className']}")
    
    print("=== KẾT THÚC DEBUG ===\n")

def click_element_by_javascript(page, target):
    """
    Click element bằng JavaScript trực tiếp
    """
    try:
        # Thử click bằng JavaScript với nhiều selector khác nhau
        selectors = [
            f'button:contains("{target}")',
            f'[role="button"]:contains("{target}")',
            f'div:contains("{target}")',
            f'span:contains("{target}")',
            f'a:contains("{target}")',
            f'ytcp-button:contains("{target}")',
            f'[aria-label*="{target}"]',
            f'[title*="{target}"]',
            f'[data-testid*="{target.lower()}"]',
            f'[class*="{target.lower()}"]'
        ]
        
        for selector in selectors:
            try:
                # Thử click bằng JavaScript
                result = page.evaluate(f"""
                    () => {{
                        const elements = document.querySelectorAll('{selector.replace(":contains", "")}');
                        for (let el of elements) {{
                            const text = el.textContent || el.innerText || '';
                            const ariaLabel = el.getAttribute('aria-label') || '';
                            const title = el.getAttribute('title') || '';
                            
                            if (text.includes('{target}') || ariaLabel.includes('{target}') || title.includes('{target}')) {{
                                if (el.offsetParent !== null) {{
                                    el.click();
                                    return true;
                                }}
                            }}
                        }}
                        return false;
                    }}
                """)
                
                if result:
                    print(f"Đã click (JavaScript): {target}")
                    return True
            except:
                continue
        
        return False
    except Exception as e:
        print(f"Lỗi JavaScript click: {e}")
        return False

def find_similar_element(page, target):
    """
    Tìm element có text tương tự với target
    """
    try:
        # Từ khóa tương tự cho các element
        similar_keywords = {
            "Chế độ hiển thị": ["hiển thị", "visibility", "chế độ", "public", "private", "unlisted", "visibility settings"],
            "Visibility": ["hiển thị", "visibility", "chế độ", "public", "private", "unlisted", "visibility settings"],
            "Riêng tư": ["private", "riêng tư", "private", "private video"],
            "Private": ["private", "riêng tư", "private", "private video"],
            "Chia sẻ": ["share", "chia sẻ", "edit", "chỉnh sửa", "share video"],
            "Share": ["share", "chia sẻ", "edit", "chỉnh sửa", "share video"],
            "Xong": ["done", "xong", "ok", "confirm", "apply", "close"],
            "Done": ["done", "xong", "ok", "confirm", "apply", "close"],
            "Lưu": ["save", "lưu", "save changes", "publish"],
            "Save": ["save", "lưu", "save changes", "publish"]
        }
        
        keywords = similar_keywords.get(target, [target.lower()])
        
        # Tìm tất cả element có text
        elements = page.evaluate(f"""
            () => {{
                const allElements = document.querySelectorAll('button, [role="button"], div, span, a, ytcp-button, [tabindex]');
                const results = [];
                
                for (let el of allElements) {{
                    if (el.offsetParent !== null) {{
                        const text = (el.textContent || el.innerText || '').toLowerCase();
                        const ariaLabel = (el.getAttribute('aria-label') || '').toLowerCase();
                        const title = (el.getAttribute('title') || '').toLowerCase();
                        
                        for (let keyword of {keywords}) {{
                            if (text.includes(keyword) || ariaLabel.includes(keyword) || title.includes(keyword)) {{
                                results.push({{
                                    element: el,
                                    text: el.textContent || el.innerText || '',
                                    ariaLabel: el.getAttribute('aria-label') || '',
                                    tagName: el.tagName,
                                    className: el.getAttribute('class') || '',
                                    id: el.getAttribute('id') || '',
                                    tabIndex: el.getAttribute('tabindex')
                                }});
                                break;
                            }}
                        }}
                    }}
                }}
                
                return results.slice(0, 5); // Chỉ lấy 5 kết quả đầu tiên
            }}
        """)
        
        if elements:
            print(f"Tìm thấy {len(elements)} element tương tự với '{target}':")
            for i, elem in enumerate(elements):
                print(f"  {i+1}. Text: '{elem['text']}' | Aria: '{elem['ariaLabel']}' | Tag: {elem['tagName']} | TabIndex: {elem['tabIndex']}")
            
            # Thử click vào element đầu tiên
            if click_element_by_javascript(page, elements[0]['text']):
                return True
        
        return False
    except Exception as e:
        print(f"Lỗi tìm element tương tự: {e}")
        return False

def handle_popup_done(page):
    """
    Xử lý việc click "Xong" trong popup Chế độ hiển thị sử dụng logic thông minh
    """
    print("🔍 Tìm kiếm popup và nút Xong thông minh...")
    
    # Bước 1: Tìm popup/modal bằng AI
    page_info = get_page_info(page)
    
    ai_prompt = f"""
    Tìm popup/modal trên trang này và nút "Xong" hoặc "Done" trong popup đó.
    
    Thông tin trang:
    - Text: {page_info['page_text'][:500]}...
    - Clickable elements: {json.dumps(page_info['clickable_elements'][:10], indent=2)}
    
    Hãy phân tích và trả về JSON với format:
    {{
        "found_popup": true/false,
        "popup_selector": "selector của popup",
        "found_done_button": true/false,
        "done_button_selector": "selector của nút Xong trong popup",
        "reason": "lý do"
    }}
    """
    
    try:
        llm = ChatGoogleGenerativeAI(model=LLM_MODEL, google_api_key=GOOGLE_API_KEY)
        result = llm.invoke(ai_prompt)
        
        import re
        result_str = str(result.content)
        json_match = re.search(r'\{[\s\S]*?\}', result_str)
        
        if json_match:
            ai_result = json.loads(json_match.group(0))
            if ai_result.get("found_popup") and ai_result.get("found_done_button"):
                popup_selector = ai_result.get("popup_selector")
                done_selector = ai_result.get("done_button_selector")
                
                try:
                    popup = page.locator(popup_selector)
                    if popup.is_visible():
                        done_button = popup.locator(done_selector)
                        if done_button.is_visible():
                            done_button.click()
                            print(f"✅ Đã click Xong trong popup theo AI")
                            return True
                except Exception as e:
                    print(f"❌ AI popup selector thất bại: {e}")
    except Exception as e:
        print(f"❌ Lỗi AI popup: {e}")
    
    # Bước 2: Logic thủ công thông minh cho popup
    print("🔧 Thử logic thủ công thông minh cho popup...")
    
    # Tìm popup/modal bằng JavaScript thông minh
    result = page.evaluate("""
        () => {
            const popupSelectors = [
                '[role="dialog"]',
                '[class*="modal"]',
                '[class*="popup"]',
                '[class*="dialog"]',
                '.ytcp-dialog',
                '.ytcp-modal',
                'tp-yt-paper-dialog',
                '[data-testid*="dialog"]',
                '[data-testid*="modal"]',
                '[data-testid*="popup"]'
            ];
            
            for (let selector of popupSelectors) {
                try {
                    const popups = document.querySelectorAll(selector);
                    for (let popup of popups) {
                        if (popup.offsetParent !== null) {
                            // Tìm nút Xong trong popup
                            const keywords = ['xong', 'done', 'ok', 'confirm', 'apply'];
                            const buttons = popup.querySelectorAll('button, [role="button"], ytcp-button, div, span, a');
                            
                            for (let btn of buttons) {
                                if (btn.offsetParent !== null) {
                                    const text = (btn.textContent || btn.innerText || '').toLowerCase();
                                    const ariaLabel = (btn.getAttribute('aria-label') || '').toLowerCase();
                                    
                                    for (let keyword of keywords) {
                                        if (text.includes(keyword) || ariaLabel.includes(keyword)) {
                                            try {
                                                btn.click();
                                                return {
                                                    success: true,
                                                    popupSelector: selector,
                                                    buttonText: btn.textContent || btn.innerText || '',
                                                    keyword: keyword
                                                };
                                            } catch (e) {
                                                continue;
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                } catch (e) {
                    continue;
                }
            }
            
            return {success: false};
        }
    """)
    
    if result.get('success'):
        print(f"✅ Đã click Xong trong popup thông minh: '{result.get('buttonText', '')}'")
        print(f"   Popup selector: {result.get('popupSelector')}")
        print(f"   Keyword: {result.get('keyword')}")
        return True
    
    # Bước 3: Fallback - tìm nút Xong thông thường
    print("🔄 Fallback: tìm nút Xong thông thường...")
    return find_done_button(page)

def find_visibility_button(page):
    """
    Tìm và click vào nút "Chế độ hiển thị" sử dụng logic thông minh
    """
    return smart_find_element(
        page, 
        "Chế độ hiển thị hoặc Visibility", 
        "button",
        fallback_selectors=['button:has-text("Chế độ hiển thị")', 'button:has-text("Visibility")']
    )

def find_share_button(page):
    """
    Tìm và click vào nút "Chia sẻ riêng tư" hoặc "Chỉnh sửa" sử dụng logic thông minh
    """
    print("🔍 Tìm kiếm nút Chia sẻ riêng tư hoặc Chỉnh sửa...")
    
    # Bước 1: Tìm nút Chỉnh sửa trước (khi video đã chia sẻ)
    print("🔍 Tìm kiếm nút Chỉnh sửa...")
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
                                element: el,
                                text: el.textContent || el.innerText || '',
                                ariaLabel: el.getAttribute('aria-label') || '',
                                tagName: el.tagName,
                                className: el.getAttribute('class') || ''
                            });
                            break;
                        }
                    }
                }
            }
            
            // Sắp xếp theo độ ưu tiên: button > role="button" > div/span
            foundElements.sort((a, b) => {
                const aPriority = a.tagName === 'BUTTON' ? 3 : (a.element.getAttribute('role') === 'button' ? 2 : 1);
                const bPriority = b.tagName === 'BUTTON' ? 3 : (b.element.getAttribute('role') === 'button' ? 2 : 1);
                return bPriority - aPriority;
            });
            
            // Thử click element đầu tiên
            if (foundElements.length > 0) {
                const element = foundElements[0].element;
                try {
                    // Thử click thông thường trước
                    element.click();
                    return {
                        success: true,
                        text: foundElements[0].text,
                        tagName: foundElements[0].tagName,
                        className: foundElements[0].className,
                        method: 'normal_click'
                    };
                } catch (e) {
                    // Nếu không được, thử trigger event
                    try {
                        element.dispatchEvent(new MouseEvent('click', {
                            bubbles: true,
                            cancelable: true,
                            view: window
                        }));
                        return {
                            success: true,
                            text: foundElements[0].text,
                            tagName: foundElements[0].tagName,
                            className: foundElements[0].className,
                            method: 'mouse_event'
                        };
                    } catch (e2) {
                        // Cuối cùng thử focus và Enter
                        try {
                            element.focus();
                            element.dispatchEvent(new KeyboardEvent('keydown', {
                                key: 'Enter',
                                code: 'Enter',
                                keyCode: 13,
                                which: 13,
                                bubbles: true
                            }));
                            return {
                                success: true,
                                text: foundElements[0].text,
                                tagName: foundElements[0].tagName,
                                className: foundElements[0].className,
                                method: 'keyboard_event'
                            };
                        } catch (e3) {
                            console.log('Tất cả phương pháp click đều thất bại');
                        }
                    }
                }
            }
            
            return {success: false, foundElements: foundElements};
        }
    """)
    
    if result.get('success'):
        print(f"✅ Đã click nút Chỉnh sửa ({result.get('method')}): '{result.get('text', '').strip()}'")
        print(f"   Tag: {result.get('tagName')} | Class: {result.get('className')}")
        return True
    
    if result.get('foundElements'):
        print(f"❌ Tìm thấy {len(result.get('foundElements'))} nút Chỉnh sửa nhưng không thể click:")
        for elem in result.get('foundElements')[:3]:
            print(f"   - '{elem.get('text', '').strip()}' | Tag: {elem.get('tagName')}")
    
    # Bước 2: Nếu không tìm thấy nút Chỉnh sửa, tìm nút Chia sẻ riêng tư
    print("🔍 Không tìm thấy nút Chỉnh sửa, tìm nút Chia sẻ riêng tư...")
    return smart_find_element(
        page, 
        "Chia sẻ riêng tư hoặc Chia sẻ", 
        "button",
        fallback_selectors=['button:has-text("Chia sẻ riêng tư")', 'button:has-text("Chia sẻ")']
    )

def find_done_button(page):
    """
    Tìm và click vào nút "Xong" sử dụng logic thông minh
    """
    return smart_find_element(
        page, 
        "Xong hoặc Done", 
        "button",
        fallback_selectors=['#done-button', 'button:has-text("Xong")', 'button:has-text("Done")']
    )

def find_done_button_enabled(page):
    """
    Tìm và click vào nút "Xong" enabled (không bị disabled)
    """
    print("🔍 Tìm kiếm nút Xong enabled...")
    
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
                    
                    // Kiểm tra có phải nút Xong không
                    for (let keyword of keywords) {
                        if (text.includes(keyword) || ariaLabel.includes(keyword)) {
                            foundButtons.push({
                                element: btn,
                                text: btn.textContent || btn.innerText || '',
                                ariaLabel: btn.getAttribute('aria-label') || '',
                                className: className,
                                disabled: disabled,
                                score: 0
                            });
                            break;
                        }
                    }
                }
            }
            
            // Sắp xếp: enabled trước, disabled sau
            foundButtons.sort((a, b) => {
                if (a.disabled !== b.disabled) {
                    return a.disabled ? 1 : -1; // enabled trước
                }
                return b.score - a.score;
            });
            
            // Thử click nút enabled đầu tiên
            for (let btn of foundButtons) {
                if (!btn.disabled && !btn.className.includes('disabled')) {
                    try {
                        btn.element.click();
                        return {
                            success: true,
                            text: btn.text,
                            enabled: true,
                            className: btn.className
                        };
                    } catch (e) {
                        continue;
                    }
                }
            }
            
            // Nếu không có nút enabled, thử click nút disabled đầu tiên
            if (foundButtons.length > 0) {
                try {
                    foundButtons[0].element.click();
                    return {
                        success: true,
                        text: foundButtons[0].text,
                        enabled: false,
                        className: foundButtons[0].className
                    };
                } catch (e) {
                    return {success: false, error: e.toString()};
                }
            }
            
            return {success: false, foundButtons: foundButtons};
        }
    """)
    
    if result.get('success'):
        enabled_status = "enabled" if result.get('enabled') else "disabled"
        print(f"✅ Đã click nút Xong ({enabled_status}): '{result.get('text', '')}'")
        print(f"   Class: {result.get('className')}")
        return True
    
    if result.get('foundButtons'):
        print(f"❌ Tìm thấy {len(result.get('foundButtons'))} nút Xong nhưng không thể click:")
        for btn in result.get('foundButtons')[:3]:  # Chỉ hiển thị 3 nút đầu
            status = "enabled" if not btn.get('disabled') else "disabled"
            print(f"   - '{btn.get('text')}' ({status})")
    
    print("❌ Không tìm thấy nút Xong enabled")
    return False

def find_save_button(page):
    """
    Tìm và click vào nút "Lưu" sử dụng logic thông minh
    """
    return smart_find_element(
        page, 
        "Lưu hoặc Save", 
        "button",
        fallback_selectors=['button:has-text("Lưu")', 'button:has-text("Save")', '#save-button']
    )

def smart_find_element(page, target_description, element_type="button", fallback_selectors=None):
    """
    Tìm element thông minh bằng cách kết hợp AI và logic thủ công
    """
    print(f"🧠 Tìm kiếm thông minh: {target_description}")
    
    # Bước 1: Hỏi AI để phân tích trang và tìm element
    page_info = get_page_info(page)
    
    # Tạo prompt cho AI để tìm element cụ thể
    ai_prompt = f"""
    Tìm element "{target_description}" trên trang này.
    
    Thông tin trang:
    - Text: {page_info['page_text'][:500]}...
    - Clickable elements: {json.dumps(page_info['clickable_elements'][:10], indent=2)}
    
    Hãy phân tích và trả về JSON với format:
    {{
        "found": true/false,
        "element_info": {{
            "text": "text của element",
            "aria_label": "aria-label",
            "tag_name": "tag name",
            "class_name": "class name",
            "id": "id",
            "selector": "selector để tìm element này"
        }},
        "reason": "lý do chọn element này"
    }}
    
    Nếu không tìm thấy, trả về:
    {{
        "found": false,
        "reason": "lý do không tìm thấy"
    }}
    """
    
    try:
        # Hỏi AI
        llm = ChatGoogleGenerativeAI(model=LLM_MODEL, google_api_key=GOOGLE_API_KEY)
        result = llm.invoke(ai_prompt)
        
        # Parse kết quả AI
        import re
        result_str = str(result.content)
        json_match = re.search(r'\{[\s\S]*?\}', result_str)
        
        if json_match:
            ai_result = json.loads(json_match.group(0))
            if ai_result.get("found"):
                element_info = ai_result.get("element_info", {})
                selector = element_info.get("selector")
                
                if selector:
                    print(f"🤖 AI đề xuất selector: {selector}")
                    try:
                        element = page.locator(selector)
                        if element.is_visible():
                            element.click()
                            print(f"✅ Đã click element theo AI: {element_info.get('text', '')}")
                            return True
                    except Exception as e:
                        print(f"❌ AI selector thất bại: {e}")
        
        print("🤖 AI không tìm thấy element phù hợp")
        
    except Exception as e:
        print(f"❌ Lỗi AI: {e}")
    
    # Bước 2: Logic thủ công thông minh (không fix cứng)
    print("🔧 Thử logic thủ công thông minh...")
    
    # Tạo từ khóa tìm kiếm dựa trên mô tả
    keywords = []
    if "xong" in target_description.lower() or "done" in target_description.lower():
        keywords = ["xong", "done", "ok", "confirm", "apply", "save", "submit"]
    elif "chia sẻ" in target_description.lower() or "share" in target_description.lower():
        keywords = ["chia sẻ", "share", "edit", "chỉnh sửa", "private", "riêng tư"]
    elif "hiển thị" in target_description.lower() or "visibility" in target_description.lower():
        keywords = ["hiển thị", "visibility", "chế độ", "public", "private", "unlisted"]
    elif "lưu" in target_description.lower() or "save" in target_description.lower():
        keywords = ["lưu", "save", "publish", "update"]
    else:
        # Tách từ khóa từ mô tả
        keywords = target_description.lower().split()
    
    # Tìm element bằng JavaScript thông minh
    result = page.evaluate(f"""
        () => {{
            const keywords = {keywords};
            const elementTypes = ['button', 'ytcp-button', '[role="button"]', 'div', 'span', 'a'];
            const foundElements = [];
            
            for (let tag of elementTypes) {{
                const elements = document.querySelectorAll(tag);
                for (let el of elements) {{
                    if (el.offsetParent !== null) {{
                        const text = (el.textContent || el.innerText || '').toLowerCase();
                        const ariaLabel = (el.getAttribute('aria-label') || '').toLowerCase();
                        const title = (el.getAttribute('title') || '').toLowerCase();
                        const className = (el.getAttribute('class') || '').toLowerCase();
                        const id = (el.getAttribute('id') || '').toLowerCase();
                        
                        // Tính điểm phù hợp
                        let score = 0;
                        for (let keyword of keywords) {{
                            if (text.includes(keyword)) score += 3;
                            if (ariaLabel.includes(keyword)) score += 2;
                            if (title.includes(keyword)) score += 2;
                            if (className.includes(keyword)) score += 1;
                            if (id.includes(keyword)) score += 1;
                        }}
                        
                        if (score > 0) {{
                            foundElements.push({{
                                element: el,
                                text: el.textContent || el.innerText || '',
                                ariaLabel: el.getAttribute('aria-label') || '',
                                tagName: el.tagName,
                                className: el.getAttribute('class') || '',
                                id: el.getAttribute('id') || '',
                                score: score
                            }});
                        }}
                    }}
                }}
            }}
            
            // Sắp xếp theo điểm số
            foundElements.sort((a, b) => b.score - a.score);
            
            // Thử click element có điểm cao nhất
            if (foundElements.length > 0) {{
                const bestElement = foundElements[0];
                try {{
                    const element = bestElement.element;
                    
                    // Thử nhiều cách click khác nhau
                    if (element.tagName === 'BUTTON' || element.getAttribute('role') === 'button') {{
                        element.click();
                    }} else {{
                        // Với DIV/SPAN, thử trigger click event
                        element.dispatchEvent(new MouseEvent('click', {{
                            bubbles: true,
                            cancelable: true,
                            view: window
                        }}));
                        
                        // Nếu không được, thử focus và nhấn Enter
                        if (!element.onclick) {{
                            element.focus();
                            element.dispatchEvent(new KeyboardEvent('keydown', {{
                                key: 'Enter',
                                code: 'Enter',
                                keyCode: 13,
                                which: 13,
                                bubbles: true
                            }}));
                        }}
                    }}
                    
                    return {{
                        success: true,
                        text: bestElement.text,
                        tagName: bestElement.tagName,
                        className: bestElement.className,
                        isClickable: bestElement.isClickable,
                        type: 'edit'
                    }};
                }} catch (e) {{
                    console.log('Không thể click element:', e);
                    
                    // Thử click bằng JavaScript trực tiếp
                    try {{
                        bestElement.element.dispatchEvent(new Event('click', {{ bubbles: true }}));
                        return {{
                            success: true,
                            text: bestElement.text,
                            tagName: bestElement.tagName,
                            className: bestElement.className,
                            isClickable: bestElement.isClickable,
                            type: 'edit',
                            method: 'javascript_event'
                        }};
                    }} catch (e2) {{
                        console.log('JavaScript event cũng thất bại:', e2);
                    }}
                }}
            }}
            
            return {{success: false, foundElements: foundElements.slice(0, 5)}};
        }}
    """)
    
    if result.get('success'):
        print(f"✅ Đã click element thông minh: '{result.get('text', '')}'")
        print(f"   Điểm số: {result.get('score')}")
        print(f"   Tag: {result.get('tagName')}")
        print(f"   Class: {result.get('className')}")
        return True
    
    # Bước 3: Fallback với selectors cơ bản (nếu có)
    if fallback_selectors:
        print("🔄 Thử fallback selectors...")
        for selector in fallback_selectors:
            try:
                element = page.locator(selector)
                if element.is_visible():
                    element.click()
                    print(f"✅ Đã click với fallback selector: {selector}")
                    return True
            except:
                continue
    
    print(f"❌ Không tìm thấy element: {target_description}")
    return False

def find_and_fill_email_field(page, email):
    """
    Tìm và nhập email vào field sử dụng logic thông minh
    """
    print(f"🔍 Tìm kiếm email field thông minh cho: {email}")
    
    # Bước 1: Hỏi AI để tìm input field
    page_info = get_page_info(page)
    
    ai_prompt = f"""
    Tìm input field để nhập email trên trang này.
    
    Thông tin trang:
    - Text: {page_info['page_text'][:500]}...
    - Input fields: {json.dumps(page_info['inputs'], indent=2)}
    
    Hãy phân tích và trả về JSON với format:
    {{
        "found": true/false,
        "input_info": {{
            "selector": "selector của input field",
            "type": "input type",
            "placeholder": "placeholder text",
            "reason": "lý do chọn field này"
        }}
    }}
    """
    
    try:
        llm = ChatGoogleGenerativeAI(model=LLM_MODEL, google_api_key=GOOGLE_API_KEY)
        result = llm.invoke(ai_prompt)
        
        import re
        result_str = str(result.content)
        json_match = re.search(r'\{[\s\S]*?\}', result_str)
        
        if json_match:
            ai_result = json.loads(json_match.group(0))
            if ai_result.get("found"):
                input_info = ai_result.get("input_info", {})
                selector = input_info.get("selector")
                
                if selector:
                    print(f"🤖 AI đề xuất input selector: {selector}")
                    try:
                        input_field = page.locator(selector)
                        if input_field.is_visible():
                            input_field.fill(email)
                            print(f"✅ Đã nhập email theo AI: {email}")
                            return True
                    except Exception as e:
                        print(f"❌ AI input selector thất bại: {e}")
    except Exception as e:
        print(f"❌ Lỗi AI input: {e}")
    
    # Bước 2: Logic thủ công thông minh
    print("🔧 Thử logic thủ công thông minh cho input...")
    
    result = page.evaluate(f"""
        () => {{
            const email = '{email}';
            const inputSelectors = [
                'input[type="email"]',
                'input[type="text"]',
                'input[placeholder*="email"]',
                'input[placeholder*="Email"]',
                'input[aria-label*="email"]',
                'input[aria-label*="Email"]',
                'textarea',
                '[contenteditable="true"]',
                '[role="textbox"]',
                '[data-testid*="email"]',
                '[data-testid*="input"]',
                'ytcp-text-input',
                'ytcp-input',
                'form input',
                '.email-input',
                '.input-field',
                'input',
                'textarea'
            ];
            
            for (let selector of inputSelectors) {{
                try {{
                    const elements = document.querySelectorAll(selector);
                    for (let el of elements) {{
                        if (el.offsetParent !== null) {{
                            // Kiểm tra xem element có phải là input field không
                            const tagName = el.tagName.toLowerCase();
                            const type = el.getAttribute('type') || '';
                            const placeholder = el.getAttribute('placeholder') || '';
                            const ariaLabel = el.getAttribute('aria-label') || '';
                            const contentEditable = el.getAttribute('contenteditable');
                            const role = el.getAttribute('role');
                            
                            // Tính điểm phù hợp
                            let score = 0;
                            if (tagName === 'input' || tagName === 'textarea') score += 2;
                            if (type === 'email') score += 3;
                            if (type === 'text') score += 1;
                            if (placeholder.toLowerCase().includes('email')) score += 2;
                            if (ariaLabel.toLowerCase().includes('email')) score += 2;
                            if (contentEditable === 'true') score += 1;
                            if (role === 'textbox') score += 1;
                            
                            if (score > 0) {{
                                try {{
                                    // Focus vào element
                                    el.focus();
                                    
                                    // Clear nội dung cũ
                                    el.value = '';
                                    el.textContent = '';
                                    
                                    // Nhập email
                                    if (tagName === 'input' || tagName === 'textarea') {{
                                        el.value = email;
                                    }} else {{
                                        el.textContent = email;
                                    }}
                                    
                                    // Trigger events
                                    el.dispatchEvent(new Event('input', {{ bubbles: true }}));
                                    el.dispatchEvent(new Event('change', {{ bubbles: true }}));
                                    
                                    return {{
                                        success: true,
                                        selector: selector,
                                        tagName: tagName,
                                        score: score,
                                        type: type,
                                        placeholder: placeholder
                                    }};
                                }} catch (e) {{
                                    continue;
                                }}
                            }}
                        }}
                    }}
                }} catch (e) {{
                    continue;
                }}
            }}
            
            return {{success: false}};
        }}
    """)
    
    if result.get('success'):
        print(f"✅ Đã nhập email thông minh: {email}")
        print(f"   Selector: {result.get('selector')}")
        print(f"   TagName: {result.get('tagName')}")
        print(f"   Score: {result.get('score')}")
        print(f"   Type: {result.get('type')}")
        print(f"   Placeholder: {result.get('placeholder')}")
        return True
    
    print("❌ Không thể tìm thấy email field thông minh")
    return False

def find_done_button_email_section(page):
    """
    Tìm và click vào nút "Xong" trong phần nhập email (bước 3)
    """
    print("🔍 Tìm kiếm nút Xong trong phần nhập email...")
    
    # Tìm nút Xong trong context của email input
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
                    
                    // Kiểm tra có phải nút Xong không
                    for (let keyword of keywords) {
                        if (text.includes(keyword) || ariaLabel.includes(keyword)) {
                            // Kiểm tra xem nút này có liên quan đến email input không
                            // Tìm input field gần nhất
                            let emailInputNearby = false;
                            const emailInputs = document.querySelectorAll('input[type="email"], input[type="text"], textarea, [contenteditable="true"]');
                            
                            for (let input of emailInputs) {
                                if (input.offsetParent !== null) {
                                    const rect1 = btn.getBoundingClientRect();
                                    const rect2 = input.getBoundingClientRect();
                                    
                                    // Kiểm tra khoảng cách giữa button và input
                                    const distance = Math.sqrt(
                                        Math.pow(rect1.left - rect2.left, 2) + 
                                        Math.pow(rect1.top - rect2.top, 2)
                                    );
                                    
                                    if (distance < 500) { // Trong phạm vi 500px
                                        emailInputNearby = true;
                                        break;
                                    }
                                }
                            }
                            
                            foundButtons.push({
                                element: btn,
                                text: btn.textContent || btn.innerText || '',
                                ariaLabel: btn.getAttribute('aria-label') || '',
                                className: className,
                                disabled: disabled,
                                emailInputNearby: emailInputNearby,
                                distance: emailInputNearby ? 0 : 1000 // Ưu tiên nút gần email input
                            });
                            break;
                        }
                    }
                }
            }
            
            // Sắp xếp: nút gần email input trước, enabled trước
            foundButtons.sort((a, b) => {
                if (a.emailInputNearby !== b.emailInputNearby) {
                    return a.emailInputNearby ? -1 : 1;
                }
                if (a.disabled !== b.disabled) {
                    return a.disabled ? 1 : -1;
                }
                return a.distance - b.distance;
            });
            
            // Thử click nút đầu tiên (ưu tiên nhất)
            if (foundButtons.length > 0) {
                try {
                    foundButtons[0].element.click();
                    return {
                        success: true,
                        text: foundButtons[0].text,
                        emailInputNearby: foundButtons[0].emailInputNearby,
                        enabled: !foundButtons[0].disabled,
                        className: foundButtons[0].className
                    };
                } catch (e) {
                    return {success: false, error: e.toString()};
                }
            }
            
            return {success: false, foundButtons: foundButtons};
        }
    """)
    
    if result.get('success'):
        nearby_status = "gần email input" if result.get('emailInputNearby') else "không gần email input"
        enabled_status = "enabled" if result.get('enabled') else "disabled"
        print(f"✅ Đã click nút Xong email ({nearby_status}, {enabled_status}): '{result.get('text', '')}'")
        print(f"   Class: {result.get('className')}")
        return True
    
    if result.get('foundButtons'):
        print(f"❌ Tìm thấy {len(result.get('foundButtons'))} nút Xong nhưng không thể click:")
        for btn in result.get('foundButtons')[:3]:
            nearby = "gần email" if btn.get('emailInputNearby') else "không gần email"
            status = "enabled" if not btn.get('disabled') else "disabled"
            print(f"   - '{btn.get('text')}' ({nearby}, {status})")
    
    print("❌ Không tìm thấy nút Xong trong phần email")
    return False

def find_done_button_popup(page):
    """
    Tìm và click vào nút "Xong" trong popup Chế độ hiển thị (bước 4)
    """
    print("🔍 Tìm kiếm nút Xong trong popup Chế độ hiển thị...")
    
    # Tìm popup/modal trước
    result = page.evaluate("""
        () => {
            const popupSelectors = [
                '[role="dialog"]',
                '[class*="modal"]',
                '[class*="popup"]',
                '[class*="dialog"]',
                '.ytcp-dialog',
                '.ytcp-modal',
                'tp-yt-paper-dialog',
                '[data-testid*="dialog"]',
                '[data-testid*="modal"]',
                '[data-testid*="popup"]'
            ];
            
            for (let selector of popupSelectors) {
                try {
                    const popups = document.querySelectorAll(selector);
                    for (let popup of popups) {
                        if (popup.offsetParent !== null) {
                            // Tìm nút Xong trong popup
                            const keywords = ['xong', 'done', 'ok', 'confirm', 'apply'];
                            const buttons = popup.querySelectorAll('button, [role="button"], ytcp-button, div, span, a');
                            
                            for (let btn of buttons) {
                                if (btn.offsetParent !== null) {
                                    const text = (btn.textContent || btn.innerText || '').toLowerCase();
                                    const ariaLabel = (btn.getAttribute('aria-label') || '').toLowerCase();
                                    
                                    for (let keyword of keywords) {
                                        if (text.includes(keyword) || ariaLabel.includes(keyword)) {
                                            try {
                                                btn.click();
                                                return {
                                                    success: true,
                                                    popupSelector: selector,
                                                    buttonText: btn.textContent || btn.innerText || '',
                                                    keyword: keyword
                                                };
                                            } catch (e) {
                                                continue;
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                } catch (e) {
                    continue;
                }
            }
            
            return {success: false};
        }
    """)
    
    if result.get('success'):
        print(f"✅ Đã click nút Xong trong popup: '{result.get('buttonText', '')}'")
        print(f"   Popup selector: {result.get('popupSelector')}")
        print(f"   Keyword: {result.get('keyword')}")
        return True
    
    # Nếu không tìm thấy popup, thử tìm nút Xong thông thường (có thể là popup ẩn)
    print("🔍 Không tìm thấy popup, thử tìm nút Xong thông thường...")
    return find_done_button(page)

def share_video_with_ai(prompt: str):
    info = extract_share_info(prompt)
    video_ids = info.get("video_ids", [])
    emails = info.get("emails", [])
    
    # Hỗ trợ cả video_id cũ và video_ids mới
    if not video_ids and info.get("video_id"):
        video_ids = [info.get("video_id")]
    
    if not video_ids or not emails:
        print("Không đủ thông tin video_ids hoặc emails!")
        return
    
    if not os.path.exists(PROFILE_PATH):
        print(f"Không tìm thấy profile: {PROFILE_PATH}")
        return
    
    print(f"Sử dụng profile: {PROFILE_PATH}")
    print(f"Video IDs: {video_ids}")
    print(f"Emails: {emails}")
    
    # Xử lý từng video ID
    for i, video_id in enumerate(video_ids):
        print(f"\n{'='*60}")
        print(f"🎬 XỬ LÝ VIDEO {i+1}/{len(video_ids)}: {video_id}")
        print(f"{'='*60}")
        
        try:
            share_single_video(video_id, emails)
            print(f"✅ Hoàn thành video {i+1}: {video_id}")
        except Exception as e:
            print(f"❌ Lỗi xử lý video {i+1}: {video_id} - {e}")
            continue
        
        # Chờ một chút giữa các video
        if i < len(video_ids) - 1:
            print("⏳ Chờ 3 giây trước khi xử lý video tiếp theo...")
            import time
            time.sleep(3)
    
    print(f"\n🎉 HOÀN THÀNH XỬ LÝ {len(video_ids)} VIDEO!")

def share_single_video(video_id: str, emails: list):
    """
    Xử lý chia sẻ một video cụ thể
    """
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
        
        # Kiểm tra xem có phải đang ở trang edit không
        current_url = page.url
        print(f"URL hiện tại: {current_url}")
        
        # Nếu không phải trang edit, thử điều hướng lại
        if "/edit" not in current_url:
            print("Không phải trang edit, thử điều hướng lại...")
            page.goto(f"https://studio.youtube.com/video/{video_id}/edit")
            page.wait_for_timeout(3000)
        
        # Chờ trang load hoàn toàn (thay đổi từ networkidle sang domcontentloaded)
        try:
            print("Chờ trang load...")
            page.wait_for_load_state("domcontentloaded", timeout=15000)
            print("✅ Trang đã load xong")
        except Exception as e:
            print(f"⚠️ Timeout chờ trang load: {e}")
            print("Tiếp tục với trang hiện tại...")
        
        # Chờ thêm một chút để JavaScript chạy xong
        page.wait_for_timeout(3000)
        
        # Debug: In ra thông tin element trên trang
        debug_page_elements(page)
        
        # Kiểm tra xem có nút "Chế độ hiển thị" không
        visibility_button = page.locator('button:has-text("Chế độ hiển thị"), button:has-text("Visibility"), [aria-label*="visibility"], [aria-label*="hiển thị"]')
        if visibility_button.count() > 0:
            print("✅ Tìm thấy nút Chế độ hiển thị")
        else:
            print("❌ Không tìm thấy nút Chế độ hiển thị, có thể cần scroll hoặc chờ thêm")
            # Thử scroll xuống để tìm
            page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
            page.wait_for_timeout(2000)
            debug_page_elements(page)
        
        # Thực hiện các bước tự động với AI
        steps = [
            "Tìm và click vào nút Chế độ hiển thị/Visibility",
            "Click vào nút Chia sẻ riêng tư/Chia sẻ/Chỉnh sửa",
            "Nhập email vào ô input và click Xong",
            "Click Xong của popup Chế độ hiển thị",
            "Click Lưu/Save"
        ]
        
        for i, step in enumerate(steps):
            print(f"\n--- Bước {i+1}: {step} ---")
            
            # Xử lý đặc biệt cho bước 1 (tìm nút Chế độ hiển thị)
            if i == 0:  # Bước 1
                print("🔄 Xử lý bước 1: Tìm nút Chế độ hiển thị")
                if find_visibility_button(page):
                    print("✅ Hoàn thành bước 1")
                    page.wait_for_timeout(2000)
                    continue
                else:
                    print("❌ Không thể tìm thấy nút Chế độ hiển thị, thử dùng AI...")
            
            # Xử lý đặc biệt cho bước 2 (tìm nút Chia sẻ riêng tư)
            if i == 1:  # Bước 2
                print("🔄 Xử lý bước 2: Tìm nút Chia sẻ riêng tư")
                if find_share_button(page):
                    print("✅ Hoàn thành bước 2")
                    page.wait_for_timeout(2000)
                    continue
                else:
                    print("❌ Không thể tìm thấy nút Chia sẻ riêng tư, thử dùng AI...")
            
            # Xử lý đặc biệt cho bước 3 (nhập email và click Xong)
            if i == 2:  # Bước 3
                print("🔄 Xử lý bước 3: Nhập email và click Xong")
                if emails and len(emails) > 0:
                    email = emails[0]  # Lấy email đầu tiên
                    print(f"📧 Nhập email: {email}")
                    
                    # Tìm input field và nhập email với nhiều loại element khác nhau
                    try:
                        # Thử nhiều loại input field khác nhau
                        input_selectors = [
                            'input[type="email"]',
                            'input[type="text"]',
                            'input[placeholder*="email"]',
                            'input[placeholder*="Email"]',
                            'input[aria-label*="email"]',
                            'input[aria-label*="Email"]',
                            'textarea',
                            '[contenteditable="true"]',
                            '[role="textbox"]',
                            '[data-testid*="email"]',
                            '[data-testid*="input"]',
                            'ytcp-text-input',
                            'ytcp-input',
                            'form input',
                            '.email-input',
                            '.input-field'
                        ]
                        
                        input_found = False
                        for selector in input_selectors:
                            try:
                                input_field = page.locator(selector)
                                if input_field.count() > 0:
                                    for j in range(input_field.count()):
                                        field = input_field.nth(j)
                                        if field.is_visible():
                                            print(f"✅ Tìm thấy input field với selector: {selector}")
                                            
                                            # Thử nhập email
                                            try:
                                                field.fill(email)
                                                print(f"✅ Đã nhập email: {email}")
                                                input_found = True
                                                break
                                            except Exception as fill_error:
                                                print(f"❌ Không thể nhập vào field này: {fill_error}")
                                                continue
                                    
                                    if input_found:
                                        break
                            except Exception as e:
                                print(f"❌ Lỗi với selector {selector}: {e}")
                                continue
                        
                        if input_found:
                            # Chờ một chút để UI cập nhật
                            print("⏳ Chờ UI cập nhật sau khi nhập email...")
                            page.wait_for_timeout(2000)
                            
                            # Tìm và click nút "Xong" với logic cải thiện
                            print("🔍 Tìm nút Xong sau khi nhập email...")
                            
                            # Thử tìm nút Xong với nhiều cách khác nhau
                            done_found = False
                            
                            # Cách 1: Tìm nút Xong thông minh
                            if find_done_button_email_section(page):
                                print("✅ Đã click Xong (thông minh)")
                                done_found = True
                            else:
                                print("❌ Không tìm thấy nút Xong (thông minh)")
                            
                            # Cách 2: Nếu không tìm thấy, thử tìm nút enabled
                            if not done_found:
                                print("🔍 Thử tìm nút Xong enabled...")
                                
                                # Thử nhiều lần với thời gian chờ khác nhau
                                for attempt in range(3):
                                    print(f"   Lần thử {attempt + 1}/3...")
                                    
                                    if find_done_button_enabled(page):
                                        print("✅ Đã click nút Xong enabled")
                                        done_found = True
                                        break
                                    else:
                                        print(f"   Lần {attempt + 1} thất bại, chờ 2 giây...")
                                        page.wait_for_timeout(2000)
                                
                                if not done_found:
                                    print("❌ Không tìm thấy nút Xong enabled sau 3 lần thử")
                            
                            # Cách 3: Thử nhấn Enter
                            if not done_found:
                                print("🔍 Thử nhấn Enter...")
                                try:
                                    page.keyboard.press('Enter')
                                    print("✅ Đã nhấn Enter")
                                    done_found = True
                                except Exception as e:
                                    print(f"❌ Không thể nhấn Enter: {e}")
                            
                            # Cách 4: Thử click nút disabled (cuối cùng)
                            if not done_found:
                                print("🔍 Thử click nút Xong disabled...")
                                if find_done_button(page):  # Sử dụng hàm cũ để click cả disabled
                                    print("✅ Đã click nút Xong (có thể disabled)")
                                    done_found = True
                                else:
                                    print("❌ Không thể click nút Xong disabled")
                            
                            if done_found:
                                print("✅ Hoàn thành nhập email và click Xong")
                                # Chờ thêm thời gian để popup xuất hiện
                                page.wait_for_timeout(3000)
                                continue
                            else:
                                print("❌ Không thể click Xong, thử dùng AI...")
                        else:
                            print("❌ Không tìm thấy input field phù hợp, thử JavaScript...")
                            # Thử bằng JavaScript
                            if find_and_fill_email_field(page, email):
                                page.wait_for_timeout(2000)
                                if find_done_button_enabled(page):
                                    print("✅ Đã click Xong sau khi nhập email (JavaScript)")
                                    page.wait_for_timeout(3000)
                                    continue
                                else:
                                    print("❌ Không tìm thấy nút Xong, thử dùng AI...")
                            else:
                                print("❌ Không thể nhập email, thử dùng AI...")
                            
                    except Exception as e:
                        print(f"❌ Lỗi nhập email: {e}, thử dùng AI...")
            
            # Xử lý đặc biệt cho bước 4 (popup)
            if i == 3:  # Bước 4
                print("🔄 Xử lý bước 4: Click Xong trong popup Chế độ hiển thị")
                if find_done_button_popup(page):
                    print("✅ Hoàn thành bước 4")
                    page.wait_for_timeout(2000)
                    continue
                else:
                    print("❌ Không thể xử lý popup, thử dùng AI...")
            
            # Xử lý đặc biệt cho bước 5 (Lưu)
            if i == 4:  # Bước 5
                print("🔄 Xử lý bước 5: Click Lưu")
                if find_save_button(page):
                    print("✅ Hoàn thành bước 5")
                    page.wait_for_timeout(2000)
                    continue
                else:
                    print("❌ Không thể tìm thấy nút Lưu, thử dùng AI...")
            
            # Lấy thông tin trang hiện tại
            page_info = get_page_info(page)
            
            # Hỏi AI cần làm gì
            action_info = ask_ai_for_action(page_info, step, emails if "email" in step.lower() else None)
            print(f"AI đề xuất: {action_info}")
            
            # Thực hiện thao tác
            success = execute_ai_action(page, action_info, step)
            if not success:
                print(f"Không thể thực hiện bước: {step}")
                # Thử lại với phương pháp thủ công cho bước 1
                if i == 0:
                    print("🔄 Thử lại với phương pháp thủ công...")
                    if find_visibility_button(page):
                        print("✅ Hoàn thành bước 1 (thủ công)")
                        page.wait_for_timeout(2000)
                        continue
                break
            
            # Chờ một chút
            page.wait_for_timeout(2000)
        
        print(f"\nHoàn tất quy trình chia sẻ video {video_id}!")
        browser.close()

if __name__ == "__main__":
    user_prompt = input("Nhập lệnh AI (ví dụ: 'Chia sẻ video abc123 cho email test@gmail.com'): ")
    share_video_with_ai(user_prompt)