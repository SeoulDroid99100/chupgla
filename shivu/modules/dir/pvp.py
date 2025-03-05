# pvp.py - Main Entry Point
from shivu import shivuu
from pyrogram import filters, InlineKeyboardMarkup, InlineKeyboardButton
from .core.battle.engine import AsyncBattleEngine
from .core.data.species import RAYQUAZA_SPECIES
from .core.data.moves import MOVES
from .sessions.manager import battle_manager
from .handlers.ui import create_battle_message, create_action_keyboard
from typing import Dict, Optional

# Initialize with Rayquaza as default Pokémon
DEFAULT_MOVESET = [
    MOVES["Dragon Ascent"],
    MOVES["Hyper Beam"],
    MOVES["Extreme Speed"],
    MOVES["Dragon Dance"]
]

@shivuu.on_message(filters.command("test"))
async def start_pvp(client, message):
    """Initiate a PvP battle challenge"""
    challenger = message.from_user
    challenged = message.reply_to_message.from_user if message.reply_to_message else None
    
    if not challenged:
        await message.reply("Reply to a user to challenge them!")
        return
    
    # Create battle session
    session = await battle_manager.create_session(
        challenger=challenger,
        challenged=challenged,
        chat_id=message.chat.id
    )
    
    # Send challenge message
    accept_button = InlineKeyboardButton(
        "Accept Battle", 
        callback_data=f"accept_{session.id}"
    )
    
    challenge_text = (
        f"[{challenger.first_name}](tg://user?id={challenger.id}) "
        f"has challenged [{challenged.first_name}](tg://user?id={challenged.id})!\n\n"
        "Sandbox Mode: Enabled\n"
        f"✅ {challenger.first_name} is ready\n"
        f"❌ {challenged.first_name} is not ready"
    )
    
    await message.reply(
        challenge_text,
        reply_markup=InlineKeyboardMarkup([[accept_button]])
    )

@shivuu.on_callback_query(filters.regex(r"accept_(.+)"))
async def accept_battle(client, callback):
    """Handle battle acceptance"""
    session_id = callback.matches[0].group(1)
    session = await battle_manager.get_session(session_id)
    
    if callback.from_user.id != session.challenged.id:
        await callback.answer("Only the challenged player can accept!")
        return
    
    # Initialize battle engine
    session.engine = AsyncBattleEngine(
        player1=create_rayquaza(session.challenger),
        player2=create_rayquaza(session.challenged)
    )
    
    # Start first turn
    await session.start()
    await update_battle_ui(client, session)

def create_rayquaza(user):
    return AsyncPokemon(
        species=RAYQUAZA_SPECIES,
        level=100,
        moves=DEFAULT_MOVESET,
        tera_type="Flying",
        owner=user
    )

async def update_battle_ui(client, session):
    """Update battle interface with current state"""
    text = create_battle_message(session)
    keyboard = create_action_keyboard(session)
    
    if not session.message_id:
        msg = await client.send_message(
            session.chat_id,
            text,
            reply_markup=keyboard
        )
        session.message_id = msg.id
    else:
        await client.edit_message_text(
            session.chat_id,
            session.message_id,
            text,
            reply_markup=keyboard
        )

@shivuu.on_callback_query()
async def handle_battle_action(client, callback):
    """Process player actions"""
    session = await battle_manager.find_session(callback.message)
    
    if not session:
        await callback.answer("Battle not found!")
        return
    
    player = session.engine.current_player
    
    if callback.from_user.id != player.owner.id:
        await callback.answer("Not your turn!")
        return
    
    action_type, _, action_data = callback.data.partition("_")
    
    try:
        if action_type == "move":
            move_idx = int(action_data)
            await session.engine.register_move(player, move_idx)
        elif action_type == "mech":
            await session.engine.register_mechanic(player, action_data)
        
        if session.engine.both_acted:
            await process_turn(client, session)
        
        await callback.answer()
        await update_battle_ui(client, session)
    except Exception as e:
        await callback.answer(f"Error: {str(e)}")

async def process_turn(client, session):
    """Process a full battle turn"""
    # Resolve turn order and effects
    await session.engine.process_turn()
    
    # Check for battle end
    if session.engine.winner:
        await end_battle(client, session)
    else:
        session.engine.next_turn()
        await update_battle_ui(client, session)

async def end_battle(client, session):
    """Handle battle conclusion"""
    winner = session.engine.winner.owner.mention
    await client.edit_message_text(
        session.chat_id,
        session.message_id,
        f"**Battle Over!** {winner}'s Rayquaza wins!",
        reply_markup=None
    )
    await battle_manager.end_session(session.id)
