from shivu import shivuu, xy
from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import random
import asyncio
from datetime import datetime, timedelta

# --- Constants ---
PVP_COOLDOWN = 10  # Seconds
AI_MAX_BET = 10   # Maximum bet for AI
WIN_POINTS = 10    # Points for winning
LOSS_POINTS = -5  # Points for losing
DEFEATED_PLAYER_WIN_POINTS = 50 # Points for defeating player
DEFEATED_PLAYER_LOSS_POINTS = -25 # Points for losing to player

# --- Helper Functions ---
def small_caps_bold(text):
    """Converts text to small caps (Unicode) and bolds it."""
    small_caps_map = {
        'A': 'ᴀ', 'B': 'ʙ', 'C': 'ᴄ', 'D': 'ᴅ', 'E': 'ᴇ', 'F': 'ғ', 'G': 'ɢ',
        'H': 'ʜ', 'I': 'ɪ', 'J': 'ᴊ', 'K': 'ᴋ', 'L': 'ʟ', 'M': 'ᴍ', 'N': 'ɴ',
        'O': 'ᴏ', 'P': 'ᴘ', 'Q': 'ǫ', 'R': 'ʀ', 'S': 's', 'T': 'ᴛ', 'U': 'ᴜ',
        'V': 'ᴠ', 'W': 'ᴡ', 'X': 'x', 'Y': 'ʏ', 'Z': 'ᴢ',
        '0': '₀', '1': '₁', '2': '₂', '3': '₃', '4': '₄', '5': '₅', '6': '₆',
        '7': '₇', '8': '₈', '9': '₉',
    }
    bold_text = ''.join(small_caps_map.get(char.upper(), char) for char in text)
    return f"**{bold_text}**"

def small_caps(text):
    """Converts text to small caps (Unicode)."""
    small_caps_map = {
        'A': 'ᴀ', 'B': 'ʙ', 'C': 'ᴄ', 'D': 'ᴅ', 'E': 'ᴇ', 'F': 'ғ', 'G': 'ɢ',
        'H': 'ʜ', 'I': 'ɪ', 'J': 'ᴊ', 'K': 'ᴋ', 'L': 'ʟ', 'M': 'ᴍ', 'N': 'ɴ',
        'O': 'ᴏ', 'P': 'ᴘ', 'Q': 'ǫ', 'R': 'ʀ', 'S': 's', 'T': 'ᴛ', 'U': 'ᴜ',
        'V': 'ᴠ', 'W': 'ᴡ', 'X': 'x', 'Y': 'ʏ', 'Z': 'ᴢ',
        '0': '₀', '1': '₁', '2': '₂', '3': '₃', '4': '₄', '5': '₅', '6': '₆',
        '7': '₇', '8': '₈', '9': '₉',
    }
    return ''.join(small_caps_map.get(char.upper(), char) for char in text)


async def get_ranking(user_id: int, current_size: float) -> tuple[int, int]:
    """Gets the user's global ranking."""
    try:
        larger_users_count = await xy.count_documents({"progression.lund_size": {"$gt": current_size}})
        return larger_users_count + 1, await xy.count_documents({})
    except Exception as e:
        print(f"Error in get_ranking: {e}")
        raise

async def calculate_percentage_smaller(user_id: int, current_size: float) -> float:
    """Calculates the percentage of users with a smaller lund_size."""
    try:
        total_users = await xy.count_documents({"progression.lund_size": {"$exists": True}})
        if total_users <= 1: return 100.0
        smaller_count = await xy.count_documents({"progression.lund_size": {"$lt": current_size}})
        return round((smaller_count / (total_users - 1)) * 100, 2)
    except Exception:
        print("Error calculating percentage")
        raise

# --- Pending PvP Requests ---
pending_pvp_requests = {}  # { (challenger_id, challenged_id): {"bet": bet_amount, "message_id": msg_id} }


