#!/usr/bin/env python3
"""
Test script để kiểm tra YouTube Share Agent với các cải tiến mới
"""

import os
import sys
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
import re
import json

# Thêm thư mục src vào path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from agent.youtube_share_agent import share_video_with_ai

# Load biến môi trường từ file .env
load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-2.5-flash")

def test_extract_share_info(prompt: str):
    """
    Test function để debug AI response parsing
    """
    template = ChatPromptTemplate.from_messages([
        ("system", "Bạn là AI chuyên phân tích lệnh chia sẻ video YouTube riêng tư. Hãy trích xuất video_id và email từ lệnh người dùng. Trả về JSON với format: {{\"video_id\": \"...\", \"emails\": [\"...\"]}}. Nếu không đủ thông tin, trả về lỗi rõ ràng."),
        ("user", "{prompt}")
    ])
    llm = ChatGoogleGenerativeAI(model=LLM_MODEL, google_api_key=GOOGLE_API_KEY)
    chain = template | llm
    result = chain.invoke({"prompt": prompt})
    
    print(f"AI Response type: {type(result)}")
    print(f"AI Response: {result}")
    
    # Lấy content từ result
    if hasattr(result, 'content'):
        result_str = str(result.content)
        print(f"Result content: {result_str}")
    else:
        result_str = str(result)
        print(f"Result string: {result_str}")
    
    # Thử tìm JSON trong markdown code block trước
    markdown_pattern = r'```(?:json)?\s*(\{[\s\S]*?\})\s*```'
    markdown_match = re.search(markdown_pattern, result_str)
    if markdown_match:
        try:
            json_str = markdown_match.group(1)
            print(f"Found JSON in markdown: {json_str}")
            data = json.loads(json_str)
            print(f"Parsed data: {data}")
            return data
        except Exception as e:
            print(f"Error parsing markdown JSON: {e}")
    
    # Nếu không tìm thấy trong markdown, thử tìm JSON thường
    json_pattern = r'\{[\s\S]*?\}'
    json_match = re.search(json_pattern, result_str)
    if json_match:
        try:
            json_str = json_match.group(0)
            print(f"Found JSON: {json_str}")
            data = json.loads(json_str)
            print(f"Parsed data: {data}")
            return data
        except Exception as e:
            print(f"Error parsing JSON: {e}")
    
    print("No JSON found!")
    return None

def main():
    # Kiểm tra các biến môi trường cần thiết
    required_vars = ['BROWSER_USER_DATA', 'GOOGLE_API_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"Thiếu các biến môi trường: {missing_vars}")
        print("Vui lòng tạo file .env với các biến này")
        return
    
    # Test prompt
    test_prompt = "Chia sẻ video abc123 cho email test@gmail.com"
    
    print("=== TEST YOUTUBE SHARE AGENT ===")
    print(f"Test prompt: {test_prompt}")
    print("Bắt đầu test...")
    
    try:
        share_video_with_ai(test_prompt)
    except Exception as e:
        print(f"Lỗi trong quá trình test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 