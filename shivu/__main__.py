import importlib
import time
import random
import re
import asyncio
import uvloop
from html import escape

# Set uvloop as the event loop policy
uvloop.install()

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CommandHandler, CallbackContext, MessageHandler, filters

from shivu import (
    collection,
    top_global_groups_collection,
    group_user_totals_collection,
    user_collection,
    user_totals_collection,
    shivuu,
    application,
    SUPPORT_CHAT,
    UPDATE_CHAT,
    db,
    LOGGER,
)
from shivu.modules import ALL_MODULES
from shivu.modules.lrank import periodic_rank_updates, initialize_rank_db
from shivu.modules.lloan import initialize_loan_db, periodic_loan_checks

from flask import Flask, jsonify
import threading

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({"status": "running", "message": "Bot is alive!"})

@app.route('/random')
def random_number():
    return jsonify({"number": random.randint(1, 50)})

def run_flask():
    app.run(host="0.0.0.0", port=7860)

# Import all modules
for module_name in ALL_MODULES:
    imported_module = importlib.import_module("shivu.modules." + module_name)

def main() -> None:
    """Run bot."""
    # Initialize databases and start periodic tasks
    initialize_rank_db()
    initialize_loan_db()
    
    # Start the Telegram bot
    application.run_polling(drop_pending_updates=True)
    
    # Schedule periodic tasks
    shivuu.loop.create_task(periodic_rank_updates())
    shivuu.loop.create_task(periodic_loan_checks())

if __name__ == "__main__":
    # Start Flask server in a daemon thread
    threading.Thread(target=run_flask, daemon=True).start()
    
    # Start the Pyrogram client
    shivuu.start()
    
    LOGGER.info("Bot started")
    
    # Run the main bot function
    main()
