import os
import sys
import json
import random
import logging
import time
from datetime import datetime
import re
import requests
from typing import Optional, List, Dict
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
BOT_USERNAME = (os.getenv('BOT_USERNAME') or '').lstrip('@')
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
GROQ_API_URL = os.getenv('GROQ_API_URL', "https://api.groq.com/openai/v1/chat/completions")
try:
    CHAT_HISTORY_LENGTH = max(0, int(os.getenv('CHAT_HISTORY_LENGTH', '0')))
except ValueError:
    CHAT_HISTORY_LENGTH = 0
BOT_USER_ID = None
BOT_MENTION_PATTERN = re.compile(rf"@{re.escape(BOT_USERNAME)}", re.IGNORECASE) if BOT_USERNAME else None
if TELEGRAM_TOKEN and ':' in TELEGRAM_TOKEN:
    try:
        BOT_USER_ID = int(TELEGRAM_TOKEN.split(':', 1)[0])
    except ValueError:
        BOT_USER_ID = None

# Fallback fun messages (Vietnamese)
FALLBACK_MESSAGES = [
    "Haha nghe vui à nha 😆",
    "Ủa gì zợ? 😂 kể nghe coi",
    "Bot xỉu ngang 🤣",
    "Ghê zợ ông bạn 😜",
    "Cái này coi bộ căng à nha 😆",
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

# System prompt for Groq
SYSTEM_PROMPT = "Bạn là bot chat vui vẻ trong group. Trả lời ngắn gọn, vui nhộn, và thân thiện. Không vượt quá 2 câu."
GROQ_MODEL = os.getenv('GROQ_MODEL', 'llama3-8b-instant')
MOOD_TONES = {
    "vui": "Luôn vui vẻ, thân thiện, dùng nhiều emoji dễ thương.",
    "lem_linh": "Lém lỉnh, cà khịa nhẹ, tung hứng dí dỏm nhưng không xúc phạm.",
    "cau_gat": "Giả vờ cáu gắt, càm ràm nhưng vẫn hài hước và không quá khó chịu."
}
DEFAULT_MOOD = "vui"
MOOD_OPTIONS_TEXT = ", ".join(MOOD_TONES.keys())
VI_DAY_NAMES = [
    "Thứ Hai",
    "Thứ Ba",
    "Thứ Tư",
    "Thứ Năm",
    "Thứ Sáu",
    "Thứ Bảy",
    "Chủ Nhật"
]
HELP_TEXT = (
    "Danh sách lệnh:\n"
    "/alive - Kiểm tra bot còn hoạt động.\n"
    "/mute <phút> - Tạm im lặng trong nhóm.\n"
    "/help - Hiển thị các lệnh điều khiển.\n"
    f"/mood <tên> - Đổi mood bot ({MOOD_OPTIONS_TEXT}).\n"
    "/autoreply <all|mention> - Bật tắt chế độ trả lời tất cả hay chỉ khi được nhắc.\n"
)
if BOT_USERNAME:
    HELP_TEXT += f"Nhắc @{BOT_USERNAME} để gọi bot xác nhận.\n"

BOT_START_TIME = time.time()
chat_mute_until: dict[int, float] = {}
chat_mood: dict[int, str] = {}
chat_auto_reply_mode: dict[int, str] = {}
AUTO_REPLY_ALL = "all"
AUTO_REPLY_MENTION = "mention"
chat_history: Dict[int, List[Dict[str, str]]] = {}


def escape_markdown(text: str) -> str:
    """Escape characters that break Telegram Markdown links."""
    if not text:
        return text

    replacements = ['\\', '*', '_', '[', ']', '(', ')', '`']
    for char in replacements:
        text = text.replace(char, f"\\{char}")
    return text


def get_groq_response(message_text: str, system_prompt: str, history: Optional[List[Dict[str, str]]] = None) -> Optional[str]:
    """
    Call Groq API to generate a fun response.
    
    Args:
        message_text: User's message text
        system_prompt: Prompt describing bot behavior
        
    Returns:
        Generated response or None if failed
    """
    try:
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": message_text})

        payload = {
            "model": GROQ_MODEL,
            "messages": messages
        }
        
        response = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=2)
        response.raise_for_status()
        
        data = response.json()
        reply = data.get('choices', [{}])[0].get('message', {}).get('content', '').strip()
        
        if reply:
            logger.info(f"Groq response received: {reply[:50]}...")
            return reply
        else:
            logger.warning("Groq returned empty response")
            return None
            
    except requests.Timeout:
        logger.warning("Groq API timeout")
        return None
    except requests.RequestException as e:
        logger.error(f"Groq API error: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error calling Groq: {e}")
        return None


