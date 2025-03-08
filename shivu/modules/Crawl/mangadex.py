import os
import json
import logging
from typing import Optional, Tuple, Dict, List
from datetime import datetime
from functools import wraps
from io import BytesIO
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from shivu import shivuu
from PIL import Image
import img2pdf
import requests
from requests.exceptions import RequestException
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Small caps translation table
SMALL_CAPS_TRANS = str.maketrans(
    'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZABCDEFGHIJKLMNOPQRSTUVWXYZ',
    'ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀsᴛᴜᴠᴡxʏᴢᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀsᴛᴜᴠᴡxʏᴢᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀsᴛᴜᴠᴡxʏᴢ'
)

def small_caps(text: str) -> str:
    """Convert text to small caps using Unicode characters"""
    return text.translate(SMALL_CAPS_TRANS)

class MangaDexClient:
    BASE_URL = "https://api.mangadex.org"
    SYMBOLS = {
        'title': '⌖',
        'divider': '▰▱'*8,
        'list_item': '▢',
        'arrow': '➾',
        'nav_prev': '◀',
        'nav_next': '▶',
        'progress': '▰',
        'inactive': '▱'
    }

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self._generate_user_agent()})

    def _generate_user_agent(self) -> str:
        try:
            return UserAgent().random
        except Exception as e:
            logger.warning(f"UserAgent generation failed: {e}")
            return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

    def _handle_response(self, response: requests.Response) -> dict:
        try:
            response.raise_for_status()
            return response.json()
        except json.JSONDecodeError:
            logger.error("Failed to decode JSON response")
            return {}
        except requests.HTTPError as e:
            logger.error(f"HTTP error {e.response.status_code}")
            return {}

    def search_manga(self, query: str) -> Tuple[Optional[dict], Optional[str]]:
        try:
            response = self.session.get(
                f"{self.BASE_URL}/manga",
                params={"title": query, "limit": 1, "includes[]": ["cover_art"]}
            )
            data = self._handle_response(response)
            
            if not data.get('data'):
                return None, None

            manga = data['data'][0]
            attrs = manga.get('attributes', {})
            relationships = manga.get('relationships', [])

            # Extract cover art
            cover_art = next(
                (r for r in relationships if r.get('type') == 'cover_art'),
                {}
            )
            cover_file = cover_art.get('attributes', {}).get('fileName', '')
            cover_url = f"https://uploads.mangadex.org/covers/{manga['id']}/{cover_file}" if cover_file else ''

            # Process genres safely
            genres = []
            for tag in attrs.get('tags', []):
                if name := tag.get('attributes', {}).get('name', {}).get('en'):
                    genres.append(name.capitalize())

            return {
                'title': attrs.get('title', {}).get('en', 'Untitled'),
                'year': attrs.get('year', 'N/A'),
                'status': str(attrs.get('status', 'N/A')).capitalize(),
                'score': round(attrs.get('rating', {}).get('bayesian', 0) * 10),  # Fixed line
                'genres': genres[:5],
                'description': attrs.get('description', {}).get('en', 'No description available'),
                'cover_url': cover_url
            }, manga.get('id')

        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            return None, None

    def get_chapters(self, manga_id: str) -> List[dict]:
        try:
            response = self.session.get(
                f"{self.BASE_URL}/manga/{manga_id}/feed",
                params={"translatedLanguage[]": "en", "order[chapter]": "asc"}
            )
            data = self._handle_response(response)
            return [
                {
                    'id': ch['id'],
                    'chapter': ch['attributes'].get('chapter', 0),
                    'hash': ch['attributes'].get('hash', '')
                }
                for ch in data.get('data', [])
                if ch.get('attributes')
            ]
        except Exception as e:
            logger.error(f"Chapter fetch failed: {str(e)}")
            return []

mdex = MangaDexClient()
chapter_store = defaultdict(list)
download_tracker = defaultdict(dict)

def error_handler(func):
    @wraps(func)
    async def wrapper(client, update, *args, **kwargs):
        try:
            return await func(client, update, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {str(e)}")
            if isinstance(update, Message):
                await update.reply(small_caps("operation failed: internal error"))
            elif isinstance(update, CallbackQuery):
                await update.answer(small_caps("operation failed"), show_alert=True)
    return wrapper

@shivuu.on_message(filters.command("mangadex"))
@error_handler
async def mangadex_command(client, message: Message):
    query = " ".join(message.command[1:])
    if not query:
        return await message.reply(small_caps("provide manhwa name"))

    manga_info, manga_id = mdex.search_manga(query)
    if not manga_info or not manga_id:
        return await message.reply(small_caps("manhwa not found"))

    # Format response with symbols
    response = [
        f"{mdex.SYMBOLS['title']} **{manga_info['title']}**",
        f"{mdex.SYMBOLS['list_item']} {small_caps('start date')} {mdex.SYMBOLS['arrow']} {manga_info['year']}",
        f"{mdex.SYMBOLS['list_item']} {small_caps('status')} {mdex.SYMBOLS['arrow']} {manga_info['status']}",
        f"{mdex.SYMBOLS['list_item']} {small_caps('score')} {mdex.SYMBOLS['arrow']} {manga_info['score']}",
        f"{mdex.SYMBOLS['list_item']} {small_caps('genres')} {mdex.SYMBOLS['arrow']} {', '.join(manga_info['genres']}",
        mdex.SYMBOLS['divider'],
        manga_info['description'],
        mdex.SYMBOLS['divider']
    ]

    # Store chapters
    chapters = mdex.get_chapters(manga_id)
    chapter_store[manga_id] = chapters

    # Create keyboard with small caps
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton(
            f"{small_caps('access chapters')} ➫",
            callback_data=f"nav:{manga_id}:0"
        )
    ]])

    await message.reply_photo(
        photo=manga_info['cover_url'],
        caption="\n".join(response),
        reply_markup=keyboard
    )

