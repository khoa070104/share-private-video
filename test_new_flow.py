#!/usr/bin/env python3
"""
Test script để kiểm tra flow mới với 6 bước
"""

import os
import sys
from dotenv import load_dotenv

# Thêm thư mục src vào path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_new_flow():
    """Test flow mới với 6 bước"""
    print("=== TEST FLOW MỚI VỚI 6 BƯỚC ===")
    print("Flow chuẩn mới:")
    print("1. Tìm và click vào nút 'Chế độ hiển thị' hoặc 'Visibility'")
    print("2. Chọn 'Riêng tư' hoặc 'Private'")
    print("3. Nhập email vào ô input và click 'Xong'")
    print("4. Click vào nút 'Chia sẻ' hoặc 'Chỉnh sửa' hoặc 'Share' hoặc 'Edit'")
    print("5. Click 'Xong' của popup Chế độ hiển thị")
    print("6. Click 'Lưu' hoặc 'Save'")
    print()
    
    # Kiểm tra các biến môi trường
    load_dotenv()
    required_vars = ['BROWSER_USER_DATA', 'GOOGLE_API_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Thiếu các biến môi trường: {missing_vars}")
        print("Vui lòng tạo file .env với các biến này")
        return False
    
    print("✅ Các biến môi trường đã được cấu hình")
    
    # Test prompt
    test_prompt = "Chia sẻ video 9-hAmy3PDJk cho accffao011@gmail.com"
    print(f"📝 Test prompt: {test_prompt}")
    
    try:
        from agent.youtube_share_agent import share_video_with_ai
        print("🚀 Bắt đầu test flow mới...")
        share_video_with_ai(test_prompt)
        return True
    except Exception as e:
        print(f"❌ Lỗi trong quá trình test: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    success = test_new_flow()
    if success:
        print("\n✅ Test flow mới hoàn tất thành công!")
    else:
        print("\n❌ Test flow mới thất bại!")

if __name__ == "__main__":
    main() 