# --- PvP Command Handler ---
@shivuu.on_message(filters.command("pvp") & (filters.group | filters.private))
async def pvp_challenge(client: shivuu, message: Message):
    challenger_id = message.from_user.id
    challenger_data = await xy.find_one({"user_id": challenger_id})

    if not challenger_data:
        await message.reply(small_caps_bold("⌧ ᴀᴄᴄᴏᴜɴᴛ ɴᴏᴛ ғᴏᴜɴᴅ! ᴜsᴇ /ʟsᴛᴀʀᴛ ᴛᴏ ʀᴇɢɪsᴛᴇʀ."))
        return
    
    # --- Cooldown Check ---
    last_pvp_time = challenger_data.get("combat_stats", {}).get("last_pvp_time")
    if last_pvp_time:
        time_since_last_pvp = (datetime.utcnow() - last_pvp_time).total_seconds()
        if time_since_last_pvp < PVP_COOLDOWN:
            remaining_cooldown = int(PVP_COOLDOWN - time_since_last_pvp)
            await message.reply(small_caps_bold(f"⚔️ ᴄᴏᴏʟᴅᴏᴡɴ ᴀᴄᴛɪᴠᴇ! ᴛʀʏ ᴀɢᴀɪɴ ɪɴ {remaining_cooldown}s."))
            return

    # --- Check for reply and get challenged user/AI ---
    if message.reply_to_message:
        challenged_user = message.reply_to_message.from_user
        challenged_id = challenged_user.id
        challenged_data = await xy.find_one({"user_id": challenged_id})
        is_ai = False

        if not challenged_data:
            await message.reply(small_caps_bold("⌧ ᴄʜᴀʟʟᴇɴɢᴇᴅ ᴜsᴇʀ ᴅᴏᴇsɴ'ᴛ ʜᴀᴠᴇ ᴀɴ ᴀᴄᴄᴏᴜɴᴛ."))
            return
          
        if challenger_id == challenged_id:
            await message.reply(small_caps_bold("ʏᴏᴜ ᴄᴀɴɴᴏᴛ ᴄʜᴀʟʟᴇɴɢᴇ ʏᴏᴜʀsᴇʟғ!"))
            return

    else: # Challenging AI
        challenged_id = "AI"
        challenged_data = None  # AI doesn't have data
        is_ai = True
        challenged_user = None # No user object for AI

    # --- Get bet amount ---
    if len(message.command) > 1:
        try:
            bet_amount = float(message.command[1])
            if bet_amount <= 0:
                raise ValueError
        except ValueError:
            await message.reply(small_caps_bold("⌧ ɪɴᴠᴀʟɪᴅ ʙᴇᴛ ᴀᴍᴏᴜɴᴛ. ᴜsᴇ `/pvp <cm>`."))
            return
    else:
        await message.reply(small_caps_bold("⌧ ᴄᴀʟʟ ᴛʜᴇ ᴄᴏᴍᴍᴀɴᴅ ᴡɪᴛʜ ᴀ ɴᴜᴍʙᴇʀ ᴏғ ᴄᴇɴᴛɪᴍᴇᴛᴇʀs ʏᴏᴜ'ʀᴇ ᴡɪʟʟɪɴɢ ᴛᴏ ʙᴇᴛ."))
        return

    # --- AI Bet Limit ---
    if is_ai and bet_amount > AI_MAX_BET:
        await message.reply(small_caps_bold(f"⌧ ᴛʜᴇ ᴀɪ ᴄᴀɴ ᴏɴʟʏ ʙᴇᴛ ᴀ ᴍᴀxɪᴍᴜᴍ ᴏғ {AI_MAX_BET}ᴄᴍ."))
        return

    # --- Check User Bet Limit ---
    if bet_amount > challenger_data["progression"]["lund_size"] or (challenged_data and bet_amount > challenged_data["progression"]["lund_size"]):
        await message.reply(small_caps_bold("⌧ ʙᴇᴛ ᴀᴍᴏᴜɴᴛ ᴇxᴄᴇᴇᴅs ᴀᴠᴀɪʟᴀʙʟᴇ sɪᴢᴇ."))
        return
    
    # --- Create PvP Request (or proceed directly for AI) ---
    if is_ai:
        await process_pvp_battle(client, challenger_id, challenged_id, bet_amount, message) #Directly go to Battle
    else:
        request_key = (challenger_id, challenged_id)
        
        if request_key in pending_pvp_requests:
            await message.reply(small_caps_bold("⌧ ᴀ ᴘᴠᴘ ʀᴇǫᴜᴇsᴛ ɪs ᴀʟʀᴇᴀᴅʏ ᴘᴇɴᴅɪɴɢ."))
            return

        # NO EXPIRATION: Remove 'expires'
        pending_pvp_requests[request_key] = {
            "bet": bet_amount,
            "message_id": None,  # Will be updated after sending the message
        }
          
        # --- Send Confirmation Request to Challenged User ---
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ " + small_caps("Accept"), callback_data=f"pvp_accept_{challenger_id}_{bet_amount}"),
             InlineKeyboardButton("❌ " + small_caps("Reject"), callback_data=f"pvp_reject_{challenger_id}")]
        ])

        sent_message = await message.reply_to_message.reply_text(
            f"⚔️ **{small_caps_bold('PvP Challenge!')}**\n\n"
            f"{message.from_user.first_name} {small_caps('challenges you to a PvP battle!')}\n"
            f"🔥 {small_caps_bold('Bet:')} **{bet_amount}cm**\n\n"
            f"{small_caps('Do you accept?')}",
            reply_markup=keyboard
        )
          
        pending_pvp_requests[request_key]["message_id"] = sent_message.id

