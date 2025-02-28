from shivu import shivuu, xy
from pyrogram import filters
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

# --- Helper Functions ---

async def calculate_repayment(amount: float, tier: str, league: str) -> tuple:
    """Calculates the repayment amount and due date."""
    tier_data = LOAN_TIERS[tier]
    league_adj = LEAGUE_ADJUSTMENTS.get(league, {"loan_mult": 1.0, "interest_mult": 1.0})  # Default if league not found

    interest_rate = LOAN_CONFIG["interest_rate_base"] * tier_data["interest_mult"] * league_adj["interest_mult"]
    interest = amount * interest_rate
    total = amount + interest
    due_date = datetime.now() + tier_data["duration"]
    return total, due_date


async def get_user_loan_limit(user_data: dict) -> float:
    """Calculates the user's maximum loan amount based on level and league."""
    level = user_data["progression"]["level"]
    league = user_data["progression"]["current_league"]
    league_adj = LEAGUE_ADJUSTMENTS.get(league, {"loan_mult": 1.0, "interest_mult": 1.0})

    # Limit calculation (adjust as needed)
    return min(level * 100 * league_adj["loan_mult"], LOAN_CONFIG["max_loan_base"] * league_adj["loan_mult"])

async def check_overdue_loans(user_id: int):
    """Checks for overdue loans and applies penalties."""
    user_data = await xy.find_one({"user_id": user_id})
    if not user_data or "loans" not in user_data:
        return

    overdue_loans = [loan for loan in user_data["loans"] if loan["due_date"] < datetime.now()]
    for loan in overdue_loans:
      # Apply penalties (example: increase interest, reduce rating, etc.)
      penalty_interest = loan["amount"] * 0.05  # 5% penalty interest
      await xy.update_one(
          {"user_id": user_id, "loans.issued_at": loan["issued_at"]},
          {"$inc": {"loans.$.total": penalty_interest,
                    "combat_stats.rating": -10}}  # Example: reduce rating
      )

      # Send overdue notification (if not already sent)
      if not loan.get("overdue_notified"):
          try:
              await shivuu.send_message(
                  user_id,
                  f"⚠️ Your loan of {loan['amount']:.1f}LC is overdue!  Repay immediately to avoid further penalties."
              )
              await xy.update_one(
                  {"user_id": user_id, "loans.issued_at": loan["issued_at"]},
                  {"$set": {"loans.$.overdue_notified": True}}
              )
          except Exception as e:
            logging.error(f"Error sending overdue notification to {user_id}: {e}")

async def periodic_loan_checks():
    """Periodically checks for overdue loans and sends reminders."""
    while True:
        all_user_ids = await xy.distinct("user_id")
        for user_id in all_user_ids:
            await check_overdue_loans(user_id)
        await asyncio.sleep(600)  # Check every 10 minutes (adjust as needed)

# --- Command Handlers ---

@shivuu.on_message(filters.command("lloan"))
async def loan_handler(client: shivuu, message: Message):
    user_id = message.from_user.id
    user_data = await xy.find_one({"user_id": user_id})

    if not user_data:
        await message.reply("❌ Account not found! Use /lstart to register.")
        return

    args = message.command[1:]

    if not args:
        # Show loan status
        active_loans = user_data.get("loans", [])
        response = ["🏦 **Loan Status**\n"]

        for idx, loan in enumerate(active_loans, 1):
            remaining = loan["due_date"] - datetime.now()
            if remaining.total_seconds() < 0:
              time_str = "Overdue!"
            else:
              time_str = f"{remaining.days}d {remaining.seconds//3600}h remaining"
            response.append(
                f"{idx}. {loan['amount']:.1f}LC → "
                f"Repay {loan['total']:.1f}LC\n"
                f"   ⏳ {time_str}"
            )
            if not active_loans:
              response.append("✅ No Active Loans")

        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("💵 Take Loan", callback_data="loan_new"),
             InlineKeyboardButton("💰 Repay", callback_data="loan_repay")]
        ])

        await message.reply("\n".join(response), reply_markup=buttons)
        return

