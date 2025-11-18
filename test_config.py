"""
Simple test script to verify API connections and configuration.
Run this before deploying the bot.
"""

import os
import sys
import requests
from dotenv import load_dotenv

load_dotenv()

def test_telegram_token():
    """Test Telegram bot token."""
    token = os.getenv('TELEGRAM_TOKEN')
    
    if not token:
        print("❌ TELEGRAM_TOKEN not set in .env")
        return False
    
    try:
        response = requests.post(
            f"https://api.telegram.org/bot{token}/getMe",
            timeout=5
        )
        response.raise_for_status()
        data = response.json()
        
        if data.get('ok'):
            bot_info = data.get('result', {})
            print(f"✅ Telegram Token Valid")
            print(f"   Bot: @{bot_info.get('username')}")
            print(f"   Name: {bot_info.get('first_name')}")
            return True
        else:
            print(f"❌ Telegram Error: {data.get('description')}")
            return False
            
    except requests.RequestException as e:
        print(f"❌ Telegram Connection Error: {e}")
        return False


def test_groq_key():
    """Test Groq API key."""
    key = os.getenv('GROQ_API_KEY')
    
    if not key:
        print("❌ GROQ_API_KEY not set in .env")
        return False
    
    try:
        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "llama3-8b-instant",
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'Hello' briefly."}
            ]
        }
        
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=5
        )
        response.raise_for_status()
        data = response.json()
        
        if data.get('choices'):
            message = data['choices'][0]['message']['content']
            print(f"✅ Groq API Key Valid")
            print(f"   Test Response: {message[:50]}...")
            return True
        else:
            print(f"❌ Groq Error: {data}")
            return False
            
    except requests.RequestException as e:
        print(f"❌ Groq Connection Error: {e}")
        return False


def test_environment():
    """Test all environment variables."""
    print("\n=== CONFIGURATION TEST ===\n")
    
    required_vars = {
        'TELEGRAM_TOKEN': 'Telegram Bot Token',
        'GROQ_API_KEY': 'Groq API Key'
    }
    
    all_set = True
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            masked = value[:10] + "..." if len(value) > 10 else value
            print(f"✅ {description}: {masked}")
        else:
            print(f"❌ {description}: NOT SET")
            all_set = False
    
    return all_set


def main():
    """Run all tests."""
    print("\n" + "="*50)
    print("TELEGRAM FUN BOT - CONFIGURATION TEST")
    print("="*50 + "\n")
    
    # Check .env exists
    if not os.path.exists('.env'):
        print("❌ .env file not found!")
        print("   Create it from .env.example:")
        print("   cp .env.example .env")
        return False
    
    # Test environment
    env_ok = test_environment()
    
    if not env_ok:
        print("\n❌ Missing configuration. Update .env file and try again.")
        return False
    
    print("\n=== API TESTS ===\n")
    
    # Test APIs
    telegram_ok = test_telegram_token()
    print()
    groq_ok = test_groq_key()
    
    print("\n" + "="*50)
    
    if telegram_ok and groq_ok:
        print("✅ ALL TESTS PASSED - BOT IS READY!")
        print("\nStart the bot with:")
        print("  python polling_bot.py")
        print("\nOr with webhook:")
        print("  python webhook_server.py")
        return True
    else:
        print("❌ SOME TESTS FAILED - CHECK CONFIGURATION")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