def get_fallback_message() -> str:
    """Get a random fallback fun message."""
    return random.choice(FALLBACK_MESSAGES)


def get_chat_mood(chat_id: int) -> str:
    """Return the configured mood for a chat."""
    return chat_mood.get(chat_id, DEFAULT_MOOD)


def set_chat_mood(chat_id: int, mood: str) -> None:
    """Persist mood selection for a chat."""
    chat_mood[chat_id] = mood


def build_system_prompt(chat_id: int) -> str:
    """Compose system prompt with mood instructions."""
    mood_key = get_chat_mood(chat_id)
    tone = MOOD_TONES.get(mood_key, MOOD_TONES[DEFAULT_MOOD])
    return f"{SYSTEM_PROMPT}\nMood hiện tại: {tone}"


def get_auto_reply_mode(chat_id: int) -> str:
    """Return current auto reply mode for chat."""
    return chat_auto_reply_mode.get(chat_id, AUTO_REPLY_ALL)


def set_auto_reply_mode(chat_id: int, mode: str) -> None:
    """Save auto reply mode for chat."""
    chat_auto_reply_mode[chat_id] = mode


def append_chat_history_entry(chat_id: int, role: str, content: str) -> None:
    if CHAT_HISTORY_LENGTH <= 0 or not content:
        return
    history = chat_history.setdefault(chat_id, [])
    history.append({"role": role, "content": content})
    if len(history) > CHAT_HISTORY_LENGTH:
        del history[0: len(history) - CHAT_HISTORY_LENGTH]


def record_conversation_turn(chat_id: int, user_text: Optional[str], bot_text: Optional[str]) -> None:
    if CHAT_HISTORY_LENGTH <= 0:
        return
    if user_text:
        append_chat_history_entry(chat_id, "user", user_text)
    if bot_text:
        append_chat_history_entry(chat_id, "assistant", bot_text)


def get_chat_history_messages(chat_id: int) -> List[Dict[str, str]]:
    if CHAT_HISTORY_LENGTH <= 0:
        return []
    history = chat_history.get(chat_id, [])
    return history[-CHAT_HISTORY_LENGTH:]


def get_local_intent_reply(message_text: str) -> Optional[str]:
    """Return a local deterministic reply for time/date questions."""
    if not message_text:
        return None
    normalized = message_text.lower()
    now = datetime.now()

    time_keywords = [
        "mấy giờ",
        "giờ mấy",
        "bây giờ là mấy giờ",
        "hiện tại mấy giờ",
        "giờ hiện tại",
    ]
    if any(keyword in normalized for keyword in time_keywords):
        return f"Bây giờ là {now.strftime('%H:%M')} (ngày {now.strftime('%d/%m/%Y')})."

    day_keywords = [
        "thứ mấy",
        "hôm nay là thứ",
        "nay là thứ",
        "hôm nay ngày",
        "ngày mấy",
        "ngày bao nhiêu",
    ]
    if any(keyword in normalized for keyword in day_keywords):
        day_name = VI_DAY_NAMES[now.weekday()]
        return f"Hôm nay {day_name}, ngày {now.strftime('%d/%m/%Y')}"

    return None


def extract_text_without_mention(text: str) -> tuple[str, bool]:
    """Remove bot mention from text and report if mention existed."""
    if not text or not BOT_MENTION_PATTERN:
        return text.strip(), False
    cleaned, count = BOT_MENTION_PATTERN.subn(' ', text)
    return cleaned.strip(), count > 0


def is_chat_muted(chat_id: int) -> bool:
    """Return True if the chat is currently muted."""
    mute_until = chat_mute_until.get(chat_id)
    if not mute_until:
        return False
    if time.time() >= mute_until:
        chat_mute_until.pop(chat_id, None)
        return False
    return True


def set_chat_mute(chat_id: int, minutes: int) -> None:
    """Mute a chat for the given number of minutes."""
    chat_mute_until[chat_id] = time.time() + (minutes * 60)


