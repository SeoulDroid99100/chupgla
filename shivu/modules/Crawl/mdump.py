import asyncio
import logging
from io import BytesIO
from typing import Tuple, List, Dict
from functools import wraps
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from pyrogram.errors import FloodWait, QueryIdInvalid
from pyrogram.enums import ParseMode
import aiohttp
from PIL import Image
import img2pdf
import hashlib
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Assume this is imported from your main bot module
from shivu import shivuu  # Replace with your Pyrogram Client instance

# Small caps text converter (optional, for formatting)
SMALL_CAPS_TRANS = str.maketrans(
    'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ',
    'ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀsᴛᴜᴠᴝxʏᴢᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀsᴛᴜᴠᴝxʏᴢ'
)

def small_caps(text: str) -> str:
    return text.translate(SMALL_CAPS_TRANS)

# MangaDex API Client
class MangaDexClient:
    BASE_URL = "https://api.mangadex.org"

    def __init__(self):
        self.session = None

    async def _get_session(self):
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        return self.session

    async def _handle_response(self, response: aiohttp.ClientResponse) -> dict:
        try:
            response.raise_for_status()
            return await response.json()
        except (aiohttp.ContentTypeError, aiohttp.ClientResponseError) as e:
            logger.error(f"Response error: {e}")
            return {}

    async def search_manga(self, query: str, offset: int = 0, limit: int = 5) -> Tuple[List[Dict], int]:
        session = await self._get_session()
        try:
            async with session.get(
                f"{self.BASE_URL}/manga",
                params={
                    "title": query,
                    "limit": limit,
                    "offset": offset,
                    "includes[]": ["cover_art"],
                    "contentRating[]": ["safe", "suggestive", "erotica", "pornographic"],
                    "order[relevance]": "desc"
                }
            ) as response:
                data = await self._handle_response(response)
                results = []
                for manga in data.get('data', []):
                    attrs = manga.get('attributes', {})
                    relationships = manga.get('relationships', [])
                    cover_art = next((r for r in relationships if r.get('type') == 'cover_art'), None)
                    cover_file = cover_art.get('attributes', {}).get('fileName', '') if cover_art else ''
                    cover_url = f"https://uploads.mangadex.org/covers/{manga['id']}/{cover_file}" if cover_file else ''
                    results.append({
                        'id': manga['id'],
                        'title': attrs.get('title', {}).get('en', 'Untitled'),
                        'year': attrs.get('year', 'N/A'),
                        'status': str(attrs.get('status', 'N/A')).capitalize(),
                        'score': round(attrs.get('rating', {}).get('bayesian', 0) * 10),
                        'description': attrs.get('description', {}).get('en', ''),
                        'cover_url': cover_url,
                        'url': f"https://mangadex.org/title/{manga['id']}"
                    })
                return results, data.get('total', 0)
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return [], 0

    async def get_all_chapters(self, manga_id: str) -> List[Dict]:
        session = await self._get_session()
        all_chapters = []
        offset = 0
        limit = 100
        while True:
            async with session.get(
                f"{self.BASE_URL}/manga/{manga_id}/feed",
                params={
                    "translatedLanguage[]": "en",
                    "order[chapter]": "asc",
                    "includes[]": ["scanlation_group"],
                    "limit": limit,
                    "offset": offset,
                    "contentRating[]": ["safe", "suggestive", "erotica", "pornographic"]
                }
            ) as response:
                data = await self._handle_response(response)
                chapters = data.get('data', [])
                if not chapters:
                    break
                all_chapters.extend(chapters)
                offset += limit
                await asyncio.sleep(1.5)  # Rate limit compliance
        # Remove duplicates by chapter number only, ignoring scanlation groups
        seen = set()
        unique_chapters = []
        for ch in all_chapters:
            attributes = ch.get('attributes', {})
            chapter_num = str(attributes.get('chapter', 'Oneshot'))
            if chapter_num not in seen:
                seen.add(chapter_num)
                group = next((r for r in ch.get('relationships', []) if r.get('type') == 'scanlation_group'), None)
                group_name = group.get('attributes', {}).get('name', 'Unknown') if group else 'Unknown'
                unique_chapters.append({
                    'id': ch['id'],
                    'chapter': chapter_num,
                    'title': attributes.get('title', ''),
                    'group': group_name
                })
        return unique_chapters

    async def get_chapter_data(self, ch_id: str) -> Dict:
        session = await self._get_session()
        async with session.get(f"{self.BASE_URL}/at-home/server/{ch_id}") as response:
            return await self._handle_response(response)

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()

# Session Management
class SessionManager:
    def __init__(self):
        self.search_sessions = {}

    def create_search_session(self, results: List[Dict], total: int, query: str, offset: int = 0) -> str:
        session_id = hashlib.md5(f"{datetime.now().timestamp()}".encode()).hexdigest()[:8]
        self.search_sessions[session_id] = {
            'results': results,
            'total': total,
            'query': query,
            'offset': offset,
            'timestamp': datetime.now()
        }
        return session_id

    def get_search_session(self, session_id: str) -> Dict:
        session = self.search_sessions.get(session_id)
        if session and datetime.now() - session['timestamp'] < timedelta(hours=1):
            return session
        return None

# Initialize clients
mdex = MangaDexClient()
sessions = SessionManager()

# Error handling decorator
def error_handler(func):
    @wraps(func)
    async def wrapper(client, update, *args, **kwargs):
        try:
            return await func(client, update, *args, **kwargs)
        except FloodWait as e:
            logger.warning(f"Flood wait required: {e}")
            await asyncio.sleep(e.value)
            return await func(client, update, *args, **kwargs)
        except QueryIdInvalid:
            logger.warning("Query ID expired, ignoring answer")
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}", exc_info=True)
            if isinstance(update, Message):
                await update.reply(small_caps("operation failed: internal error"), parse_mode=ParseMode.MARKDOWN)
            elif isinstance(update, CallbackQuery):
                try:
                    await update.answer(small_caps("operation failed"), show_alert=True)
                except QueryIdInvalid:
                    pass
    return wrapper

