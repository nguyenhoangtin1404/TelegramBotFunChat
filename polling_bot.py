"""
Simple polling-based bot (alternative to webhook).
Run this if you don't have a public domain for webhooks.
"""

import time
import logging
from telegram_bot import handle_update, validate_config
import requests
import os
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"


def get_updates(offset: int = None) -> tuple[list, int]:
    """
    Get updates from Telegram using long polling.
    
    Args:
        offset: Update ID to start from
        
    Returns:
        Tuple of (updates list, next offset)
    """
    try:
        payload = {
            "timeout": 30,
            "allowed_updates": ["message"]
        }
        
        if offset:
            payload["offset"] = offset
        
        response = requests.post(
            f"{TELEGRAM_API_URL}/getUpdates",
            json=payload,
            timeout=35
        )
        response.raise_for_status()
        
        data = response.json()
        
        if data.get('ok'):
            updates = data.get('result', [])
            next_offset = updates[-1]['update_id'] + 1 if updates else offset
            return updates, next_offset
        else:
            logger.error(f"Telegram API error: {data}")
            return [], offset
            
    except Exception as e:
        logger.error(f"Error getting updates: {e}")
        return [], offset


def run_polling():
    """Run the bot using long polling."""
    if not validate_config():
        logger.error("Configuration validation failed")
        return
    
    logger.info("Starting bot with polling mode...")
    
    offset = None
    
    try:
        while True:
            try:
                updates, offset = get_updates(offset)
                
                for update in updates:
                    try:
                        handle_update(update)
                    except Exception as e:
                        logger.error(f"Error processing update {update.get('update_id')}: {e}")
                
                if not updates:
                    # No updates, just wait and try again
                    time.sleep(1)
                    
            except KeyboardInterrupt:
                logger.info("Bot interrupted by user")
                break
            except Exception as e:
                logger.error(f"Polling error: {e}")
                time.sleep(5)  # Wait before retrying
                
    except Exception as e:
        logger.error(f"Fatal error in polling loop: {e}")


if __name__ == "__main__":
    run_polling()
