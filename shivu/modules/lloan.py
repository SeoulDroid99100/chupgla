from shivu import shivuu, xy
from pyrogram import filters, enums
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta
import random
import asyncio
import logging

# --- Configuration ---
LOAN_CONFIG = {
    "max_loan_base": 5000,  # Base maximum loan amount
    "interest_rate_base": 0.15,  # Base interest rate (15%)
    "max_active_loans": 3,
}

# Time-based Loan Tiers (Duration, Interest Multiplier, Borrowing Limit Multiplier)
LOAN_TIERS = {
    "1h": {"duration": timedelta(hours=1), "interest_mult": 0.5, "borrow_limit_mult": 2.0},
    "3h": {"duration": timedelta(hours=3), "interest_mult": 0.75, "borrow_limit_mult": 1.5},
    "8h": {"duration": timedelta(hours=8), "interest_mult": 1.0, "borrow_limit_mult": 1.2},
    "24h": {"duration": timedelta(hours=24), "interest_mult": 1.25, "borrow_limit_mult": 1.0},
    "3d": {"duration": timedelta(days=3), "interest_mult": 1.5, "borrow_limit_mult": 0.8},
    "7d": {"duration": timedelta(days=7), "interest_mult": 2.0, "borrow_limit_mult": 0.5},
}

# League-based Loan Adjustments (Example - Adjust as needed)
LEAGUE_ADJUSTMENTS = {
    "Dragonborn League 🐉": {"loan_mult": 1.0, "interest_mult": 1.0},
    "Crusader's League 🛡️": {"loan_mult": 1.2, "interest_mult": 0.9},
    "Berserker King's League 🪓": {"loan_mult": 1.5, "interest_mult": 0.8},
    "Olympian Gods' League ⚡": {"loan_mult": 1.8, "interest_mult": 0.7},
    "Spartan Warlord League 🏛️": {"loan_mult": 2.0, "interest_mult": 0.6},
    "Dragonlord Overlord League 🔥": {"loan_mult": 2.5, "interest_mult": 0.5},
    "Titan Sovereign League 🗿": {"loan_mult": 3.0, "interest_mult": 0.4},
    "Divine King League 👑": {"loan_mult": 3.5, "interest_mult": 0.3},
    "Immortal Emperor League ☠️": {"loan_mult": 4.0, "interest_mult": 0.2}
}

# --- Configure logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Helper Functions ---
def small_caps_bold(text):
    """Converts text to small caps and bolds it."""
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

async def calculate_repayment(amount: float, tier: str, league: str) -> tuple:
    """Calculates the repayment amount and due date."""
    tier_data = LOAN_TIERS[tier]
    league_adj = LEAGUE_ADJUSTMENTS.get(league, {"loan_mult": 1.0, "interest_mult": 1.0})

    interest_rate = LOAN_CONFIG["interest_rate_base"] * tier_data["interest_mult"] * league_adj["interest_mult"]
    interest = amount * interest_rate
    total = amount + interest
    due_date = datetime.now() + tier_data["duration"]
    return total, due_date


async def get_user_loan_limit(user_data: dict) -> float:
    """Calculates the user's maximum loan amount."""
    level = user_data["progression"]["level"]
    league = user_data["progression"]["current_league"]
    league_adj = LEAGUE_ADJUSTMENTS.get(league, {"loan_mult": 1.0, "interest_mult": 1.0})

    return min(level * 100 * league_adj["loan_mult"], LOAN_CONFIG["max_loan_base"] * league_adj["loan_mult"])

async def check_overdue_loans(user_id: int):
    """Checks for overdue loans and applies penalties."""
    user_data = await xy.find_one({"user_id": user_id})
    if not user_data or "loans" not in user_data:
        return

    now = datetime.utcnow()
    overdue_loans = [loan for loan in user_data["loans"] if loan["due_date"] < now]

    for loan in overdue_loans:
        penalty_interest = loan["amount"] * 0.05  # 5% penalty
        new_total = loan["total"] + penalty_interest

        await xy.update_one(
            {"user_id": user_id, "loans.issued_at": loan["issued_at"]},
            {
                "$inc": {"combat_stats.rating": -10},  # Penalty
                "$set": {
                    "loans.$.total": new_total,
                    "loans.$.due_date": now + timedelta(hours=24),  # Extend due date
                    "loans.$.overdue_notified": True  # Mark as notified
                }
            }
        )

        try:
            await shivuu.send_message(
                user_id,
                f"⚠️ Your loan of {loan['amount']:.1f}LC is overdue!  A 5% penalty has been applied. New total: {new_total:.1f}LC. You have 24 hours to repay."
            )
        except Exception as e:
            logger.error(f"Error sending overdue notification to {user_id}: {e}")


