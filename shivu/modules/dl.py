import os
import yt_dlp
from pathlib import Path
from shivu import shivuu
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message

# Set download path
DOWNLOAD_PATH = Path.home() / "Downloads" / "youtube"
DOWNLOAD_PATH.mkdir(parents=True, exist_ok=True)

# Store user choices temporarily
USER_SELECTIONS = {}

@shivuu.on_message(filters.regex(r"(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+"))
async def youtube_download_handler(client, message: Message):
    url = message.text

    try:
        # Extract video info
        ydl_opts = {'quiet': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            video_title = info['title']
            formats = info.get('formats', [])

        # Filter MP4 formats (single file, no separate audio)
        available_resolutions = {}
        for fmt in formats:
            if fmt.get('ext') == 'mp4' and fmt.get('vcodec') and fmt.get('acodec'):
                height = fmt.get('height', 0)
                available_resolutions[str(height)] = fmt['format_id']

        if not available_resolutions:
            await message.reply_text("No complete MP4 video streams found.")
            return

        # Sort resolutions in descending order
        available_resolutions = dict(sorted(available_resolutions.items(), key=lambda x: int(x[0]), reverse=True))

        # Store resolution mapping
        USER_SELECTIONS[message.chat.id] = (url, available_resolutions)

        # Send resolution selection buttons
        buttons = [
            [InlineKeyboardButton(text=f"{res}p", callback_data=f"yt_res_{res}")]
            for res in available_resolutions.keys()
        ]
        await message.reply_text(
            f"🎥 **{video_title}**\nChoose a resolution:",
            reply_markup=InlineKeyboardMarkup(buttons),
        )

    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")

@shivuu.on_callback_query(filters.regex(r"yt_res_"))
async def resolution_selected(client, query: CallbackQuery):
    chat_id = query.message.chat.id
    if chat_id not in USER_SELECTIONS:
        await query.answer("Session expired. Please send the link again.")
        return

    url, available_resolutions = USER_SELECTIONS.pop(chat_id)
    selected_res = query.data.split("_")[-1]

    await query.message.edit_text(f"⬇ Downloading in {selected_res}p...")

    # Download without FFmpeg (single MP4 file)
    ydl_opts = {
        'format': available_resolutions[selected_res],
        'outtmpl': str(DOWNLOAD_PATH / '%(title)s.%(ext)s'),
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # Find the downloaded file
        downloaded_files = list(DOWNLOAD_PATH.glob("*.mp4"))
        if not downloaded_files:
            await query.message.edit_text("❌ Download failed.")
            return

        video_file = downloaded_files[0]
        await query.message.reply_video(video=str(video_file))

        # Clean up
        os.remove(video_file)

    except Exception as e:
        await query.message.edit_text(f"❌ Error: {e}")