# Generate search results message
async def generate_search_message(session_id: str) -> Tuple[str, InlineKeyboardMarkup]:
    session = sessions.get_search_session(session_id)
    if not session:
        return "", InlineKeyboardMarkup([])

    results = session['results']
    total = session['total']

    caption = f"**{small_caps('search results')}**\n{'─' * 10}\n"
    for idx, res in enumerate(results):
        caption += f"{idx+1}. [{res['title']}]({res['cover_url']})\n★ {res['score']}/100\n"

    buttons = []
    for idx in range(len(results)):
        buttons.append([InlineKeyboardButton(
            f"Dump All: {results[idx]['title'][:25]}",
            callback_data=f"dumpall:{session_id}:{idx}"
        )])

    return caption[:1024], InlineKeyboardMarkup(buttons)

# Command to search manga
@shivuu.on_message(filters.command("mdump"))
@error_handler
async def mdump_command(client, message: Message):
    query = " ".join(message.command[1:])
    if not query:
        return await message.reply(small_caps("provide manga name"), parse_mode=ParseMode.MARKDOWN)

    results, total = await mdex.search_manga(query)
    if not results:
        await message.reply(small_caps("no results found"), parse_mode=ParseMode.MARKDOWN)
        return

    session_id = sessions.create_search_session(results, total, query, 0)
    caption, reply_markup = await generate_search_message(session_id)
    await message.reply(
        text=caption,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=False
    )

# Handle "Dump All" button
@shivuu.on_callback_query(filters.regex(r"^dumpall:"))
@error_handler
async def handle_dump_all(client, callback: CallbackQuery):
    _, session_id, idx = callback.data.split(":")
    session = sessions.get_search_session(session_id)
    if not session:
        await callback.answer("Session expired", show_alert=True)
        return
    try:
        manga = session['results'][int(idx)]
    except (IndexError, ValueError):
        await callback.answer("Invalid selection", show_alert=True)
        return

    user_id = callback.from_user.id
    manga_id = manga['id']
    manga_title = manga['title']
    chat_id = callback.message.chat.id
    message_id = callback.message.message_id

    asyncio.create_task(dump_all_chapters(user_id, manga_id, manga_title, chat_id, message_id))
    await callback.answer("Dumping started, check your DMs.")
    await callback.message.edit_text(small_caps("dumping started, check your dms"), parse_mode=ParseMode.MARKDOWN)

# Dump all chapters
async def dump_all_chapters(user_id, manga_id, manga_title, chat_id, message_id):
    try:
        await shivuu.send_message(user_id, f"Starting to dump chapters for {manga_title}...")
    except Exception as e:
        await shivuu.send_message(
            chat_id,
            small_caps("please start a conversation with me by sending /start in dms"),
            reply_to_message_id=message_id,
            parse_mode=ParseMode.MARKDOWN
        )
        return

    chapters = await mdex.get_all_chapters(manga_id)
    if not chapters:
        await shivuu.send_message(user_id, small_caps("no chapters found for this manga"), parse_mode=ParseMode.MARKDOWN)
        return

    pdf_files = []
    for chapter in chapters:
        try:
            pdf_bytes = await generate_pdf(chapter)
            pdf_files.append((f"chapter_{chapter['chapter']}.pdf", pdf_bytes))
        except Exception as e:
            logger.error(f"Failed to generate PDF for chapter {chapter['chapter']}: {e}")
            continue

    # Send all PDFs in batches respecting rate limits
    batch_size = 10  # Adjust based on testing
    for i in range(0, len(pdf_files), batch_size):
        batch = pdf_files[i:i + batch_size]
        for file_name, pdf_bytes in batch:
            try:
                await shivuu.send_document(
                    user_id,
                    document=BytesIO(pdf_bytes),
                    file_name=file_name,
                    caption=small_caps(f"chapter {file_name.split('_')[1].split('.')[0]} of {manga_title}"),
                    parse_mode=ParseMode.MARKDOWN
                )
                await asyncio.sleep(1)  # Rate limit compliance (1 second delay)
            except Exception as e:
                logger.error(f"Failed to send document {file_name}: {e}")
                continue

    await shivuu.send_message(user_id, small_caps(f"all chapters dumped for {manga_title}"), parse_mode=ParseMode.MARKDOWN)

# Generate PDF for a chapter
async def generate_pdf(chapter):
    data = await mdex.get_chapter_data(chapter['id'])
    if not data or 'chapter' not in data:
        raise ValueError("Invalid chapter data")
    base_url = data['baseUrl']
    images = data['chapter']['data']
    hash_value = data['chapter']['hash']

    image_buffers = []
    async with aiohttp.ClientSession() as session:
        tasks = [download_image(session, f"{base_url}/data/{hash_value}/{filename}") for filename in images]
        for task in asyncio.as_completed(tasks):
            img_bytes = await task
            bio = BytesIO(img_bytes)
            img = Image.open(bio).convert('RGB')
            bio = BytesIO()
            img.save(bio, format='JPEG', quality=85)
            image_buffers.append(bio.getvalue())

    loop = asyncio.get_running_loop()
    pdf_bytes = await loop.run_in_executor(None, img2pdf.convert, image_buffers)
    return pdf_bytes

async def download_image(session: aiohttp.ClientSession, url: str) -> bytes:
    async with session.get(url) as response:
        return await response.read()

# Cleanup on bot shutdown
async def cleanup():
    await mdex.close()
