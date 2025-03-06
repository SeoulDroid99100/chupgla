import os
import yt_dlp
import ffmpeg_static
from pathlib import Path
from shivu import shivuu
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message

# Set download path
DOWNLOAD_PATH = Path.home() / "Downloads" / "youtube"
DOWNLOAD_PATH.mkdir(parents=True, exist_ok=True)

# Get ffmpeg path
FFMPEG_PATH = ffmpeg_static.get_ffmpeg_path()

# Store user choices temporarily
USER_SELECTIONS = {}

@shivuu.on_message(filters.regex(r"(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+"))
async def youtube_download_handler(client: Client, message: Message):
    url = message.text

    try:
        # Extract video info
        ydl_opts = {'quiet': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            video_title = info['title']
            formats = info.get('formats', [])

        # Define desired resolutions
        desired_resolutions = ['1080p', '720p', '480p', '360', '240', '144']
        available_resolutions = []
        resolution_mapping = {}

        for res in desired_resolutions:
            res_num = int(res[:-1])
            for fmt in formats:
                if (fmt.get('ext') == 'mp4' and fmt.get('height') == res_num and fmt.get('vcodec')):
                    available_resolutions.append(res)
                    resolution_mapping[res] = fmt['format_id']
                    break

        if not available_resolutions:
            await message.reply_text("No MP4 video streams found for 1080p, 720p, or 480p.")
            return

        # Store resolution mapping
        USER_SELECTIONS[message.chat.id] = (url, resolution_mapping)

        # Send resolution selection buttons
        buttons = [
            [InlineKeyboardButton(text=res, callback_data=f"yt_res_{res}")]
            for res in available_resolutions
        ]
        await message.reply_text(
            f"🎥 **{video_title}**\nChoose a resolution:",
            reply_markup=InlineKeyboardMarkup(buttons),
        )

    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")

@shivuu.on_callback_query(filters.regex(r"yt_res_"))
async def resolution_selected(client: Client, query: CallbackQuery):
    chat_id = query.message.chat.id
    if chat_id not in USER_SELECTIONS:
        await query.answer("Session expired. Please send the link again.")
        return

    url, resolution_mapping = USER_SELECTIONS.pop(chat_id)
    selected_res = query.data.split("_")[-1]

    await query.message.edit_text(f"⬇ Downloading in {selected_res}...")

    # Download with ffmpeg-static
    ydl_opts = {
        'format': f'bestvideo[height<={selected_res[:-1]}][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4][height<={selected_res[:-1]}]',
        'outtmpl': str(DOWNLOAD_PATH / '%(title)s.%(ext)s'),
        'merge_output_format': 'mp4',
        'ffmpeg_location': FFMPEG_PATH,
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