# --- Callback Query Handlers ---
@shivuu.on_callback_query(filters.regex(r"^pvp_(accept|reject)_(\d+)_?([\d\.]+)?$"))
async def handle_pvp_response(client: shivuu, callback_query):
    action = callback_query.data.split("_")[1]
    challenger_id = int(callback_query.data.split("_")[2])
    challenged_id = callback_query.from_user.id
    request_key = (challenger_id, challenged_id)

    # NO EXPIRATION CHECK:  Still check for existence, but don't check expiration.
    if request_key not in pending_pvp_requests:
         await callback_query.answer(small_caps("This PvP request does not exist."), show_alert=True)
         await callback_query.message.delete()  # Clean up the old message
         return


    if action == "reject":
        del pending_pvp_requests[request_key]
        await callback_query.message.edit_text(f"⚔️ {callback_query.from_user.first_name} **{small_caps_bold('rejected')}** {small_caps('the PvP challenge.')}")
        await callback_query.answer()
        return

    if action == "accept":
        bet_amount = pending_pvp_requests[request_key]["bet"]
        del pending_pvp_requests[request_key]  # Remove BEFORE processing
        await callback_query.message.delete()
        await callback_query.answer()
        await process_pvp_battle(client, challenger_id, challenged_id, bet_amount, callback_query.message)


