# Telegram Fun Chat Bot (Python)

A fun Telegram group bot that auto-mentions users and replies with AI-generated messages powered by Groq API, with fallback random fun messages.

## Features

✅ Auto-mention sender in replies  
✅ AI-generated responses via Groq API (llama3-8b-instant)  
✅ Fallback random fun messages (Vietnamese)  
✅ Direct reply to original message  
✅ Full Unicode/Vietnamese support  
✅ Graceful error handling  
✅ Tùy chỉnh mood trò chuyện theo từng nhóm  
✅ Trả lời nhanh câu hỏi ngày/giờ hiện tại  
✅ Có thể gửi kèm lịch sử vài tin nhắn gần nhất để Groq nắm ngữ cảnh  
✅ Two deployment options: Webhook or Polling  

## Requirements

- Python 3.8+
- Telegram Bot Token (from BotFather)
- Groq API Key (from console.groq.com)

## Installation

### 1. Clone and Setup

```bash
cd d:\MyRepo\TelegramBotFunChat
```

### 2. Create Virtual Environment (Recommended)

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Copy `.env.example` to `.env`:

```bash
copy .env.example .env
```

Edit `.env` and fill in your credentials:

```
TELEGRAM_TOKEN=your_bot_token_here
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
GROQ_API_URL=https://api.groq.com/openai/v1/chat/completions
BOT_USERNAME=your_bot_username
CHAT_HISTORY_LENGTH=4
WEBHOOK_HOST=0.0.0.0
WEBHOOK_PORT=5000
```

### Getting Your Tokens

#### Telegram Bot Token
1. Open Telegram and search for `@BotFather`
2. Send `/newbot` command
3. Follow the prompts and copy your bot token
4. Send `/setprivacy` and choose "Disable" to let bot read group messages
5. Sau khi disable privacy, thêm bot vào group rồi gửi `/start` trong chat riêng để cập nhật quyền (nếu cần)

#### Groq API Key
1. Visit https://console.groq.com
2. Sign up/login
3. Create an API key
4. Copy and save it

## Usage

### Option 1: Polling (Recommended for Testing)

Polling is simpler and doesn't require a public domain. The bot continuously asks Telegram for new messages.

```bash
python polling_bot.py
```

**Advantages:**
- No public domain needed
- Works on localhost
- Simple to test

**Disadvantages:**
- Slightly higher latency (~30s)
- Higher API usage

### Option 2: Webhook (Production)

Requires a public domain/IP and HTTPS. Telegram sends updates directly to your server.

```bash
python webhook_server.py
```

Then set the webhook on Telegram:

```bash
curl https://api.telegram.org/bot<YOUR_TOKEN>/setWebhook?url=https://yourdomain.com/<YOUR_TOKEN>
```

**Advantages:**
- Real-time message delivery
- Lower latency
- Lower API usage

**Disadvantages:**
- Requires public domain with HTTPS
- More complex setup
- Phải đảm bảo bot đã được `@BotFather` set privacy "Disable" thì Telegram mới gửi toàn bộ tin nhắn nhóm đến webhook/polling.

## Bot Commands

- `/help` hoặc `/start`: hiển thị danh sách lệnh.
- `/alive`: báo uptime bot và trạng thái Groq.
- `/mute <phút>`: khiến bot im lặng tạm thời trong nhóm.
- `/mood <tên>`: đổi mood trò chuyện (`vui`, `lem_linh`, `cau_gat`). Nếu không truyền tham số sẽ trả về mood hiện tại.
- `/autoreply <all|mention>`: điều khiển chế độ bot trả lời mọi tin nhắn hoặc chỉ khi được nhắc tên.
- `@BotName đây?`: ping trực tiếp để bot đáp "Có mặt".

## Project Structure

```
TelegramBotFunChat/
├── telegram_bot.py          # Core bot logic
├── webhook_server.py        # Flask webhook server
├── polling_bot.py           # Polling-based bot
├── requirements.txt         # Python dependencies
├── .env.example            # Environment variables template
├── .env                    # Your actual config (create from .env.example)
└── README.md              # This file
```

## How It Works

### Message Flow

