import importlib
import time
import random
import re
import asyncio
from html import escape 

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram import Update
from telegram.ext import CommandHandler, CallbackContext, MessageHandler, filters

from shivu import collection, top_global_groups_collection, group_user_totals_collection, user_collection, user_totals_collection, shivuu
from shivu import application, SUPPORT_CHAT, UPDATE_CHAT, db, LOGGER
from shivu.modules import ALL_MODULES
from shivu.modules.lrank import periodic_rank_updates, initialize_rank_db # Import 
from flask import Flask, jsonify
import threading
import nest_asyncio
app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({"status": "running", "message": "Bot is alive!"})

@app.route('/random')
def random_number():
    return jsonify({"number": random.randint(1, 50)})

def run_flask():
    app.run(host="0.0.0.0", port=7860)

nest_asyncio.apply()

for module_name in ALL_MODULES:
    imported_module = importlib.import_module("shivu.modules." + module_name)



# Start task


async def main() -> None:
    """Run bot."""
    application.run_polling(drop_pending_updates=True)
    await initialize_rank_db()  # Call both initialization functions
    await initialize_loan_db()
    shivuu.loop.create_task(periodic_rank_updates())  # Start the tasks
    shivuu.loop.create_task(periodic_loan_checks())

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start() 
    shivuu.start()
    LOGGER.info("Bot started")
    await main()