def handle_command(message_text: str, chat_id: int) -> Optional[str]:
    """Handle slash commands. Return response text if handled."""
    text = message_text.strip()
    if not text.startswith('/'):
        return None
    parts = text.split()
    if not parts:
        return None
    command = parts[0].lower()
    if '@' in command:
        command = command.split('@', 1)[0]

    if command == '/alive':
        uptime_seconds = int(time.time() - BOT_START_TIME)
        if uptime_seconds < 60:
            uptime_display = f"{uptime_seconds} giây"
        else:
            uptime_display = f"{uptime_seconds // 60} phút"
        groq_status = "đã sẵn sàng" if GROQ_API_KEY else "chưa có GROQ_API_KEY"
        return f"Bot vẫn sống khỏe ({uptime_display}). Groq {groq_status}."

    if command in ('/help', '/start'):
        return HELP_TEXT.strip()

    if command == '/mute':
        minutes = 10
        if len(parts) > 1:
            try:
                minutes = int(parts[1])
            except ValueError:
                return "Vui lòng nhập số phút hợp lệ, ví dụ /mute 10."
        if minutes <= 0:
            return "Số phút phải lớn hơn 0."
        set_chat_mute(chat_id, minutes)
        return f"Đã im lặng trong {minutes} phút."

    if command == '/mood':
        if len(parts) == 1:
            current = get_chat_mood(chat_id)
            return f"Mood hiện tại: {current}. Mood khả dụng: {MOOD_OPTIONS_TEXT}."
        mood_raw = " ".join(parts[1:]).strip().lower()
        mood_key = mood_raw.replace(" ", "_")
        if mood_key not in MOOD_TONES:
            return f"Mood không hợp lệ. Chọn một trong: {MOOD_OPTIONS_TEXT}."
        set_chat_mood(chat_id, mood_key)
        return f"Đã chuyển mood sang {mood_key}. {MOOD_TONES[mood_key]}"

    if command == '/autoreply':
        if len(parts) == 1:
            return f"Auto-reply hiện tại: {get_auto_reply_mode(chat_id)} (all/mention)."
        mode = parts[1].lower()
        if mode not in (AUTO_REPLY_ALL, AUTO_REPLY_MENTION):
            return "Chỉ chấp nhận 'all' hoặc 'mention'. Ví dụ: /autoreply mention"
        set_auto_reply_mode(chat_id, mode)
        if mode == AUTO_REPLY_ALL:
            return "Bot sẽ trả lời tất cả tin nhắn văn bản."
        return "Bot sẽ chỉ trả lời khi được nhắc tên hoặc lệnh."

    return None


def send_telegram_message(chat_id: int, text: str, reply_to_message_id: int) -> bool:
    """
    Send a message to Telegram group.
    
    Args:
        chat_id: Group chat ID
        text: Message text (with mention and response)
        reply_to_message_id: Message ID to reply to
        
    Returns:
        True if successful, False otherwise
    """
    try:
        payload = {
            "chat_id": chat_id,
            "text": text,
            "reply_to_message_id": reply_to_message_id,
            "parse_mode": "Markdown"
        }
        
        response = requests.post(
            f"{TELEGRAM_API_URL}/sendMessage",
            json=payload,
            timeout=5
        )
        response.raise_for_status()

        logger.info(f"Message sent to chat {chat_id}")
        return True
        
    except requests.RequestException as e:
        error_body = ''
        if 'response' in locals() and response is not None:
            try:
                error_body = response.text
            except Exception:
                error_body = ''
        logger.error(f"Failed to send Telegram message: {e}. Response: {error_body}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending message: {e}")
        return False


