import os
import json
import requests
import img2pdf
from PIL import Image
from io import BytesIO
from collections import defaultdict
from shivu import shivuu
from fake_useragent import UserAgent
from concurrent.futures import ThreadPoolExecutor
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message

# Small caps conversion mapping
SMALL_CAPS_MAP = str.maketrans(
    'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ',
    'ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀsᴛᴜᴠᴡxʏᴢᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀsᴛᴜᴠᴡxʏᴢ'
)

chapter_data = defaultdict(dict)
download_status = defaultdict(dict)

def small_caps(text: str) -> str:
    return text.translate(SMALL_CAPS_MAP)

def generate_user_agent():
    return UserAgent().random

async def search_mangadex(query: str):
    headers = {'User-Agent': generate_user_agent()}
    url = f"https://api.mangadex.org/manga?title={query}&limit=1&includes[]=cover_art"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json().get('data', [])
        if data:
            manga = data[0]
            attributes = manga['attributes']
            title = attributes['title'].get('en', attributes['title'].get('ko', 'No Title'))
            
            # Get cover URL
            cover_id = next(r['id'] for r in manga['relationships'] if r['type'] == 'cover_art')
            cover_url = f"https://uploads.mangadex.org/covers/{manga['id']}/{cover_id}.jpg"
            
            return {
                "title": title,
                "start_date": attributes.get('year', 'N/A'),
                "status": attributes['status'].capitalize(),
                "score": round(attributes['rating']['bayesian'] * 10) if attributes.get('rating') else 'N/A',
                "genres": [g.capitalize() for g in attributes.get('tags', [])],
                "description": attributes['description'].get('en', 'No description available'),
                "cover_url": cover_url
            }, manga['id']
    return None, None

def get_chapters(manga_id: str):
    headers = {'User-Agent': generate_user_agent()}
    url = f"https://api.mangadex.org/manga/{manga_id}/feed?translatedLanguage[]=en&order[chapter]=asc"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return [{"id": ch['id'], "chapter": ch['attributes']['chapter']} for ch in response.json().get('data', [])]
    return []

@shivuu.on_message(filters.command("mangadex"))
async def mangadex_command(_, message: Message):
    query = " ".join(message.command[1:])
    if not query:
        return await message.reply(small_caps("provide manhwa name!"))

    manga_info, manga_id = await search_mangadex(query)
    if not manga_info:
        return await message.reply(small_caps("manhwa not found!"))

    response = [
        f"▣ {small_caps(manga_info['title'])}",
        f"▢ {small_caps('start date')} ➾ {manga_info['start_date']}",
        f"▢ {small_caps('status')} ➾ {manga_info['status']}",
        f"▢ {small_caps('score')} ➾ {manga_info['score']}",
        f"▢ {small_caps('genres')} ➾ {', '.join(manga_info['genres'][:3])}",
        f"\n▰▱▰▱▰▱▰▱▰▱▰▱▰▱▰▱",
        f"{manga_info['description']}",
        f"\n▰▱▰▱▰▱▰▱▰▱▰▱▰▱▰▱",
        f"[​]({manga_info['cover_url']})"  # Hidden image preview link
    ]

    chapters = get_chapters(manga_id)
    chapter_data[manga_id] = chapters

    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton(
            small_caps("access chapters") + " ➫",
            callback_data=f"nav:{manga_id}:0"
        )
    ]])

    await message.reply_text("\n".join(response), reply_markup=keyboard)

@shivuu.on_callback_query(filters.regex(r"^nav:(.*)"))
async def handle_navigation(_, callback: CallbackQuery):
    manga_id, page = callback.data.split(":")[1], int(callback.data.split(":")[2])
    chapters = chapter_data.get(manga_id, [])

    # Pagination setup
    page_size = 10
    total_pages = (len(chapters) + page_size - 1) // page_size
    start_idx = page * page_size
    end_idx = start_idx + page_size

    buttons = []
    for ch in chapters[start_idx:end_idx]:
        btn_text = f"▷ {small_caps(f'chapter {ch['chapter']}')}"
        buttons.append([InlineKeyboardButton(btn_text, callback_data=f"dl:{manga_id}:{ch['id']}:{ch['chapter']}")])

    # Navigation controls
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("◀", callback_data=f"nav:{manga_id}:{page-1}"))
    nav_buttons.append(InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="none"))
    if end_idx < len(chapters):
        nav_buttons.append(InlineKeyboardButton("▶", callback_data=f"nav:{manga_id}:{page+1}"))
    
    if nav_buttons:
        buttons.append(nav_buttons)

    buttons.append([
        InlineKeyboardButton(
            small_caps("return to index") + " ⇱",
            callback_data=f"nav:{manga_id}:0"
        )
    ])

    await callback.message.edit_reply_markup(InlineKeyboardMarkup(buttons))

@shivuu.on_callback_query(filters.regex(r"^dl:(.*)"))
async def handle_download(_, callback: CallbackQuery):
    manga_id, chapter_id, ch_num = callback.data.split(":")[1:4]
    
    # Fetch chapter data
    headers = {'User-Agent': generate_user_agent()}
    server_data = requests.get(
        f"https://api.mangadex.org/at-home/server/{chapter_id}",
        headers=headers
    ).json()

    # Download images
    base_url = server_data['baseUrl']
    images = server_data['chapter']['data']
    manga_title = small_caps("chapter") + f"_{ch_num}"
    
    download_status[manga_title] = {'images': {}, 'total': len(images)}
    
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = []
        for idx, img in enumerate(images):
            url = f"{base_url}/data/{server_data['chapter']['hash']}/{img}"
            futures.append(executor.submit(
                lambda: download_image(url, idx, callback.message, manga_title, ch_num)
            ))
        
        for future in futures:
            await future

    # Create PDF
    img_list = [download_status[manga_title]['images'][k] for k in sorted(download_status[manga_title]['images'])]
    pdf = img2pdf.convert([img.tobytes() for img in img_list])
    
    # Send PDF
    await callback.message.reply_document(
        document=pdf,
        file_name=f"{small_caps('chapter')}_{ch_num}.pdf"
    )
    del download_status[manga_title]

async def download_image(url: str, index: int, message: Message, title: str, ch_num: str):
    response = requests.get(url, headers={'User-Agent': generate_user_agent()})
    if response.status_code == 200:
        img = Image.open(BytesIO(response.content))
        download_status[title]['images'][index] = img
        
        progress = f"▰ {small_caps('downloading')} {index+1}/{download_status[title]['total']} ▰"
        await message.edit_text(f"`{progress}`")
        return img
    return None
