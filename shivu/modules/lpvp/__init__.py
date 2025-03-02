from pyrogram import filters
from shivu import shivuu
# Import all handler functions from handlers.py, and battle manager.
import importlib

def register_handlers():
    # Dynamically import handlers to avoid circular dependency issues.
    handlers = importlib.import_module("shivu.modules.lpvp.handlers")
    shivuu.add_handler(filters.command("lpvp") & filters.group, group=1)(handlers.pvp_challenge)
    shivuu.add_handler(filters.callback_query(filters.regex(r"^pvp_(accept|decline):(\d+):(\d+)$")), group=1)(handlers.pvp_callback)
    shivuu.add_handler(filters.callback_query(filters.regex(r"^select_pokemon:(\d+):(\d+):(\d+):(\d+)$")), group=1)(handlers.handle_pokemon_selection)
    shivuu.add_handler(filters.callback_query(filters.regex(r"^select_move:(\d+):(\d+):(\d+):(\d+)$")), group=1)(handlers.handle_move_selection)
    shivuu.add_handler(filters.callback_query(filters.regex(r"^no_pp$")), group=1)(handlers.handle_no_pp)
    shivuu.add_handler(filters.callback_query(filters.regex(r"^switch_pokemon:(\d+):(\d+):(\d+)$")), group=1)(handlers.handle_switch_pokemon)
    shivuu.add_handler(filters.callback_query(filters.regex(r"^confirm_switch:(\d+):(\d+):(\d+):(\d+)$")), group=1)(handlers.confirm_switch)

register_handlers()