def process_message(update: dict) -> None:
    """
    Process an incoming Telegram message and send a reply.
    
    Args:
        update: Telegram update object
    """
    try:
        # Extract message data
        message = update.get('message', {})
        
        # Ignore if not a text message
        if not message or 'text' not in message:
            logger.debug("Ignoring non-text message")
            return
        
        # Ignore bot messages
        from_user = message.get('from', {})
        if from_user.get('is_bot', False):
            logger.debug("Ignoring bot message")
            return
        
        # Extract required fields
        chat_id = message.get('chat', {}).get('id')
        message_id = message.get('message_id')
        user_id = from_user.get('id')
        # Use username if available, fallback to first_name
        username = from_user.get('username') or from_user.get('first_name') or 'User'
        original_text = message.get('text', '')
        message_text = original_text.strip()
        cleaned_text, has_mention = extract_text_without_mention(original_text)
        auto_reply_mode = get_auto_reply_mode(chat_id)
        if has_mention:
            if not cleaned_text:
                reply_text = "Có mặt! Bạn cần gì nè?"
                safe_username = escape_markdown(username)
                safe_reply = escape_markdown(reply_text)
                final_message = f"[{safe_username}](tg://user?id={user_id}) {safe_reply}"
                send_telegram_message(chat_id, final_message, message_id)
                user_entry = original_text.strip() or (f"@{BOT_USERNAME}" if BOT_USERNAME else original_text.strip())
                record_conversation_turn(chat_id, user_entry, reply_text)
                return
            message_text = cleaned_text
        elif auto_reply_mode == AUTO_REPLY_MENTION:
            # Only respond to commands when in mention-only mode
            if not message_text.startswith('/'):
                logger.info(f"Chat {chat_id} ở chế độ mention, bỏ qua tin nhắn không mention")
                return
        reply_to = message.get('reply_to_message') or {}
        reply_to_user = reply_to.get('from', {}) if reply_to else {}
        is_reply_to_bot = bool(BOT_USER_ID and reply_to_user.get('id') == BOT_USER_ID)
        
        # Validate extracted data
        if not all([chat_id, message_id, user_id, message_text]):
            logger.warning(f"Missing required fields - chat_id: {chat_id}, message_id: {message_id}, user_id: {user_id}, text: {bool(message_text)}")
            return
        
        logger.info(f"Processing message from {username} (ID: {user_id}): {original_text[:50]}")

        # Quick reply when user replies directly to bot message
        if is_reply_to_bot and not original_text.strip():
            reply_text = "Có mặt! Bạn cần gì nè?"
            safe_username = escape_markdown(username)
            safe_reply = escape_markdown(reply_text)
            final_message = f"[{safe_username}](tg://user?id={user_id}) {safe_reply}"
            send_telegram_message(chat_id, final_message, message_id)
            record_conversation_turn(chat_id, original_text.strip(), reply_text)
            return

        # Slash commands
        command_reply = handle_command(message_text, chat_id)
        if command_reply:
            safe_username = escape_markdown(username)
            safe_reply = escape_markdown(command_reply)
            final_message = f"[{safe_username}](tg://user?id={user_id}) {safe_reply}"
            send_telegram_message(chat_id, final_message, message_id)
            record_conversation_turn(chat_id, message_text, command_reply)
            return

        # Respect mute state
        if is_chat_muted(chat_id):
            logger.info(f"Chat {chat_id} đang trong trạng thái im lặng, bỏ qua tin nhắn.")
            return

        # Local deterministic replies (time/date queries)
        local_reply = get_local_intent_reply(message_text)
        if local_reply:
            safe_username = escape_markdown(username)
            safe_reply = escape_markdown(local_reply)
            final_message = f"[{safe_username}](tg://user?id={user_id}) {safe_reply}"
            send_telegram_message(chat_id, final_message, message_id)
            record_conversation_turn(chat_id, message_text, local_reply)
            return

        # Try to get AI response with mood-aware prompt, fallback if it fails
        system_prompt = build_system_prompt(chat_id)
        history_messages = get_chat_history_messages(chat_id)
        ai_response = get_groq_response(message_text, system_prompt, history_messages)
        reply_text = ai_response if ai_response else get_fallback_message()

        # Build final message with mention and escape Markdown characters in name
        safe_username = escape_markdown(username)
        safe_reply = escape_markdown(reply_text)
        final_message = f"[{safe_username}](tg://user?id={user_id}) {safe_reply}"

        # Send reply
        send_telegram_message(chat_id, final_message, message_id)
        record_conversation_turn(chat_id, message_text, reply_text)
        
    except Exception as e:
        logger.error(f"Error processing message: {e}")


def handle_update(update: dict) -> None:
    """
    Handle incoming Telegram update from webhook.
    
    Args:
        update: Telegram update dictionary
    """
    try:
        process_message(update)
    except Exception as e:
        logger.error(f"Error handling update: {e}")


def validate_config() -> bool:
    """Validate required environment variables."""
    if not TELEGRAM_TOKEN:
        logger.error("TELEGRAM_TOKEN not set in environment")
        return False
    if not GROQ_API_KEY:
        logger.error("GROQ_API_KEY not set in environment")
        return False
    return True


def main():
    """Main entry point for webhook server."""
    if not validate_config():
        logger.error("Configuration validation failed")
        sys.exit(1)
    
    logger.info("Telegram Fun Chat Bot initialized")
    logger.info("Waiting for messages...")
    
    # This function would typically be called from a Flask/FastAPI webhook
    # For now, just log that it's ready
    print("Bot is ready. Use webhook or polling to receive updates.")


if __name__ == "__main__":
    main()
