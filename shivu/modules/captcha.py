from io import BytesIO
from contextlib import suppress
from captcha.image import ImageCaptcha
from shivu import shivuu, xy
from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import random
import asyncio
from datetime import datetime, timedelta

# ⚙️ ᴄᴏɴғɪɢ
C_ᴅᴜʀᴀᴛɪᴏɴ = 15
B_ʀᴇᴡᴀʀᴅ = 100
L_ᴛʜʀᴇsʜᴏʟᴅs = [1000, 5000, 15000, 30000, 50000]
P_ᴄᴏsᴛs = {"ʜɪɴᴛ": 200, "ᴛɪᴍᴇ": 300, "ᴍᴜʟᴛ": 500}

# ɢʟᴏʙᴀʟ sᴛᴀᴛᴇ
active_captchas = {}
user_powerups = {}
captcha_lock = asyncio.Lock()
image_captcha = ImageCaptcha()

# ⌗ ʟᴇᴠᴇʟ ᴄᴀʟᴄ
async def get_user_level(user_id):
    user = await xy.find_one({"user_id": user_id})
    return sum(1 for t in L_ᴛʜʀᴇsʜᴏʟᴅs if user["economy"]["wallet"] >= t) if user else 0

# ⎇ ᴘᴏᴡᴇʀᴜᴘ ɪɴᴛᴇʀғᴀᴄᴇ
@shivuu.on_message(filters.command("powerup"))
async def powerup_interface(_, m):
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"⌞ ʜɪɴᴛ ➠ {P_ᴄᴏsᴛs['ʜɪɴᴛ']}⌝", "hint"),
         InlineKeyboardButton(f"⌞ ᴛɪᴍᴇ+ ➠ {P_ᴄᴏsᴛs['ᴛɪᴍᴇ']}⌝", "time")],
        [InlineKeyboardButton(f"⌞ x2 ᴍᴜʟᴛ ➠ {P_ᴄᴏsᴛs['ᴍᴜʟᴛ']}⌝", "multiplier")]
    ])
    await m.reply("⎇ ᴘᴏᴡᴇʀᴜᴘ sᴛᴏʀᴇ\n⎯⎯⎯⎯⎯⎯⎯⎯⎯", reply_markup=kb)

@shivuu.on_callback_query()
async def handle_powerups(_, query):
    u_id = query.from_user.id
    async with captcha_lock:
        if u_id in user_powerups:
            await query.answer("⚠ ᴘʀᴇᴠ ᴘᴏᴡᴇʀᴜᴘ ᴀᴄᴛɪᴠᴇ\n⎯⎯⎯⎯⎯⎯⎯⎯⎯\nᴡᴀɪᴛ ғᴏʀ ᴇxᴘɪʀʏ")
            return

    u_data = await xy.find_one({"user_id": u_id})
    choice = query.data
    cost = P_ᴄᴏsᴛs.get(choice, 0)
    
    if u_data["economy"]["wallet"] < cost:
        await query.answer("⌞ ɪɴsᴜғғɪᴄɪᴇɴᴛ ғᴜɴᴅs")
        return

    async with captcha_lock:
        user_powerups[u_id] = {
            "type": choice,
            "expiry": datetime.utcnow() + timedelta(minutes=10)
        }
    
    await xy.update_one({"user_id": u_id}, {"$inc": {"economy.wallet": -cost}})
    await query.answer(f"⌞ {choice} ᴀᴄᴛɪᴠᴀᴛᴇᴅ\n⎯⎯⎯⎯⎯⎯⎯⎯⎯\nᴇxᴘɪʀᴇs ɪɴ 10ᴍ")