1. **Receive Update** - Bot receives message from Telegram group
2. **Validation** - Ignore bot messages, non-text messages
3. **Extract Data** - Get chat_id, user_id, username, message text
4. **Call Groq AI** - Send to Groq API for intelligent response
5. **Fallback** - If Groq fails, use random fun message
6. **Build Reply** - Format: `[Username](mention_link) AI_Response`
7. **Send Reply** - Post reply to Telegram, tagged to original message

### Key Functions

- `get_groq_response()` - Call Groq API with 2s timeout
- `get_fallback_message()` - Random Vietnamese fun message
- `send_telegram_message()` - Send formatted reply to Telegram
- `process_message()` - Main processing logic
- `handle_update()` - Entry point for updates

## Configuration

### AI Model

Current model: `llama3-8b-instant` (fast, good for chat)

Alternative: `llama3-70b-versatile` (more powerful but slower)

Edit in `telegram_bot.py`:

```python
"model": "llama3-8b-instant",  # or llama3-70b-versatile
```

### System Prompt

Current Vietnamese system prompt. Edit in `telegram_bot.py`:

```python
SYSTEM_PROMPT = "Bạn là bot chat vui vẻ trong group. Trả lời ngắn gọn, vui nhộn, và thân thiện. Không vượt quá 2 câu."
```

### Conversation Context

Muốn Groq hiểu mạch hội thoại hơn? Thiết lập `CHAT_HISTORY_LENGTH` trong `.env` (ví dụ `4`) để bot luôn gửi kèm một vài tin nhắn gần nhất (bao gồm cả câu trả lời của bot). Đặt `0` nếu bạn muốn mỗi lần gọi Groq là một câu độc lập và giảm chi phí/tốc độ.

### Fallback Messages

Edit the list in `telegram_bot.py`:

```python
FALLBACK_MESSAGES = [
    "Haha nghe vui à nha 😆",
    "Cười chết mệ 😂",
    "Đó là một trò đùa tuyệt vời!",
    "Hahahaha, bạn làm tôi cười 🤣",
    "Quá hài hước rồi!",
    "Đừng làm tôi cười nữa, bụng đau rồi 😆",
    "Ơi hay quá, hay quá!",
    "Bạn thật là một người hài hước 😄",
    "Mình thích điều đó! 👍",
    "Hehe, bạn biết cách làm vui lòng người ta 😉",
]
```

## Performance

- **AI Response Time**: < 2 seconds (with timeout)
- **Fallback Response Time**: < 0.2 seconds
- **Uptime**: Designed for 24/7 operation
- **Error Handling**: Graceful fallback on any failure

## Troubleshooting

### Bot doesn't respond

1. Check that you've added bot to group chat
2. Verify `TELEGRAM_TOKEN` in `.env`
3. Check logs for errors
4. Ensure Groq API key is valid
5. Test in a private group first

### Groq API errors

- Verify API key is correct
- Check Groq API quota/balance
- Review Groq console for usage/errors

### Polling slow

- Webhook mode has better real-time performance
- Or increase timeout in `polling_bot.py`

### Import errors

```bash
# Reinstall requirements
pip install -r requirements.txt --force-reinstall
```

## Logging

Logs include:
- Update receipts
- Message processing
- API calls (success/failure)
- Errors with full stack traces

Check console output or redirect to file:

```bash
python polling_bot.py > bot.log 2>&1
```

## Security Notes

- Never commit `.env` with real tokens
- Keep `GROQ_API_KEY` and `TELEGRAM_TOKEN` secret
- Use environment variables, never hardcode
- For webhook, always use HTTPS
- Validate all incoming data

## Limits & Quotas

- **Telegram**: 30 messages/second per chat
- **Groq**: Check your plan at console.groq.com
- **Rate Limiting**: Add if needed (not included)

## Future Enhancements

- [ ] Rate limiting per user
- [ ] Database for message history
- [ ] Multiple AI model selection
- [ ] Admin commands
- [ ] Custom response templates
- [ ] Metrics/analytics
- [ ] Docker support

## License

Free to use and modify.

## Support

For issues:
1. Check logs for error messages
2. Verify credentials in `.env`
3. Test API keys separately
4. Review Telegram/Groq documentation
