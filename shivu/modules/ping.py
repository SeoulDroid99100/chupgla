from pyrogram import filters
import time

from shivu import shivuu as client, sudo_users

@client.on_message(filters.command("ping"))
async def ping(_, message):
    if str(message.from_user.id) not in sudo_users:
        await message.reply("Nouu.. its Sudo user's Command..")
        return

    start = time.time()
    msg = await message.reply("Pong!")
    end = time.time()
    elapsed = round((end - start) * 1000, 3)
    await msg.edit(f"Pong! {elapsed}ms")
