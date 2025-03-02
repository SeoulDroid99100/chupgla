from pyrogram import filters
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from shivu import shivuu
import importlib

def register_handlers():
    handlers = importlib.import_module("shivu.modules.lpvp.handlers")
    
    # Command handler for /lpvp
    shivuu.add_handler(
        MessageHandler(
            handlers.pvp_challenge,
            filters.command("lpvp") & filters.group
        ),
        group=1
    )
    
    # Callback handlers for PVP actions
    shivuu.add_handler(
        CallbackQueryHandler(
            handlers.pvp_callback,
            filters.regex(r"^pvp_(accept|decline):(\d+):(\d+)$")
        ),
        group=1
    )
    
    shivuu.add_handler(
        CallbackQueryHandler(
            handlers.handle_pokemon_selection,
            filters.regex(r"^select_pokemon:(\d+):(\d+):(\d+):(\d+)$")
        ),
        group=1
    )
    
    shivuu.add_handler(
        CallbackQueryHandler(
            handlers.handle_move_selection,
            filters.regex(r"^select_move:(\d+):(\d+):(\d+):(\d+)$")
        ),
        group=1
    )
    
    shivuu.add_handler(
        CallbackQueryHandler(
            handlers.handle_no_pp,
            filters.regex(r"^no_pp$")
        ),
        group=1
    )
    
    shivuu.add_handler(
        CallbackQueryHandler(
            handlers.handle_switch_pokemon,
            filters.regex(r"^switch_pokemon:(\d+):(\d+):(\d+)$")
        ),
        group=1
    )
    
    shivuu.add_handler(
        CallbackQueryHandler(
            handlers.confirm_switch,
            filters.regex(r"^confirm_switch:(\d+):(\d+):(\d+):(\d+)$")
        ),
        group=1
    )

register_handlers()
