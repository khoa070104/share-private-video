# Cải Tiến Flow Chia Sẻ Video YouTube

## Flow Chuẩn Mới (6 Bước)

Code đã được cải tiến để tuân theo flow chuẩn sau:

1. **Tìm và click vào nút "Chế độ hiển thị" hoặc "Visibility"**
   - Hỗ trợ tìm kiếm button, div, span có thể click
   - Tìm theo text, aria-label, title, data-testid, class name

2. **Chọn "Riêng tư" hoặc "Private"**
   - Tự động chọn chế độ riêng tư cho video

3. **Nhập email vào ô input và click "Xong"**
   - **BƯỚC MỚI**: Tự động nhập email và click "Xong" ngay sau đó
   - Tìm input field và nhập email được chỉ định
   - Tự động tìm và click nút "Xong"

4. **Click vào nút "Chia sẻ" hoặc "Chỉnh sửa" hoặc "Share" hoặc "Edit"**
   - Mở giao diện chia sẻ video

5. **Click "Xong" của popup Chế độ hiển thị**
   - Xử lý popup/modal đặc biệt
   - Tìm và click nút "Xong" trong popup

6. **Click "Lưu" hoặc "Save"**
   - Lưu thay đổi và hoàn tất quy trình

## Các Cải Tiến Chính

### 1. Flow Được Tối Ưu Hóa
- Giảm từ 7 bước xuống 6 bước
- Bước 3 kết hợp nhập email và click "Xong"
- Xử lý popup ở bước 5 thay vì bước 6

### 2. Xử Lý Email Tự Động (Bước 3)
- Tự động tìm input field
- Nhập email và click "Xong" trong một bước
- Fallback về AI nếu thất bại

### 3. Xử Lý Popup Cải Tiến (Bước 5)
- Hàm `handle_popup_done()` chuyên xử lý popup
- Tìm popup bằng nhiều selector khác nhau
- Click "Xong" trong popup bằng JavaScript

### 4. Tìm Kiếm Element Tốt Hơn
- Mở rộng tìm kiếm từ chỉ button sang tất cả element có thể click
- Hỗ trợ div, span với onclick, tabindex
- Tìm theo aria-label, title, data-testid

### 5. Debug Tốt Hơn
- Hàm `debug_page_elements()` in thông tin chi tiết
- Hiển thị tất cả element có thể click
- Giúp debug khi không tìm thấy element

## Cách Sử Dụng

### 1. Chạy Test Flow Mới
```bash
python test_new_flow.py
```

### 2. Chạy Agent Chính
```bash
python src/agent/youtube_share_agent.py
```

### 3. Cấu Hình Biến Môi Trường
Tạo file `.env` với:
```
BROWSER_USER_DATA=đường_dẫn_đến_profile_chrome
GOOGLE_API_KEY=your_google_api_key
LLM_MODEL=gemini-2.5-flash
```

## Xử Lý Lỗi

### Lỗi Không Tìm Thấy Element
- Code sẽ thử 9 phương pháp khác nhau để tìm element
- Tự động tìm element tương tự nếu không tìm thấy chính xác
- In thông tin debug để hỗ trợ

### Lỗi Nhập Email (Bước 3)
- Tự động tìm input field
- Thử nhiều loại input khác nhau
- Fallback về AI nếu thất bại

### Lỗi Popup (Bước 5)
- Tự động phát hiện và xử lý popup/modal
- Thử nhiều selector khác nhau
- Fallback về tìm nút "Xong" thông thường

## Lưu Ý Quan Trọng

1. **Đảm bảo đăng nhập YouTube Studio** trước khi chạy
2. **Video phải tồn tại** và có quyền chỉnh sửa
3. **Email phải hợp lệ** để chia sẻ
4. **Chờ đủ thời gian** giữa các bước (2 giây)
5. **Kiểm tra debug output** nếu có lỗi

## Troubleshooting

### Không Click Được "Chế Độ Hiển Thị"
- Kiểm tra debug output để xem element có tồn tại không
- Thử refresh trang và chạy lại
- Kiểm tra quyền chỉnh sửa video

### Email Không Được Nhập (Bước 3)
- Kiểm tra input field có visible không
- Thử nhập thủ công để xác nhận field hoạt động
- Kiểm tra format email

### Popup Không Xuất Hiện (Bước 5)
- Đảm bảo đã click đúng nút "Chế độ hiển thị"
- Chờ thêm thời gian cho popup load
- Kiểm tra console browser để xem lỗi JavaScript 