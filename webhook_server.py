"""
Flask webhook server for Telegram bot.
Receives updates from Telegram and processes them.
"""

import os
import logging
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from telegram_bot import handle_update, validate_config

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Configuration
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
WEBHOOK_HOST = os.getenv('WEBHOOK_HOST', 'localhost')
WEBHOOK_PORT = int(os.getenv('WEBHOOK_PORT', 5000))
WEBHOOK_PATH = f"/{TELEGRAM_TOKEN}"


@app.route(WEBHOOK_PATH, methods=['POST'])
def webhook():
    """
    Webhook endpoint for Telegram updates.
    Receives POST requests from Telegram servers.
    """
    try:
        update = request.get_json()
        
        if not update:
            logger.warning("Received empty update")
            return jsonify({"ok": False, "error": "Empty update"}), 400
        
        logger.debug(f"Received update: {update}")
        
        # Process the update asynchronously
        handle_update(update)
        
        # Always return 200 OK to acknowledge to Telegram
        return jsonify({"ok": True}), 200
        
    except Exception as e:
        logger.error(f"Error in webhook handler: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy"}), 200


@app.route('/', methods=['GET'])
def index():
    """Index endpoint."""
    return jsonify({"message": "Telegram Fun Chat Bot is running"}), 200


if __name__ == "__main__":
    if not validate_config():
        logger.error("Configuration validation failed")
        exit(1)
    
    logger.info(f"Starting webhook server on {WEBHOOK_HOST}:{WEBHOOK_PORT}")
    logger.info(f"Webhook path: {WEBHOOK_PATH}")
    
    app.run(
        host=WEBHOOK_HOST,
        port=WEBHOOK_PORT,
        debug=False,
        threaded=True
    )
