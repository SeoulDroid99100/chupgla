from io import BytesIO
from contextlib import suppress
from captcha.image import ImageCaptcha
from shivu import shivuu, xy
from pyrogram import filters
from pyrogram.types import Message
import random
import asyncio
from datetime import datetime

# ⚙️ Config
C_DURATION = 15
B_REWARD = 100
L_THRESHOLDS = [1000, 5000, 15000, 30000, 50000]

# Global state
active_captchas = {}
captcha_lock = asyncio.Lock()
image_captcha = ImageCaptcha()

# Level calculation
async def get_user_level(user_id):
    user = await xy.find_one({"user_id": user_id})
    return sum(1 for t in L_THRESHOLDS if user["economy"]["wallet"] >= t) if user else 0

# Main captcha
@shivuu.on_message(filters.command("io") & filters.group)
async def init_captcha(_, m: Message):
    c_id = m.chat.id
    async with captcha_lock:
        if c_id in active_captchas:
            return await m.reply("⚠ Active captcha exists\nTry again in 15s")
    
    if not m.from_user:
        return
    
    u_level = await get_user_level(m.from_user.id)
    code = generate_captcha_code(u_level)
    img = create_captcha_image(code)
    
    sent = await m.reply_photo(
        photo=img,
        caption=f"🔒 CAPTCHA CHALLENGE\n⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
                f"⌞ Duration: {C_DURATION}s\n"
                f"⌞ Level: {u_level}\n"
                f"⌞ Reply with: c [your answer]"
    )
    
    async with captcha_lock:
        active_captchas[c_id] = {
            "code": code,
            "start": datetime.utcnow(),
            "msg_id": sent.id,
            "solvers": []
        }
    
    await asyncio.sleep(C_DURATION)
    async with captcha_lock:
        with suppress(KeyError):
            await sent.edit_caption("⌞ Captcha expired")
            del active_captchas[c_id]

@shivuu.on_message(filters.regex(r'^c\s+') & filters.group)
async def verify_solve(_, m: Message):
    if not m.from_user:
        return
    
    c_id = m.chat.id
    u_id = m.from_user.id
    guess = m.text.split(" ", 1)[1].strip()

    async with captcha_lock:
        captcha_data = active_captchas.get(c_id)
        if not captcha_data:
            return
        
        if u_id in captcha_data["solvers"]:
            return
        
        actual = captcha_data["code"]
        is_correct = guess == actual
        captcha_data["solvers"].append(u_id)
    
    if is_correct:
        reward = B_REWARD * (1 + (await get_user_level(u_id)) * 0.5)
        
        async with captcha_lock:
            with suppress(KeyError):
                del active_captchas[c_id]
        
        await xy.update_one(
            {"user_id": u_id},
            {"$inc": {"economy.wallet": reward}},
            upsert=True
        )
        await m.reply(f"✅ Correct! +{reward} coins")
    else:
        # Only show first character as hint
        hint = actual[0] + "..." if len(actual) > 1 else actual[0]
        await m.reply(f"❌ Incorrect\nFirst character: {hint}")

# Helpers
def generate_captcha_code(level=0):
    chars = "qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM1234567890"
    length = 6 + min(level // 3, 3)
    return "".join(random.choices(chars, k=length))

def create_captcha_image(code):
    img = image_captcha.generate_image(code)
    img_bytes = BytesIO()
    img.save(img_bytes, "PNG")
    img_bytes.seek(0)
    img_bytes.name = "captcha.png"
    return img_bytes

# Level command
@shivuu.on_message(filters.command("level"))
async def check_level(_, m: Message):
    u_level = await get_user_level(m.from_user.id)
    next_level = L_THRESHOLDS[u_level] if u_level < len(L_THRESHOLDS) else "MAX"
    await m.reply(f"⌞ Your level: {u_level}\nNext at: {next_level}")
