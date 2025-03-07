import importlib
import time
import random
import re
import asyncio
from html import escape

try:
    import uvloop
    uvloop.install()
except ImportError:
    pass  # Fall back to default asyncio loop

from pyrogram import filters, Client
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from shivu import (
    collection, top_global_groups_collection, group_user_totals_collection,
    user_collection, user_totals_collection, shivuu,
    sudo_users, SUPPORT_CHAT, UPDATE_CHAT, db, LOGGER
)
from shivu.modules import ALL_MODULES
from shivu.modules.lrank import periodic_rank_updates, initialize_rank_db
from shivu.modules.lloan import initialize_loan_db, periodic_loan_checks
from flask import Flask, jsonify
import threading
import nest_asyncio

# Flask setup
app = Flask(__name__)
nest_asyncio.apply()

@app.route('/')
def home():
    return jsonify({"status": "running", "message": "Bot is alive!"})

@app.route('/random')
def random_number():
    return jsonify({"number": random.randint(1, 50)})

def run_flask():
    app.run(host="0.0.0.0", port=7860)

# Load modules
for module_name in ALL_MODULES:
    imported_module = importlib.import_module(f"shivu.modules.{module_name}")

# Pyrogram startup handler
@shivuu.on_message(filters.command("sex") & filters.private)
async def start_command(_, message):
    await message.reply("Bot is running!")

async def main():
    # Initialize databases
    initialize_rank_db()
    initialize_loan_db()
    
    # Start periodic tasks
    asyncio.create_task(periodic_rank_updates())
    asyncio.create_task(periodic_loan_checks())
    
    # Start the client
    await client.start()
    LOGGER.info("Bot started")
    
    # Keep the client running
    await asyncio.Event().wait()

if __name__ == "__main__":
    # Start Flask in daemon thread
    threading.Thread(target=run_flask, daemon=True).start()
    
    # Run the asyncio event loop
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        LOGGER.info("Bot stopped")
