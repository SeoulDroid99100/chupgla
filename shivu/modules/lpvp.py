from shivu import shivuu, xy
from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta
import random

# PvP Configuration
PVP_CONFIG = {
    "base_reward": 0.5,  # % of opponent's size gained
    "rating_change": 25,
    "cooldown": 1800,  # 30 minutes
    "stamina_cost": 30,
    "max_attackers": 3
}

async def calculate_damage(attacker, defender):
    # Base damage formula
    base_damage = attacker['progression']['lund_size'] * 0.2
    
    # Equipment bonuses
    weapon = attacker['inventory']['equipment']['slots']['weapon']
    armor = defender['inventory']['equipment']['slots']['armor']
    
    equipment_bonus = 1.0
    if weapon:
        equipment_bonus += 0.15  # 15% damage boost for weapons
    if armor:
        equipment_bonus -= 0.10  # 10% damage reduction for armor
    
    # Critical chance (5% base)
    critical = 1.5 if random.random() < 0.05 else 1.0
    
    return base_damage * equipment_bonus * critical * random.uniform(0.9, 1.1)

async def update_ratings(winner_id, loser_id):
    # Elo-like rating system
    await xy.update_one(
        {"user_id": winner_id},
        {"$inc": {"combat_stats.rating": PVP_CONFIG['rating_change']}}
    )
    await xy.update_one(
        {"user_id": loser_id},
        {"$inc": {"combat_stats.rating": -PVP_CONFIG['rating_change']}}
    )

@shivuu.on_message(filters.command("lpvp"))
async def pvp_handler(client: shivuu, message: Message):
    user_id = message.from_user.id
    user_data = await xy.find_one({"user_id": user_id})
    
    if not user_data:
        await message.reply("❌ Account not found! Use /lstart to register.")
        return

    # Check cooldown
    last_pvp = user_data.get('combat_stats', {}).get('last_pvp')
    if last_pvp and (datetime.now() - last_pvp).seconds < PVP_CONFIG['cooldown']:
        remaining = PVP_CONFIG['cooldown'] - (datetime.now() - last_pvp).seconds
        await message.reply(f"⏳ PvP cooldown active! Try again in {remaining} seconds.")
        return

    # Check stamina
    if user_data.get('progression', {}).get('stamina', 0) < PVP_CONFIG['stamina_cost']:
        await message.reply("❌ Not enough stamina! Rest and try again later.")
        return

    # Challenge logic
    if len(message.command) > 1:
        target = message.command[1]
        try:
            target_user = await client.get_users(target)
            if target_user.id == user_id:
                await message.reply("❌ You can't battle yourself!")
                return
                
            # Send challenge request
            buttons = InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Accept", callback_data=f"pvp_accept_{user_id}"),
                 InlineKeyboardButton("❌ Decline", callback_data="pvp_decline")]
            ])
            
            await message.reply(
                f"⚔️ {target_user.mention}, you've been challenged by {message.from_user.mention}!\n"
                "Do you accept this Lund battle?",
                reply_markup=buttons
            )
            
        except Exception as e:
            await message.reply("❌ User not found!")
    else:
        # Show PvP menu
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔍 Find Opponent", callback_data="pvp_matchmake")],
            [InlineKeyboardButton("📊 Battle Stats", callback_data="pvp_stats")]
        ])
        
        await message.reply(
            "⚔️ **Lund Battle Arena**\n\n"
            "Choose an action:",
            reply_markup=buttons
        )

@shivuu.on_callback_query(filters.regex(r"^pvp_accept_(\d+)$"))
async def accept_battle(client, callback):
    challenger_id = int(callback.matches[0].group(1))
    defender_id = callback.from_user.id
    
    # Get both players' data
    challenger = await xy.find_one({"user_id": challenger_id})
    defender = await xy.find_one({"user_id": defender_id})
    
    if not challenger or not defender:
        await callback.answer("❌ Player data missing!")
        return
    
    # Calculate battle outcome
    challenger_dmg = await calculate_damage(challenger, defender)
    defender_dmg = await calculate_damage(defender, challenger)
    
    # Determine winner
    if challenger_dmg > defender_dmg:
        winner, loser = challenger, defender
    else:
        winner, loser = defender, challenger
    
    # Size transfer
    size_transfer = loser['progression']['lund_size'] * PVP_CONFIG['base_reward'] / 100
    new_winner_size = winner['progression']['lund_size'] + size_transfer
    new_loser_size = loser['progression']['lund_size'] - size_transfer
    
    # Update database
    updates = [
        (winner['user_id'], {"$inc": {"progression.lund_size": size_transfer}}),
        (loser['user_id'], {"$inc": {"progression.lund_size": -size_transfer}})
    ]
    
    for user_id, update in updates:
        await xy.update_one(
            {"user_id": user_id},
            {
                "$set": {"combat_stats.last_pvp": datetime.now()},
                "$inc": {
                    "combat_stats.pvp.wins": 1 if user_id == winner['user_id'] else 0,
                    "combat_stats.pvp.losses": 1 if user_id != winner['user_id'] else 0,
                    "progression.stamina": -PVP_CONFIG['stamina_cost']
                },
                **update
            }
        )
    
    # Update ratings
    await update_ratings(winner['user_id'], loser['user_id'])
    
    # Build battle report
    report = (
        f"⚔️ **Battle Results** ⚔️\n\n"
        f"🏆 Winner: {winner['user_info']['first_name']}\n"
        f"💥 Damage Dealt: {challenger_dmg if winner == challenger else defender_dmg:.1f}\n\n"
        f"💔 Loser: {loser['user_info']['first_name']}\n"
        f"🛡️ Damage Dealt: {defender_dmg if winner == challenger else challenger_dmg:.1f}\n\n"
        f"📈 Size Transfer: {size_transfer:.2f}cm\n"
        f"⭐ New Ratings: +{PVP_CONFIG['rating_change']}/-{PVP_CONFIG['rating_change']}"
    )
    
    await callback.edit_message_text(report)

@shivuu.on_callback_query(filters.regex(r"^pvp_decline$"))
async def decline_battle(client, callback):
    await callback.edit_message_text("❌ Battle challenge declined!")
