from pyrogram import filters
from pyrogram.types import Message
from shivu import shivuu, lundmate_players, lundmate_pvp, lundmate_loans

@shivuu.on_message(filters.command(["lprofile", "profile"]) & filters.private)
async def view_profile(client, message: Message):
    user_id = message.from_user.id
    player = await lundmate_players.find_one({"user_id": user_id})

    if not player:
        await message.reply_text("❌ You haven't started yet! Use /lstart to begin.")
        return

    # Fetch PvP stats
    pvp_stats = await lundmate_pvp.find_one({"user_id": user_id}) or {"wins": 0, "losses": 0}

    # Fetch Loan status
    loan_info = await lundmate_loans.find_one({"user_id": user_id}) or {"debt": 0, "loans_taken": 0}

    # Profile display
    profile_text = (
        f"👤 **{player['name']}'s Profile**\n"
        f"📏 **Lund Size:** {player['lund_size']} cm\n"
        f"🏆 **League:** {player['league']}\n"
        f"💰 **Laudacoin:** {player['laudacoin']} 🪙\n"
        f"⚔️ **PvP Wins:** {pvp_stats['wins']} | **Losses:** {pvp_stats['losses']}\n"
        f"🏦 **Debt:** {loan_info['debt']} | **Loans Taken:** {loan_info['loans_taken']}\n"
    )

    await message.reply_text(profile_text)