@shivuu.on_callback_query(filters.regex(r"^loan_new$"))
async def new_loan(client, callback):
    user_id = callback.from_user.id
    user_data = await xy.find_one({"user_id": user_id})

    # Check existing loans
    if len(user_data.get("loans", [])) >= LOAN_CONFIG["max_active_loans"]:
        return await callback.answer("❌ Max active loans reached!", show_alert=True)

    # Calculate max available loan
    loan_limit = await get_user_loan_limit(user_data)

    buttons = []
    for tier_id, tier_data in LOAN_TIERS.items():
        # Calculate potential loan amount and interest for this tier
        amount = min(loan_limit * tier_data["borrow_limit_mult"], LOAN_CONFIG["max_loan_base"])
        total_repayment, _ = await calculate_repayment(amount, tier_id, user_data["progression"]["current_league"])
        button_text = f"{tier_id} - {amount:.1f}LC (Repay: {total_repayment:.1f}LC)"
        buttons.append([InlineKeyboardButton(button_text, callback_data=f"loan_amount_{tier_id}_{amount:.1f}")])

    await callback.edit_message_text(
        f"📈 **New Loan Offers**\n\n"
        f"Max Available: {loan_limit:.1f}LC\n"
        "Choose a loan tier:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@shivuu.on_callback_query(filters.regex(r"^loan_amount_([a-zA-Z0-9]+)_([\d\.]+)$"))
async def process_loan(client, callback):
    tier_id, amount_str = callback.matches[0].groups()
    amount = float(amount_str)
    user_id = callback.from_user.id
    user_data = await xy.find_one({"user_id": user_id})

    if tier_id not in LOAN_TIERS:
        return await callback.answer("Invalid loan tier!", show_alert=True)

    total, due_date = await calculate_repayment(amount, tier_id, user_data["progression"]["current_league"])

    # Add loan to database, and add funds to WALLET
    await xy.update_one(
        {"user_id": user_id},
        {"$push": {"loans": {
            "amount": amount,
            "total": total,
            "due_date": due_date,
            "issued_at": datetime.now(),
            "tier": tier_id,
            "overdue_notified": False # Flag to track if overdue notification has been sent
        }},
         "$inc": {"economy.wallet": amount}},  # Add to WALLET
        upsert=True
    )

    await callback.edit_message_text(
        f"✅ Loan Approved!\n\n"
        f"💵 Received: {amount:.1f}LC\n"
        f"📅 Repay {total:.1f}LC by {due_date:%Y-%m-%d %H:%M}"
    )


@shivuu.on_callback_query(filters.regex(r"^loan_repay$"))
async def repay_loan(client, callback):
    user_id = callback.from_user.id
    user_data = await xy.find_one({"user_id": user_id})

    if not user_data.get("loans"):
        return await callback.answer("❌ No active loans!", show_alert=True)

    # Show active loans for repayment
    buttons = []
    for idx, loan in enumerate(user_data["loans"], 1):
        remaining = loan['due_date'] - datetime.now()
        time_str = f"{remaining.days}d {remaining.seconds//3600}h" if remaining.total_seconds() > 0 else "Overdue!"
        buttons.append([InlineKeyboardButton(
            f"{idx}. {loan['amount']:.1f}LC (Repay {loan['total']:.1f}LC) - {time_str}",
            callback_data=f"loan_repay_select_{idx-1}"  # Use index as identifier
        )])

    await callback.edit_message_text(
        "💰 **Select Loan to Repay:**",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@shivuu.on_callback_query(filters.regex(r"^loan_repay_select_(\d+)$"))
async def repay_loan_confirm(client, callback):
    loan_index = int(callback.matches[0].group(1))
    user_id = callback.from_user.id
    user_data = await xy.find_one({"user_id": user_id})
    selected_loan = user_data["loans"][loan_index]

    # Confirm repayment (optional, but good UX)
    buttons = [
        [InlineKeyboardButton("✅ Confirm Repayment", callback_data=f"loan_repay_confirm_{loan_index}")],
        [InlineKeyboardButton("❌ Cancel", callback_data="loan_repay")]  # Go back to loan list
    ]
    await callback.edit_message_text(
      f"⚠️ Confirm repayment of {selected_loan['total']:.1f}LC for loan issued at {selected_loan['issued_at']}?",
      reply_markup=InlineKeyboardMarkup(buttons)
    )

@shivuu.on_callback_query(filters.regex(r"^loan_repay_confirm_(\d+)$"))
async def repay_loan_process(client, callback):
    loan_index = int(callback.matches[0].group(1))
    user_id = callback.from_user.id
    user_data = await xy.find_one({"user_id": user_id})
    loan = user_data["loans"][loan_index]
     # Allow negative balance
    await xy.update_one(
            {"user_id": user_id},
            {
                "$inc": {"economy.wallet": -loan["total"]},
                "$pull": {"loans": {"issued_at": loan["issued_at"]}},
            }
        )
    await callback.edit_message_text(
          f"✅ Loan Repaid!\n"
          f"💸 Amount: {loan['total']:.1f}LC\n"
      )
# --- Task Integration ---
loan_task = None  # Global variable to hold the task

@shivuu.on_message(filters.command("mtask"))
async def start_loan_task(client: shivuu, message: Message):
    global loan_task
    if loan_task is None:
        loan_task = shivuu.loop.create_task(periodic_loan_checks())
        await message.reply("Loan management task started.")
    else:
        await message.reply("Loan management task is already running.")