@shivuu.on_callback_query(filters.regex(r"^nav:"))
@error_handler
async def handle_nav(client, callback: CallbackQuery):
    _, manga_id, page = callback.data.split(":")
    page = int(page)
    chapters = chapter_store.get(manga_id, [])
    
    PAGE_SIZE = 10
    total_pages = (len(chapters) + PAGE_SIZE - 1) // PAGE_SIZE
    start = page * PAGE_SIZE
    end = start + PAGE_SIZE
    
    buttons = []
    for ch in chapters[start:end]:
        btn_text = f"◁ {small_caps(f'chapter {ch['chapter']}')}"
        buttons.append([InlineKeyboardButton(
            btn_text,
            callback_data=f"dl:{manga_id}:{ch['id']}:{ch['chapter']}"
        )])
    
    # Navigation controls
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(
            mdex.SYMBOLS['nav_prev'],
            callback_data=f"nav:{manga_id}:{page-1}"
        ))
    
    nav_buttons.append(InlineKeyboardButton(
        f"{page+1}/{total_pages}",
        callback_data="none"
    ))
    
    if end < len(chapters):
        nav_buttons.append(InlineKeyboardButton(
            mdex.SYMBOLS['nav_next'],
            callback_data=f"nav:{manga_id}:{page+1}"
        ))
    
    if nav_buttons:
        buttons.append(nav_buttons)
    
    buttons.append([
        InlineKeyboardButton(
            f"{small_caps('return to index')} ⇱",
            callback_data=f"nav:{manga_id}:0"
        )
    ])

    await callback.message.edit_reply_markup(InlineKeyboardMarkup(buttons))

@shivuu.on_callback_query(filters.regex(r"^dl:"))
@error_handler
async def handle_download(client, callback: CallbackQuery):
    _, manga_id, ch_id, ch_num = callback.data.split(":")
    
    try:
        # Fetch chapter data
        response = mdex.session.get(f"{mdex.BASE_URL}/at-home/server/{ch_id}")
        data = mdex._handle_response(response)
        
        if not data:
            raise ValueError("Invalid chapter data")
        
        # Download images
        base_url = data['baseUrl']
        images = data['chapter']['data']
        total_images = len(images)
        
        download_tracker[ch_id] = {
            'progress': 0,
            'total': total_images,
            'images': {}
        }
        
        # Download with progress updates
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            for idx, filename in enumerate(images):
                url = f"{base_url}/data/{data['chapter']['hash']}/{filename}"
                futures.append(executor.submit(
                    self._download_image,
                    url, idx, ch_id, callback.message
                ))
            
            for future in futures:
                await future
        
        # Create PDF
        images = [download_tracker[ch_id]['images'][k] for k in sorted(download_tracker[ch_id]['images'])]
        pdf_bytes = img2pdf.convert([img.tobytes() for img in images])
        
        # Send PDF
        await callback.message.reply_document(
            document=pdf_bytes,
            file_name=f"{small_caps('chapter')}_{ch_num}.pdf"
        )
        
    except Exception as e:
        logger.error(f"Download failed: {str(e)}")
        await callback.answer(small_caps("download failed"), show_alert=True)
    finally:
        if ch_id in download_tracker:
            del download_tracker[ch_id]

async def _download_image(self, url: str, index: int, ch_id: str, message: Message):
    try:
        response = self.session.get(url)
        response.raise_for_status()
        
        img = Image.open(BytesIO(response.content))
        download_tracker[ch_id]['images'][index] = img
        
        # Update progress
        progress = (index + 1) / download_tracker[ch_id]['total']
        filled = int(progress * 10)
        progress_bar = f"{self.SYMBOLS['progress']*filled}{self.SYMBOLS['inactive']*(10-filled)}"
        
        await message.edit_text(
            f"`{progress_bar} {small_caps('downloading')} {index+1}/{download_tracker[ch_id]['total']}`"
        )
        
        return img
    except Exception as e:
        logger.warning(f"Failed to download image {index}: {str(e)}")
        return None