async def periodic_loan_checks():
    """Periodically checks for overdue loans."""
    while True:
        try:
            all_user_ids = await xy.distinct("user_id")
            for user_id in all_user_ids:
                await check_overdue_loans(user_id)
            await asyncio.sleep(600)  # Check every 10 minutes
        except Exception as e:
            logger.exception(f"Error in periodic_loan_checks: {e}")

# --- Command Handlers ---

async def _show_main_menu(client, message, show_alert=False, alert_text=""):
    """Displays the main loan menu."""
    user_id = message.from_user.id if isinstance(message, Message) else message.from_user.id
    user_data = await xy.find_one({"user_id": user_id})

    if not user_data:
        text = small_caps_bold("⌧ ᴀᴄᴄᴏᴜɴᴛ ɴᴏᴛ ғᴏᴜɴᴅ! ᴜsᴇ /ʟsᴛᴀʀᴛ ᴛᴏ ʀᴇɢɪsᴛᴇʀ.")
        if isinstance(message, Message):
            await message.reply(text)
        else:
            await message.edit_text(text)
        return

    buttons = [
        [InlineKeyboardButton("💵 ᴛᴀᴋᴇ ʟᴏᴀɴ", callback_data="loan_new")],
        [InlineKeyboardButton("💰 ʀᴇᴘᴀʏ", callback_data="loan_repay")],
        [InlineKeyboardButton("📜 ʟᴏᴀɴ sᴛᴀᴛᴜs", callback_data="loan_status")],
    ]
    keyboard = InlineKeyboardMarkup(buttons)
    text = small_caps_bold("ʟᴏᴀɴ sʏsᴛᴇᴍ")

    if isinstance(message, Message):
        await message.reply(text, reply_markup=keyboard)
    else:
        await message.edit_text(text, reply_markup=keyboard)

    if show_alert:
        await client.answer_callback_query(message.id, text=alert_text, show_alert=True)

@shivuu.on_message(filters.command("lloan"))
async def loan_handler(client: shivuu, message: Message):
    """Handles the /lloan command."""
    await _show_main_menu(client, message)


async def _build_loan_list_response(loans, page, total_pages):
    """Builds the loan list response string."""
    response = [small_caps_bold("ᴀᴄᴛɪᴠᴇ ʟᴏᴀɴs") + f" (ᴘᴀɢᴇ {page+1}/{total_pages})\n"]
    for loan in loans:
        remaining = loan["due_date"] - datetime.utcnow()
        if remaining.total_seconds() < 0:
            time_str = small_caps_bold("ᴏᴠᴇʀᴅᴜᴇ!")
        else:
            time_str = f"{remaining.days}d {remaining.seconds//3600}h remaining"
        response.append(
            f"• {loan['amount']:.1f}ʟᴄ → ʀᴇᴘᴀʏ {loan['total']:.1f}ʟᴄ\n"
            f"   ⏳ {time_str}"
        )
    return "\n".join(response)

async def show_loan_status(client, message, user_data, page=0):
    """Shows the user's loan status."""
    active_loans = user_data.get("loans", [])
    total_loans = len(active_loans)
    total_pages = (total_loans + 4) // 5  # 5 loans per page

    if total_loans == 0:
        buttons = [[InlineKeyboardButton("« ʙᴀᴄᴋ", callback_data="loan_main")]]
        await message.edit_text(small_caps_bold("ɴᴏ ᴀᴄᴛɪᴠᴇ ʟᴏᴀɴs"), reply_markup=InlineKeyboardMarkup(buttons))
        return

    start = page * 5
    end = min((page + 1) * 5, total_loans)
    current_page_loans = active_loans[start:end]

    response_text = await _build_loan_list_response(current_page_loans, page, total_pages)

    buttons = []
    if total_pages > 1:
        if page > 0:
            buttons.append([InlineKeyboardButton("« ᴘʀᴇᴠ", callback_data=f"loan_status_{page - 1}")])
        if page < total_pages - 1:
            buttons.append([InlineKeyboardButton("ɴᴇxᴛ »", callback_data=f"loan_status_{page + 1}")])
    buttons.append([InlineKeyboardButton("« ʙᴀᴄᴋ", callback_data="loan_main")])  # Back button
    reply_markup = InlineKeyboardMarkup(buttons)

    await message.edit_text(response_text, reply_markup=reply_markup)


