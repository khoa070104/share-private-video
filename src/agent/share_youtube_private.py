import os
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

# Load biến môi trường từ file .env
load_dotenv()

# Có thể nhập nhiều video ID, phân cách bằng dấu phẩy
VIDEO_IDS = os.getenv("YOUTUBE_VIDEO_IDS", "").split(",")
EMAILS = os.getenv("SHARE_EMAILS", "").split(",")
PROFILE_PATH = "E:\\chrome-profile-youtube"  # Đã cấu hình cứng

def share_video():
    if not os.path.exists(PROFILE_PATH):
        print(f"Không tìm thấy thư mục profile: {PROFILE_PATH}")
        print("Hãy thực hiện các bước sau:")
        print('1. Chạy lệnh: "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" --user-data-dir="E:\\chrome-profile-youtube"')
        print("2. Đăng nhập vào tài khoản Google của bạn")
        print("3. Đóng Chrome")
        print("4. Chạy lại script này")
        return
    
    print(f"Sử dụng profile: {PROFILE_PATH}")
    print(f"Video IDs: {VIDEO_IDS}")
    print(f"Emails: {EMAILS}")
    
    try:
        with sync_playwright() as p:
            print("Khởi động browser...")
            
            # Tham số cho Chrome
            browser_args = [
                # Disable automation flags
                '--disable-blink-features=AutomationControlled',
                '--disable-features=IsolateOrigins,site-per-process,AutomationControlled',
                '--disable-site-isolation-trials',
                
                # Disable security features
                '--disable-web-security',
                '--disable-features=IsolateOrigins',
                '--disable-site-isolation-trials',
                '--disable-session-crashed-bubble',
                '--ignore-certificate-errors',
                '--disable-popup-blocking',
                '--disable-notifications',
                '--disable-permissions-api',
                
                # Performance & stability
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-setuid-sandbox',
                '--disable-accelerated-2d-canvas',
                '--disable-gpu',
                '--window-size=1280,800',
                
                # Mimic real browser
                '--start-maximized',
                '--no-default-browser-check',
                '--no-first-run',
                '--no-service-autorun',
                '--password-store=basic',
                '--use-mock-keychain',
                '--force-webrtc-ip-handling-policy=default_public_interface_only',
                
                # Additional stealth params
                '--disable-automation',
                '--disable-blink-features',
                '--disable-client-side-phishing-detection',
                '--disable-default-apps',
                '--disable-infobars',
                '--disable-translate',
                '--enable-automation-mode',
                '--enable-features=NetworkService,NetworkServiceInProcess',
                '--metrics-recording-only',
                '--no-experiments',
                '--no-pings',
            ]

            # Cấu hình Chrome
            launch_options = {
                'headless': False,
                'args': browser_args,
                'viewport': {'width': 1280, 'height': 800},
                'ignore_default_args': [
                    '--enable-automation',
                    '--enable-blink-features=AutomationControlled'
                ]
            }

            # Khởi động Chrome với profile đã đăng nhập sẵn
            browser = p.chromium.launch_persistent_context(
                user_data_dir=PROFILE_PATH,
                **launch_options
            )

            # Tạo page với user agent giống browser thật
            page = browser.new_page()
            
            # Thiết lập user agent và các header khác
            page.set_extra_http_headers({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'sec-ch-ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"'
            })

            # Thêm các script để giả lập browser thật
            page.add_init_script("""
                // Ẩn dấu hiệu automation
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                Object.defineProperty(navigator, 'automation', { get: () => undefined });
                
                // Giả lập plugins và mime types
                const mockPlugins = [
                    {name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format'},
                    {name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai', description: ''},
                    {name: 'Native Client', filename: 'internal-nacl-plugin', description: ''
                ];
                Object.defineProperty(navigator, 'plugins', {
                    get: () => mockPlugins
                });
                
                // Giả lập ngôn ngữ và platform
                Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
                Object.defineProperty(navigator, 'platform', { get: () => 'Win32' });
                
                // Giả lập window.chrome
                window.chrome = {
                    app: {
                        isInstalled: false,
                        InstallState: {
                            DISABLED: 'DISABLED',
                            INSTALLED: 'INSTALLED',
                            NOT_INSTALLED: 'NOT_INSTALLED'
                        },
                        RunningState: {
                            CANNOT_RUN: 'CANNOT_RUN',
                            READY_TO_RUN: 'READY_TO_RUN',
                            RUNNING: 'RUNNING'
                        }
                    },
                    runtime: {
                        OnInstalledReason: {
                            CHROME_UPDATE: 'chrome_update',
                            INSTALL: 'install',
                            SHARED_MODULE_UPDATE: 'shared_module_update',
                            UPDATE: 'update'
                        },
                        OnRestartRequiredReason: {
                            APP_UPDATE: 'app_update',
                            OS_UPDATE: 'os_update',
                            PERIODIC: 'periodic'
                        },
                        PlatformArch: {
                            ARM: 'arm',
                            ARM64: 'arm64',
                            MIPS: 'mips',
                            MIPS64: 'mips64',
                            X86_32: 'x86-32',
                            X86_64: 'x86-64'
                        },
                        PlatformNaclArch: {
                            ARM: 'arm',
                            MIPS: 'mips',
                            MIPS64: 'mips64',
                            X86_32: 'x86-32',
                            X86_64: 'x86-64'
                        },
                        PlatformOs: {
                            ANDROID: 'android',
                            CROS: 'cros',
                            LINUX: 'linux',
                            MAC: 'mac',
                            OPENBSD: 'openbsd',
                            WIN: 'win'
                        },
                        RequestUpdateCheckStatus: {
                            NO_UPDATE: 'no_update',
                            THROTTLED: 'throttled',
                            UPDATE_AVAILABLE: 'update_available'
                        }
                    }
                };
                
                // Giả lập permissions API
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );
                
                // Thêm các thuộc tính khác
                Object.defineProperty(navigator, 'maxTouchPoints', { get: () => 10 });
                Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 8 });
                Object.defineProperty(navigator, 'deviceMemory', { get: () => 8 });
                Object.defineProperty(screen, 'colorDepth', { get: () => 24 });
                Object.defineProperty(screen, 'pixelDepth', { get: () => 24 });
                
                // Giả lập WebGL
                const getParameter = WebGLRenderingContext.prototype.getParameter;
                WebGLRenderingContext.prototype.getParameter = function(parameter) {
                    // Giả lập UNMASKED_VENDOR_WEBGL
                    if (parameter === 37445) {
                        return 'Google Inc. (NVIDIA)';
                    }
                    // Giả lập UNMASKED_RENDERER_WEBGL
                    if (parameter === 37446) {
                        return 'ANGLE (NVIDIA, NVIDIA GeForce GTX 1050 Ti Direct3D11 vs_5_0 ps_5_0, D3D11)';
                    }
                    return getParameter.apply(this, arguments);
                };
            """)

            print("Browser đã khởi động thành công!")
            
            # Xử lý từng video ID
            for video_id in VIDEO_IDS:
                video_id = video_id.strip()
                if not video_id:
                    continue
                    
                print(f"\nXử lý video ID: {video_id}")
                
                # Truy cập trực tiếp vào trang edit video
                print(f"Truy cập video: {video_id}")
                page.goto(f"https://studio.youtube.com/video/{video_id}/edit")
                page.wait_for_timeout(5000)

                # Mở tab chia sẻ quyền riêng tư
                print("Thực hiện thao tác chia sẻ...")
                try:
                    # Click vào "Chế độ hiển thị"/"Visibility"
                    print("Click vào Chế độ hiển thị...")
                    visibility_selectors = [
                        'text="Chế độ hiển thị"',  # Vietnamese
                        'text="Visibility"',  # English
                    ]
                    
                    visibility_button_found = False
                    for selector in visibility_selectors:
                        try:
                            if page.locator(selector).is_visible():
                                print(f"Tìm thấy nút với selector: {selector}")
                                page.click(selector)
                                visibility_button_found = True
                                break
                        except:
                            continue
                    
                    if not visibility_button_found:
                        print(f"Không tìm thấy nút Chế độ hiển thị/Visibility cho video {video_id}")
                        continue
                    
                    page.wait_for_timeout(2000)

                    # Đợi và chuyển sang visibility select popup
                    print("Đợi visibility select popup hiện lên...")
                    visibility_select = page.locator('ytcp-video-visibility-select')
                    if visibility_select.is_visible():
                        print("Tìm thấy visibility select popup...")
                        
                        # Click vào radio button "Riêng tư"/"Private"
                        print("Click vào Riêng tư...")
                        private_radio_selectors = [
                            '#private-radio-button',  # ID
                            'input[value="private"]',  # Value attribute
                            'label:has-text("Riêng tư")',  # Vietnamese label
                            'label:has-text("Private")'  # English label
                        ]
                        
                        private_radio_found = False
                        for selector in private_radio_selectors:
                            try:
                                if page.locator(selector).is_visible():
                                    print(f"Tìm thấy radio button với selector: {selector}")
                                    page.click(selector)
                                    private_radio_found = True
                                    break
                            except:
                                continue
                        
                        if not private_radio_found:
                            print(f"Không tìm thấy radio button Riêng tư/Private cho video {video_id}")
                            continue
                        
                        page.wait_for_timeout(2000)

                        # Click vào nút "Chỉnh sửa"/"Chia sẻ"/"Edit"/"Share"
                        print("Click vào nút Chỉnh sửa/Chia sẻ...")
                        edit_button_selectors = [
                            'ytcp-button:has-text("Chỉnh sửa")',  # Vietnamese
                            'ytcp-button:has-text("Chia sẻ")',
                            'ytcp-button:has-text("Chia sẻ riêng tư")',
                            'ytcp-button:has-text("Edit")',  # English
                            'ytcp-button:has-text("Share")',
                            'ytcp-button:has-text("Private share")',
                            '.private-share-edit-button'  # CSS class
                        ]
                        
                        edit_button_found = False
                        for selector in edit_button_selectors:
                            try:
                                button = page.locator(selector)
                                if button.is_visible():
                                    print(f"Tìm thấy nút với selector: {selector}")
                                    button.click()
                                    edit_button_found = True
                                    break
                            except:
                                continue
                        
                        if not edit_button_found:
                            print(f"Không tìm thấy nút Chỉnh sửa/Chia sẻ cho video {video_id}")
                            continue
                        
                        page.wait_for_timeout(2000)

                        # Đợi dialog nhập email hiện lên
                        print("Đợi dialog nhập email...")
                        share_dialog = page.get_by_role("dialog", name="Chia sẻ video riêng tư")
                        if share_dialog.is_visible():
                            print("Tìm thấy dialog nhập email...")
                            
                            # Nhập từng email và thêm vào danh sách chia sẻ
                            for email in EMAILS:
                                email = email.strip()
                                if not email:
                                    continue
                                    
                                print(f"Thêm email: {email}")
                                # Đợi cho ô input email xuất hiện và điền email
                                email_input = share_dialog.locator('#chip-bar-container input.text-input')
                                if email_input.is_visible():
                                    email_input.fill(email)
                                    page.wait_for_timeout(1000)
                                    
                                    # Click nút Thêm bằng Enter
                                    page.keyboard.press('Enter')
                                    page.wait_for_timeout(1000)
                            
                            # Click nút Xong trong dialog nhập email
                            print("Click nút Xong trong dialog nhập email...")
                            done_button = share_dialog.locator('#done-button')
                            if done_button.is_visible():
                                print("Tìm thấy nút Xong...")
                                done_button.click()
                                page.wait_for_timeout(2000)
                            else:
                                print(f"Không tìm thấy nút Xong trong dialog nhập email cho video {video_id}")
                                continue

                        # Click nút Xong/Done trong dialog quyền riêng tư
                        print("Click nút Xong trong dialog quyền riêng tư...")
                        visibility_dialog_selectors = [
                            'tp-yt-paper-dialog[aria-label="Chọn quyền riêng tư cho video"]',  # Vietnamese
                            'tp-yt-paper-dialog[aria-label="Choose video privacy"]'  # English
                        ]
                        
                        visibility_dialog_found = False
                        for selector in visibility_dialog_selectors:
                            try:
                                dialog = page.locator(selector)
                                if dialog.is_visible():
                                    print(f"Tìm thấy dialog với selector: {selector}")
                                    save_button_selectors = [
                                        '#save-button',  # ID
                                        'button:has-text("Xong")',  # Vietnamese
                                        'button:has-text("Done")'  # English
                                    ]
                                    
                                    save_button_found = False
                                    for save_selector in save_button_selectors:
                                        try:
                                            if page.locator(save_selector).is_visible():
                                                print(f"Tìm thấy nút với selector: {save_selector}")
                                                page.click(save_selector)
                                                save_button_found = True
                                                break
                                        except:
                                            continue
                                    
                                    if not save_button_found:
                                        print(f"Không tìm thấy nút Xong/Done trong dialog quyền riêng tư cho video {video_id}")
                                        continue
                                    
                                    visibility_dialog_found = True
                                    break
                            except:
                                continue
                        
                        if not visibility_dialog_found:
                            print(f"Không tìm thấy dialog quyền riêng tư cho video {video_id}")
                            continue
                        
                        page.wait_for_timeout(3000)
                        print("Đã hoàn tất cập nhật quyền riêng tư!")

                        # Click nút Lưu/Save để hoàn tất
                        print("Click nút Lưu để hoàn tất...")
                        final_save_button_selectors = [
                            'ytcp-button#save',  # ID
                            'button:has-text("Lưu")',  # Vietnamese
                            'button:has-text("Save")'  # English
                        ]
                        
                        final_save_button_found = False
                        for selector in final_save_button_selectors:
                            try:
                                if page.locator(selector).is_visible():
                                    print(f"Tìm thấy nút với selector: {selector}")
                                    page.click(selector)
                                    final_save_button_found = True
                                    break
                            except:
                                continue
                        
                        if not final_save_button_found:
                            print(f"Không tìm thấy nút Lưu/Save cho video {video_id}")
                            continue
                        
                        page.wait_for_timeout(3000)
                        print(f"Đã lưu thành công video {video_id}!")

                        print(f"Đã chia sẻ video {video_id} cho các email:", EMAILS)
                    else:
                        print(f"Không tìm thấy visibility select popup cho video {video_id}")
                        continue

                except Exception as e:
                    print(f"Có lỗi khi thao tác chia sẻ video {video_id}:", e)
                    print("Debug info:")
                    print("1. Kiểm tra visibility select popup:", page.locator('ytcp-video-visibility-select').is_visible())
                    visibility_select = page.locator('ytcp-video-visibility-select')
                    if visibility_select.is_visible():
                        print("2. Trong visibility select:")
                        print("   - Radio Riêng tư:", page.locator('#private-radio-button').is_visible())
                        print("   - Nút Chỉnh sửa:", page.locator('.private-share-edit-button').is_visible())
                    print("3. Kiểm tra dialog nhập email:", page.locator('tp-yt-paper-dialog').is_visible())
                    share_dialog = page.locator('tp-yt-paper-dialog')
                    if share_dialog.is_visible():
                        print("   - Ô input email:", page.locator('.text-input').is_visible())
                        print("   - Nút Thêm:", page.locator('ytcp-button:has-text("Thêm")').is_visible())
                        print("   - Nút Xong:", page.locator('ytcp-button:has-text("Xong")').is_visible())
                    continue
            
            # Đợi người dùng xem kết quả
            input("Nhấn Enter để đóng browser...")
            browser.close()
            
    except Exception as e:
        print(f"Lỗi khởi động browser: {e}")
        print("Hãy kiểm tra:")
        print("1. Thư mục E:\\chrome-profile-youtube đã tồn tại chưa")
        print("2. Có Chrome nào đang chạy không (hãy đóng hết)")
        print("3. Quyền truy cập vào ổ E:")

if __name__ == "__main__":
    share_video() 