# ✨ ᴍᴀɪɴ ᴄᴀᴘᴛᴄʜᴀ
@shivuu.on_message(filters.command("io") & filters.group)
async def init_captcha(_, m):
    c_id = m.chat.id
    async with captcha_lock:
        if c_id in active_captchas:
            return await m.reply("⚠ ᴀᴄᴛɪᴠᴇ ᴄᴀᴘᴛᴄʜᴀ ᴇxɪsᴛs\n⎯⎯⎯⎯⎯⎯⎯⎯⎯\nᴛʀʏ ᴀɢᴀɪɴ ɪɴ 15s")
    
    u_level = await get_user_level(m.from_user.id)
    code = generate_captcha_code(u_level)
    img = create_captcha_image(code)
    
    hint = f"\n⌞ ʜɪɴᴛ: {code[0]}...⌝" if random.random() < 0.3 else ""
    
    sent = await m.reply_photo(
        photo=img,
        caption=f"⎇ ᴄᴀᴘᴛᴄʜᴀ ᴄʜᴀʟʟᴇɴɢᴇ{hint}\n⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
                f"⌞ ᴅᴜʀᴀᴛɪᴏɴ: {C_ᴅᴜʀᴀᴛɪᴏɴ}s\n"
                f"⌞ ʟᴇᴠᴇʟ: {u_level}\n"
                f"⌞ ʀᴇᴘʟʏ ᴡɪᴛʜ ᴄᴏᴅᴇ"
    )
    
    async with captcha_lock:
        active_captchas[c_id] = {
            "code": code,
            "start": datetime.utcnow(),
            "msg_id": sent.id,
            "solvers": []
        }
    
    await asyncio.sleep(C_ᴅᴜʀᴀᴛɪᴏɴ)
    async with captcha_lock:
        with suppress(KeyError):
            await sent.edit_caption("⌞ ᴄᴀᴘᴛᴄʜᴀ ᴇxᴘɪʀᴇᴅ\n⎯⎯⎯⎯⎯⎯⎯⎯⎯")
            del active_captchas[c_id]

@shivuu.on_message(filters.text & filters.group)
async def verify_solve(_, m):
    c_id = m.chat.id
    u_id = m.from_user.id
    guess = m.text.strip()
    
    async with captcha_lock:
        captcha_data = active_captchas.get(c_id)
        if not captcha_data:
            return
        
        if u_id in captcha_data["solvers"]:
            return
        
        actual = captcha_data["code"]
        is_correct = guess == actual
        captcha_data["solvers"].append(u_id)
    
    # ʀᴇᴡᴀʀᴅ ʟᴏɢɪᴄ
    if is_correct:
        reward = B_ʀᴇᴡᴀʀᴅ * (1 + (await get_user_level(u_id)) * 0.5)
        
        async with captcha_lock:
            with suppress(KeyError):
                # ʀᴇᴍᴏᴠᴇ ᴘᴏᴡᴇʀᴜᴘ
                mult = 2 if user_powerups.pop(u_id, None) else 1
                reward *= mult
                
                # ᴄʟᴇᴀɴᴜᴘ ᴄᴀᴘᴛᴄʜᴀ
                del active_captchas[c_id]
        
        await xy.update_one(
            {"user_id": u_id},
            {"$inc": {"economy.wallet": reward}},
            upsert=True
        )
        await m.reply(f"⌞ sᴜᴄᴄᴇss!\n⎯⎯⎯⎯⎯⎯⎯⎯⎯\n+{reward} ᴄᴏɪɴs")
    else:
        await m.reply(f"⌞ ɪɴᴄᴏʀʀᴇᴄᴛ\n⎯⎯⎯⎯⎯⎯⎯⎯⎯\nᴛʀʏ ᴀɢᴀɪɴ ᴡ/ ʜɪɴᴛ: {actual[:len(actual)//2]}...")

# ғɪʟᴇ ʜᴇʟᴘᴇʀs
def generate_captcha_code(level=0):
    chars = "qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM1234567890@#₹_&-+()/*:;!?,."
    length = 6 + min(level // 3, 3)
    return "".join(random.choices(chars, k=length))

def create_captcha_image(code):
    img = image_captcha.generate_image(code)
    img_bytes = BytesIO()
    img.save(img_bytes, "PNG")
    img_bytes.seek(0)
    img_bytes.name = "captcha.png"
    return img_bytes

# ⌗ ʟᴇᴠᴇʟ ᴄᴏᴍᴍᴀɴᴅ
@shivuu.on_message(filters.command("level"))
async def check_level(_, m):
    u_level = await get_user_level(m.from_user.id)
    next_level = L_ᴛʜʀᴇsʜᴏʟᴅs[u_level] if u_level < len(L_ᴛʜʀᴇsʜᴏʟᴅs) else "ᴍᴀx"
    await m.reply(f"⌞ ʏᴏᴜʀ ʟᴇᴠᴇʟ: {u_level}\n⎯⎯⎯⎯⎯⎯⎯⎯⎯\nɴᴇxᴛ ᴀᴛ: {next_level}")
