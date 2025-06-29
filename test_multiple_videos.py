#!/usr/bin/env python3
"""
Test tính năng xử lý nhiều video cùng lúc
"""

import os
import sys
sys.path.append('src')

from dotenv import load_dotenv
from src.agent.youtube_share_agent import share_video_with_ai

# Load biến môi trường
load_dotenv()

def test_multiple_videos():
    """Test xử lý nhiều video"""
    
    print("🎬 TEST XỬ LÝ NHIỀU VIDEO")
    print("="*50)
    
    # Test cases
    test_cases = [
        "Chia sẻ video abc123 và def456 cho email test@gmail.com",
        "Chia sẻ video xyz789, uvw012, rst345 cho email user@example.com",
        "Chia sẻ video abc123 cho email test@gmail.com",  # Một video
        "Chia sẻ video abc123, def456, ghi789, jkl012 cho email admin@test.com"  # Nhiều video
    ]
    
    for i, test_case in enumerate(test_cases):
        print(f"\n--- Test Case {i+1} ---")
        print(f"Input: {test_case}")
        
        try:
            share_video_with_ai(test_case)
            print(f"✅ Test Case {i+1} PASSED")
        except Exception as e:
            print(f"❌ Test Case {i+1} FAILED: {e}")
        
        print("-" * 30)

if __name__ == "__main__":
    test_multiple_videos() 