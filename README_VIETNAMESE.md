# 🌐 Browser Use WebUI - Hướng dẫn sử dụng Chrome Profile đã đăng nhập Gmail

## 📋 Tổng quan

Dự án này cho phép bạn sử dụng AI để điều khiển trình duyệt Chrome với profile đã đăng nhập sẵn Gmail. Điều này có nghĩa là bạn chỉ cần đăng nhập Gmail một lần, sau đó AI có thể tự động thực hiện các tác vụ như đọc email, gửi email, quản lý inbox, v.v.

**🤖 AI Agent**: Sử dụng Google Gemini 2.5 Flash để xử lý các tác vụ thông minh.

## 🚀 Cài đặt nhanh

### Bước 1: Chạy script tự động cấu hình
```bash
python setup_chrome_profile.py
```

Script này sẽ:
- Tự động phát hiện đường dẫn Chrome và User Data
- Tạo file `.env` với cấu hình phù hợp
- Cấu hình Google Gemini API key sẵn
- Cài đặt các dependencies cần thiết
- Tạo các thư mục cần thiết

### Bước 2: Chạy ứng dụng
```bash
python webui.py --ip 127.0.0.1 --port 7788
```

### Bước 3: Truy cập WebUI
Mở trình duyệt (không phải Chrome) và truy cập: `http://127.0.0.1:7788`

## 🎯 Các tính năng chính

### ✅ Sử dụng Chrome Profile đã đăng nhập
- Không cần đăng nhập lại Gmail
- Giữ nguyên cookies, bookmarks, extensions
- Hoạt động với tất cả tài khoản Google

### 🤖 Google Gemini AI Agent
- Sử dụng Gemini 2.5 Flash - model AI mạnh mẽ nhất của Google
- Hỗ trợ đa ngôn ngữ (tiếng Việt, tiếng Anh)
- Có thể thực hiện các tác vụ phức tạp
- Giao diện web thân thiện

### 📹 Recording và Tracing
- Ghi lại video các thao tác
- Lưu trữ lịch sử agent
- Debug dễ dàng

## 💡 Các prompt ví dụ

### Gmail Operations
```
"Mở Gmail và kiểm tra email mới nhất"
"Tìm email từ john@example.com trong 7 ngày qua"
"Đếm số email chưa đọc trong inbox"
"Gửi email cho admin@company.com với tiêu đề 'Báo cáo tuần'"
"Tìm và xóa tất cả email spam"
"Tạo label mới tên 'Quan trọng' và gán cho email từ boss@company.com"
```

### YouTube Operations
```
"Mở YouTube và tìm video về 'Python tutorial'"
"Đăng ký kênh 'Tech With Tim'"
"Like video đầu tiên trong kết quả tìm kiếm"
"Thêm video vào playlist 'Học lập trình'"
```

### Google Drive Operations
```
"Mở Google Drive và tạo thư mục mới tên 'Projects'"
"Upload file từ desktop vào Google Drive"
"Chia sẻ thư mục 'Documents' với user@example.com"
"Tìm file có tên chứa 'report'"
```

## ⚙️ Cấu hình nâng cao

### Browser Settings
- **Browser Binary Path**: Đường dẫn đến chrome.exe
- **Browser User Data Dir**: Đường dẫn đến Chrome User Data
- **Use Own Browser**: Bật để sử dụng profile đã đăng nhập
- **Keep Browser Open**: Giữ browser mở giữa các task
- **Headless Mode**: Tắt để xem browser hoạt động

### Agent Settings
- **LLM Provider**: Google (đã cấu hình sẵn)
- **Model**: gemini-2.5-flash (đã cấu hình sẵn)
- **API Key**: Đã được cấu hình trong file .env

## 🔧 Troubleshooting

### Lỗi thường gặp

1. **Chrome đang chạy**
   ```
   ❌ Lỗi: Chrome đang được sử dụng
   ✅ Giải pháp: Đóng tất cả Chrome windows trước khi chạy
   ```

2. **Profile bị khóa**
   ```
   ❌ Lỗi: User data directory is already in use
   ✅ Giải pháp: Đóng Chrome hoàn toàn và thử lại
   ```

3. **Đường dẫn sai**
   ```
   ❌ Lỗi: Chrome not found
   ✅ Giải pháp: Kiểm tra lại đường dẫn trong file .env
   ```

4. **Gemini API Key không hợp lệ**
   ```
   ❌ Lỗi: Invalid API key
   ✅ Giải pháp: Kiểm tra GOOGLE_API_KEY trong file .env
   ```

### Debug
- Kiểm tra logs trong terminal
- Đảm bảo `USE_OWN_BROWSER=true` trong .env
- Kiểm tra Chrome version compatibility
- Đảm bảo Gemini API key có quyền truy cập

## 📁 Cấu trúc thư mục

```
share-private-video/
├── .env                    # Cấu hình môi trường (với Gemini API)
├── setup_chrome_profile.py # Script tự động cấu hình
├── webui.py               # Entry point
├── requirements.txt       # Dependencies
├── src/                   # Source code
├── tmp/                   # Temporary files
│   ├── record_videos/     # Browser recordings
│   ├── traces/           # Agent traces
│   ├── agent_history/    # Agent history
│   └── downloads/        # Downloaded files
└── README_VIETNAMESE.md  # Hướng dẫn này
```

## 🔒 Bảo mật

1. **API Keys**: Không commit file `.env` lên git
2. **Chrome Profile**: Backup profile trước khi sử dụng
3. **Permissions**: Chỉ cấp quyền cần thiết cho agent
4. **Updates**: Cập nhật Chrome và dependencies thường xuyên
5. **Gemini API**: Đảm bảo API key có quyền truy cập phù hợp

## 🤝 Đóng góp

Nếu bạn gặp vấn đề hoặc có ý tưởng cải thiện, hãy:
1. Tạo issue trên GitHub
2. Fork repository và tạo pull request
3. Tham gia Discord community

## 📞 Hỗ trợ

- 📖 [Documentation](https://docs.browser-use.com)
- 💬 [Discord](https://link.browser-use.com/discord)
- 🐛 [GitHub Issues](https://github.com/browser-use/web-ui/issues)

## 📄 License

Dự án này được phát hành dưới MIT License. Xem file [LICENSE](LICENSE) để biết thêm chi tiết.

---

**Lưu ý**: Đảm bảo tuân thủ Terms of Service của các dịch vụ bạn sử dụng (Gmail, YouTube, v.v.) khi sử dụng automation tools. 