async def process_pvp_battle(client: shivuu, challenger_id: int, challenged_id: str, bet_amount: float, message: Message):

    # --- Retrieve Data (handle possible missing data and AI) ---
    challenger_data = await xy.find_one({"user_id": challenger_id})
    challenged_data = None if challenged_id == "AI" else await xy.find_one({"user_id": challenged_id})

    if not challenger_data: #Shouldnt happen, but extra safety.
      return

    # --- Simulate Battle (Random Result) ---
    if random.random() < 0.5:  # 50% chance for challenger to win
        winner_data = challenger_data
        loser_data = challenged_data
        winner_id = challenger_id
        loser_id = challenged_id
        winner_name = challenger_data["user_info"]["first_name"]
        loser_name = "˹ᴅᴇɪꜰɪᴇᴅ ʙᴇɪɴɢ˼" if challenged_id == "AI" else challenged_data["user_info"]["first_name"]
        winner_is_ai = False
        loser_is_ai = True if challenged_id == "AI" else False

    else:
        winner_data = challenged_data if challenged_data else {"user_id": "AI", "progression": {"lund_size": AI_MAX_BET}, "combat_stats":{"pvp": {"wins": 0, "losses": 0}}}  # AI "data" if needed
        loser_data = challenger_data
        winner_id = challenged_id
        loser_id = challenger_id
        winner_name = "˹ᴅᴇɪꜰɪᴇᴅ ʙᴇɪɴɢ˼" if challenged_id == "AI" else challenged_data["user_info"]["first_name"]
        loser_name = challenger_data["user_info"]["first_name"]
        winner_is_ai = True if challenged_id == "AI" else False
        loser_is_ai = False

    
    # --- Update Stats ---
    new_winner_size = round(winner_data["progression"]["lund_size"] + bet_amount, 1) if winner_data else bet_amount
    new_loser_size = round(max(1.0, (loser_data["progression"]["lund_size"] if loser_data else AI_MAX_BET ) - bet_amount), 1)

    #Win rate calculation
    if winner_data:
      winner_total_battles = winner_data.get("combat_stats", {}).get("pvp", {}).get("wins", 0) + winner_data.get("combat_stats", {}).get("pvp", {}).get("losses", 0) +1
      winner_win_rate = round((winner_data.get("combat_stats", {}).get("pvp", {}).get("wins", 0) + 1) / winner_total_battles * 100, 2)
      winner_streak = winner_data.get("combat_stats", {}).get("current_win_streak", 0) + 1
      winner_max_streak = max(winner_data.get("combat_stats", {}).get("max_win_streak", 0), winner_streak)
    else: # AI won
      winner_total_battles = 1
      winner_win_rate = 100.0
      winner_streak = 1
      winner_max_streak = 1
      
    if loser_data:
        loser_total_battles = loser_data.get("combat_stats", {}).get("pvp", {}).get("wins", 0) + loser_data.get("combat_stats", {}).get("pvp", {}).get("losses", 0) +1
        loser_win_rate = round((loser_data.get("combat_stats", {}).get("pvp", {}).get("wins", 0)) / loser_total_battles * 100, 2)
    else:  # AI lost. Shouldn't really happen, but handle it just in case
        loser_total_battles = 1
        loser_win_rate = 0.0


    # --- Database Updates (using update_one for atomic operations) ---
    # Winner update
    if winner_id != "AI":
        await xy.update_one(
            {"user_id": winner_id},
            {
                "$set": {
                    "progression.lund_size": new_winner_size,
                    "combat_stats.last_pvp_time": datetime.utcnow(),
                    "combat_stats.pvp.wins": winner_data.get("combat_stats", {}).get("pvp", {}).get("wins", 0) + 1,
                    "combat_stats.current_win_streak": winner_streak,
                    "combat_stats.max_win_streak": winner_max_streak
                },
                 "$inc": {"combat_stats.rating": DEFEATED_PLAYER_WIN_POINTS if not winner_is_ai and not loser_is_ai else WIN_POINTS}
            }
        )
    # Loser update
    if loser_id != "AI":
        await xy.update_one(
            {"user_id": loser_id},
            {
                "$set": {
                    "progression.lund_size": new_loser_size,
                    "combat_stats.last_pvp_time": datetime.utcnow(),
                    "combat_stats.pvp.losses": loser_data.get("combat_stats", {}).get("pvp", {}).get("losses", 0) + 1,
                    "combat_stats.current_win_streak": 0
                 },
                 "$inc": {"combat_stats.rating": DEFEATED_PLAYER_LOSS_POINTS if not winner_is_ai and not loser_is_ai else LOSS_POINTS}
            }
        )

    # --- Leaderboard Positions (using aggregation for accurate ranks)---

    if winner_id != "AI":
      winner_rank, total_users = await get_ranking(winner_id, new_winner_size)
    else:
      winner_rank = "-" # AI doesnt get ranked

    if loser_id != "AI":
      loser_rank, _ = await get_ranking(loser_id, new_loser_size)
    else:
      loser_rank = "-"

    # --- Build Result Message ---
    result_message = (
        "╭━━━━━━━━━━━━━━━━━━━━━━━━━╮\n"
        f"🏆 **{small_caps_bold('Result')}** 🏆\n"
        "╰━━━━━━━━━━━━━━━━━━━━━━━━━╯\n\n"
        f"👑 **{small_caps('The winner is')}** **{winner_name}**! 🎉\n"
        f"🍆 **{small_caps('His lund is now')}** **{new_winner_size} cm** {small_caps('long!')}\n\n"
        f"💀 **{small_caps('The loser\'s one is')}** **{new_loser_size} cm**... {small_caps('too bad.')}\n"
        f"⚔️ **{small_caps_bold('The bet was')}** **{bet_amount} cm**.\n\n"
        f"📊 **{small_caps_bold('Leaderboard Rankings:')}**\n"
        f"🥇 **{winner_name}** - **{small_caps('Position:')} #{winner_rank}**\n"
        f"🥈 **{loser_name}** - **{small_caps('Position:')} #{loser_rank}**\n\n"
        f"🔥 **{small_caps('Win Stats for')} {winner_name}:**\n"
        f"✅ **{small_caps('Win Rate:')}** **{winner_win_rate}%**\n"
        f"💪 **{small_caps('Current Win Streak:')}** **{winner_streak}**\n"
        f"🚀 **{small_caps('Max Win Streak:')}** **{winner_max_streak}**\n\n"
        f"☠️ **{small_caps('Win Rate of the Loser:')}** **{loser_win_rate}%**\n"
        "══════════════════════════════\n"
        f"🔻 **{small_caps('Better luck next time...  grow bigger!')}** 🔻"
    )
    await message.reply(result_message)
