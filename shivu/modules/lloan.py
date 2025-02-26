from pyrogram import filters
from pyrogram.types import Message
from datetime import datetime, timedelta
from shivu import shivuu, lundmate_players, lundmate_loans

# Interest rate (example: 5% interest)
INTEREST_RATE = 0.05
REPAYMENT_PERIOD_HOURS = 3  # Set repayment period to 3 hours

@shivuu.on_message(filters.command("loan"))
async def loan_request(client, message: Message):
    """💸 Request a loan based on league's max loanable amount."""
    user_id = message.from_user.id
    args = message.text.split()

    if len(args) < 2:
        await message.reply_text("❌ Usage: /loan <amount>")
        return

    loan_amount = int(args[1])

    # Fetch player data
    player = await lundmate_players.find_one({"user_id": user_id})
    
    if not player:
        await message.reply_text("❌ You need to register first using /lstart.")
        return

    # Fetch player's league and max loanable amount
    league = player.get("league", "Grunt")  # Default to Grunt if no league found
    max_loanable = await get_max_loanable_amount(league)
    
    if loan_amount > max_loanable:
        await message.reply_text(f"❌ You can only borrow up to **{max_loanable} Laudacoin** based on your league!")
        return

    # Check if player already has an active loan
    existing_loan = await lundmate_loans.find_one({"user_id": user_id, "repayment_status": "pending"})
    
    if existing_loan:
        await message.reply_text("❌ You already have an active loan. Repay it first before requesting another.")
        return

    # Calculate the total repayment amount with interest
    repayment_amount = loan_amount + (loan_amount * INTEREST_RATE)
    
    # Set the loan repayment due date (e.g., 3 hours from now)
    due_date = datetime.now() + timedelta(hours=REPAYMENT_PERIOD_HOURS)

    # Insert loan details into the database
    await lundmate_loans.insert_one({
        "user_id": user_id,
        "loan_amount": loan_amount,
        "repayment_amount": repayment_amount,
        "interest_rate": INTEREST_RATE,
        "repayment_status": "pending",
        "due_date": due_date
    })

    # Add loan amount to player's Laudacoin balance
    await lundmate_players.update_one(
        {"user_id": user_id},
        {"$inc": {"laudacoin": loan_amount}}
    )

    await message.reply_text(f"✅ You have successfully taken a loan of **{loan_amount} Laudacoin**. Repay **{repayment_amount} Laudacoin** by **{due_date.strftime('%Y-%m-%d %H:%M:%S')}**.")

async def get_max_loanable_amount(league: str) -> int:
    """Fetch the maximum loanable amount based on the player's league."""
    league_limits = {
        "Grunt": 1000,
        "Brute": 2000,
        "Savage": 5000,
        "Warlord": 10000,
        "Overlord": 20000,
        "Tyrant": 50000,
        "Behemoth": 100000,
        "Colossus": 200000,
        "Godhand": 500000
    }
    
    return league_limits.get(league, 1000)  # Default to Grunt if no league or invalid league


@shivuu.on_message(filters.command("repay"))
async def repay_loan(client, message: Message):
    """💳 Repay loan with a specified amount."""
    user_id = message.from_user.id
    args = message.text.split()

    if len(args) < 2:
        await message.reply_text("❌ Usage: /repay <amount>")
        return

    repay_amount = int(args[1])

    # Fetch player data
    player = await lundmate_players.find_one({"user_id": user_id})

    if not player:
        await message.reply_text("❌ You need to register first using /lstart.")
        return

    # Fetch player's active loan
    loan = await lundmate_loans.find_one({"user_id": user_id, "repayment_status": "pending"})

    if not loan:
        await message.reply_text("❌ You have no active loan to repay.")
        return

    # Check if the player is repaying more than needed
    if repay_amount > loan["repayment_amount"]:
        await message.reply_text(f"❌ You cannot repay more than the remaining amount. Total repayment due: {loan['repayment_amount']}.")
        return

    # Deduct repayment from player's Laudacoin balance
    if player["laudacoin"] < repay_amount:
        await message.reply_text("❌ You don't have enough Laudacoin to repay the loan.")
        return

    # Update the player's balance after repayment
    await lundmate_players.update_one(
        {"user_id": user_id},
        {"$inc": {"laudacoin": -repay_amount}}
    )

    # Update loan status to 'paid'
    await lundmate_loans.update_one(
        {"user_id": user_id, "repayment_status": "pending"},
        {"$set": {"repayment_status": "paid"}}
    )

    await message.reply_text(f"✅ You have successfully repaid **{repay_amount} Laudacoin** towards your loan. Thank you!")