@shivuu.on_callback_query(filters.regex(r"^loan_(new|repay|main|amount|status)(?:_([a-zA-Z0-9\.]+))?(?:_([\d\.]+))?$"))
async def loan_callbacks(client: shivuu, callback_query):
    """Handles callback queries for loan interactions."""
    parts = callback_query.data.split("_")
    action = parts[1]
    user_id = callback_query.from_user.id
    user_data = await xy.find_one({"user_id": user_id})

    if not user_data:
        await callback_query.answer(small_caps_bold("⌧ ᴀᴄᴄᴏᴜɴᴛ ɴᴏᴛ ғᴏᴜɴᴅ! ᴜsᴇ /ʟsᴛᴀʀᴛ ᴛᴏ ʀᴇɢɪsᴛᴇʀ."), show_alert=True)
        return

    if action == "main":
        await _show_main_menu(client, callback_query.message)
        return

    elif action == "status":
        page = int(parts[2]) if len(parts) > 2 else 0
        await show_loan_status(client, callback_query.message, user_data, page)
        return

    elif action == "new":
        if len(user_data.get("loans", [])) >= LOAN_CONFIG["max_active_loans"]:
            await callback_query.answer(small_caps_bold("⌧ ᴍᴀx ᴀᴄᴛɪᴠᴇ ʟᴏᴀɴs ʀᴇᴀᴄʜᴇᴅ!"), show_alert=True)
            return

        loan_limit = await get_user_loan_limit(user_data)

        buttons = []
        for tier_id, tier_data in LOAN_TIERS.items():
            amount = min(loan_limit * tier_data["borrow_limit_mult"], LOAN_CONFIG["max_loan_base"])
            total_repayment, _ = await calculate_repayment(amount, tier_id, user_data["progression"]["current_league"])
            button_text = f"{tier_id} - {amount:.1f}ʟᴄ (ʀᴇᴘᴀʏ: {total_repayment:.1f}ʟᴄ)"
            buttons.append([InlineKeyboardButton(button_text, callback_data=f"loan_amount_{tier_id}_{amount:.1f}")])
        buttons.append([InlineKeyboardButton("« ʙᴀᴄᴋ", callback_data="loan_main")])

        await callback_query.edit_message_text(
            f"{small_caps_bold('ɴᴇᴡ ʟᴏᴀɴ ᴏғғᴇʀs')}\n\n"
            f"{small_caps_bold('ᴍᴀx ᴀᴠᴀɪʟᴀʙʟᴇ:')} {loan_limit:.1f}ʟᴄ\n"
            f"{small_caps_bold('ᴄʜᴏᴏsᴇ ᴀ ʟᴏᴀɴ ᴛɪᴇʀ:')}",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return

    elif action == "amount":
        tier_id = parts[2]
        amount_str = parts[3]
        amount = float(amount_str)

        if tier_id not in LOAN_TIERS:
            await callback_query.answer(small_caps_bold("ɪɴᴠᴀʟɪᴅ ʟᴏᴀɴ ᴛɪᴇʀ!"), show_alert=True)
            return

        total, due_date = await calculate_repayment(amount, tier_id, user_data["progression"]["current_league"])

        await xy.update_one(
            {"user_id": user_id},
            {
                "$push": {"loans": {
                    "amount": amount,
                    "total": total,
                    "due_date": due_date,
                    "issued_at": datetime.utcnow(),
                    "tier": tier_id,
                    "overdue_notified": False
                }},
                "$inc": {"economy.wallet": amount}  # Add to WALLET
            },
            upsert=True
        )

        await callback_query.edit_message_text(
            small_caps_bold("✅ ʟᴏᴀɴ ᴀᴘᴘʀᴏᴠᴇᴅ!\n\n") +
            small_caps_bold("💵 ʀᴇᴄᴇɪᴠᴇᴅ:") + f" {amount:.1f}ʟᴄ\n" +
            small_caps_bold("📅 ʀᴇᴘᴀʏ") + f" {total:.1f}ʟᴄ ʙʏ {due_date.strftime('%Y-%m-%d %H:%M')}"
        )
        return

    elif action == "repay":
        if not user_data.get("loans"):
            await callback_query.answer(small_caps_bold("⌧ ɴᴏ ᴀᴄᴛɪᴠᴇ ʟᴏᴀɴs!"), show_alert=True)
            return

        active_loans = user_data.get("loans", [])
        total_loans = len(active_loans)
        total_pages = (total_loans + 4) // 5
        page = int(parts[2]) if len(parts) > 2 else 0

        if total_loans == 0:
            buttons = [[InlineKeyboardButton("« ʙᴀᴄᴋ", callback_data="loan_main")]]
            await callback_query.edit_message_text(small_caps_bold("ɴᴏ ᴀᴄᴛɪᴠᴇ ʟᴏᴀɴs"), reply_markup=InlineKeyboardMarkup(buttons))
            return

        start = page * 5
        end = min((page + 1) * 5, total_loans)
        current_page_loans = active_loans[start:end]

        buttons = []
        for idx, loan in enumerate(current_page_loans, start + 1):
            remaining = loan['due_date'] - datetime.utcnow()
            time_str = f"{remaining.days}d {remaining.seconds//3600}h" if remaining.total_seconds() > 0 else small_caps_bold("ᴏᴠᴇʀᴅᴜᴇ!")
            buttons.append([InlineKeyboardButton(
                f"{idx}. {loan['amount']:.1f}ʟᴄ (ʀᴇᴘᴀʏ {loan['total']:.1f}ʟᴄ) - {time_str}",
                callback_data=f"loan_repay_select_{start + idx - 1}"
            )])
        if total_pages > 1:
            if page > 0:
                buttons.append([InlineKeyboardButton("« ᴘʀᴇᴠ", callback_data=f"loan_repay_{page - 1}")])
            if page < total_pages - 1:
                buttons.append([InlineKeyboardButton("ɴᴇxᴛ »", callback_data=f"loan_repay_{page + 1}")])
        buttons.append([InlineKeyboardButton("« ʙᴀᴄᴋ", callback_data="loan_main")])

        await callback_query.edit_message_text(
            small_caps_bold("sᴇʟᴇᴄᴛ ʟᴏᴀɴ ᴛᴏ ʀᴇᴘᴀʏ:"),
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return

    elif action == "select":
        loan_index = int(parts[2])
        selected_loan = user_data["loans"][loan_index]

        buttons = [
            [InlineKeyboardButton(small_caps_bold("✅ ᴄᴏɴғɪʀᴍ ʀᴇᴘᴀʏᴍᴇɴᴛ"), callback_data=f"loan_repay_confirm_{loan_index}")],
            [InlineKeyboardButton(small_caps_bold("❌ ᴄᴀɴᴄᴇʟ"), callback_data="loan_repay")]
        ]
        await callback_query.edit_message_text(
            small_caps_bold("⚠️ ᴄᴏɴғɪʀᴍ ʀᴇᴘᴀʏᴍᴇɴᴛ ᴏғ") + f" {selected_loan['total']:.1f}ʟᴄ ғᴏʀ ʟᴏᴀɴ ɪssᴜᴇᴅ ᴀᴛ {selected_loan['issued_at'].strftime('%Y-%m-%d %H:%M')}?",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return

    elif action == "confirm":
        loan_index = int(parts[2])
        loan = user_data["loans"][loan_index]

        # Check sufficient funds *before* attempting repayment
        if user_data["economy"]["wallet"] < loan["total"]:
            await callback_query.answer(small_caps_bold("⌧ ɪɴsᴜғғɪᴄɪᴇɴᴛ ғᴜɴᴅs ᴛᴏ ʀᴇᴘᴀʏ ʟᴏᴀɴ!"), show_alert=True)
            return

        # Repay the loan
        await xy.update_one(
            {"user_id": user_id},
            {
                "$inc": {"economy.wallet": -loan["total"]},
                "$pull": {"loans": {"issued_at": loan["issued_at"]}},
            }
        )
        await callback_query.edit_message_text(
            small_caps_bold("✅ ʟᴏᴀɴ ʀᴇᴘᴀɪᴅ!\n") +
            small_caps_bold("💸 ᴀᴍᴏᴜɴᴛ:") + f" {loan['total']:.1f}ʟᴄ\n"
        )
        return

    await callback_query.answer() #Always

# --- Database Initialization ---
async def initialize_loan_db():
    await xy.create_index([("loans.due_date", 1)])
