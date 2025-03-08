import hashlib
import asyncio
import logging
import random
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
import requests
from requests.exceptions import RequestException
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from PIL import Image
import img2pdf
from fake_useragent import UserAgent
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.enums import ParseMode
from pyrogram.errors import FloodWait, QueryIdInvalid, UserIsBlocked, PeerIdInvalid
from functools import wraps
from shivu import shivuu

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Small caps text converter
SMALL_CAPS_TRANS = str.maketrans(
    'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ',
    'ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀsᴛᴜᴠᴷxʏᴢᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀsᴛᴜᴠᴷxʏᴢ'
)

def small_caps(text: str) -> str:
    return text.translate(SMALL_CAPS_TRANS)

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

class MangaDexClient:
    BASE_URL = "https://api.mangadex.org"
    SYMBOLS = {
        'back': '◀️',
        'page': '▶️',
        'divider': '▰▱' * 5,
        'list_item': '▢',
    }

    def __init__(self):
        self.session = requests.Session()
        self.user_agents = [UserAgent().random for _ in range(5)]  # Pre-generate multiple user agents
        self.session.headers.update({"User-Agent": random.choice(self.user_agents)})

    def _rotate_user_agent(self):
        """Rotate user agent for each request."""
        self.session.headers.update({"User-Agent": random.choice(self.user_agents)})

    def _handle_response(self, response: requests.Response) -> Dict:
        try:
            response.raise_for_status()
            return response.json()
        except RequestException as e:
            logger.error(f"Response error: {e}")
            return {}

    def search_manga(self, query: str, offset: int = 0, limit: int = 5) -> Tuple[List[Dict], int]:
        """Search manga by title."""
        try:
            self._rotate_user_agent()
            response = self.session.get(
                f"{self.BASE_URL}/manga",
                params={
                    "title": query,
                    "limit": limit,
                    "offset": offset,
                    "includes[]": ["cover_art"],
                    "contentRating[]": ["safe", "suggestive", "erotica", "pornographic"],
                    "order[relevance]": "desc"
                }
            )
            data = self._handle_response(response)
            results = []
            for manga in data.get('data', []):
                attrs = manga.get('attributes', {})
                cover = next((rel for rel in manga.get('relationships', []) if rel['type'] == 'cover_art'), None)
                cover_url = f"https://uploads.mangadex.org/covers/{manga['id']}/{cover['attributes']['fileName']}" if cover else ""
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

    def get_all_chapters(self, manga_id: str) -> List[Dict]:
        """Fetch all chapters for a manga, removing duplicates."""
        try:
            all_chapters = []
            offset = 0
            limit = 100
            while True:
                self._rotate_user_agent()
                response = self.session.get(
                    f"{self.BASE_URL}/manga/{manga_id}/feed",
                    params={
                        "translatedLanguage[]": "en",
                        "order[chapter]": "asc",
                        "includes[]": ["scanlation_group"],
                        "limit": limit,
                        "offset": offset,
                        "contentRating[]": ["safe", "suggestive", "erotica", "pornographic"]
                    }
                )
                data = self._handle_response(response)
                chapters = data.get('data', [])
                if not chapters:
                    break
                all_chapters.extend(chapters)
                offset += limit
                await asyncio.sleep(1.5)  # Respect rate limits
            # Remove duplicates and sort by chapter number
            seen = set()
            unique_chapters = []
            for ch in all_chapters:
                attrs = ch.get('attributes', {})
                relationships = ch.get('relationships', [])
                group = next((r for r in relationships if r.get('type') == 'scanlation_group'), None)
                group_name = group.get('attributes', {}).get('name', 'Unknown') if group else 'Unknown'
                chapter_data = {
                    'id': ch['id'],
                    'chapter': str(attrs.get('chapter', 'Oneshot')),
                    'title': attrs.get('title', ''),
                    'group': group_name
                }
                identifier = f"{chapter_data['chapter']}-{chapter_data['group']}"
                if identifier not in seen:
                    seen.add(identifier)
                    unique_chapters.append(chapter_data)
            # Sort chapters by chapter number (numeric if possible)
            unique_chapters.sort(key=lambda x: float(x['chapter']) if x['chapter'].replace('.', '').isdigit() else float('inf'))
            return unique_chapters
        except Exception as e:
            logger.error(f"Failed to fetch chapters: {e}")
            return []

    async def download_chapter(self, chapter_id: str, chapter_num: str) -> Optional[Tuple[BytesIO, str]]:
        """Download a chapter and convert to PDF."""
        try:
            self._rotate_user_agent()
            response = self.session.get(f"{self.BASE_URL}/at-home/server/{chapter_id}")
            data = self._handle_response(response)
            if not data or 'chapter' not in data:
                raise ValueError("Invalid chapter data")
            base_url = data['baseUrl']
            images = data['chapter']['data']
            image_buffers = []
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = []
                for filename in images:
                    url = f"{base_url}/data/{data['chapter']['hash']}/{filename}"
                    futures.append(executor.submit(
                        lambda u: Image.open(BytesIO(requests.get(u, headers={"User-Agent": random.choice(self.user_agents)}).content)).convert('RGB'),
                        url
                    ))
                for future in futures:
                    img = future.result()
                    bio = BytesIO()
                    img.save(bio, format='JPEG', quality=85)
                    image_buffers.append(bio.getvalue())
            pdf_bytes = img2pdf.convert(image_buffers)
            return BytesIO(pdf_bytes), chapter_num
        except Exception as e:
            logger.error(f"Failed to download chapter {chapter_num}: {e}")
            return None, chapter_num

class SessionManager:
    def __init__(self):
        self.search_sessions = {}
        self.dump_sessions = {}

    def create_search_session(self, results: List[Dict], total: int, query: str, offset: int = 0) -> str:
        """Create a search session."""
        session_id = hashlib.md5(f"{datetime.now().timestamp()}".encode()).hexdigest()[:8]
        self.search_sessions[session_id] = {
            'results': results,
            'total': total,
            'query': query,
            'offset': offset,
            'timestamp': datetime.now()
        }
        return session_id

    def get_search_session(self, session_id: str) -> Optional[Dict]:
        session = self.search_sessions.get(session_id)
        if session and datetime.now() - session['timestamp'] < timedelta(hours=1):
            return session
        return None

    def create_dump_session(self, manga_id: str, chapters: List[Dict], user_id: int) -> str:
        """Create a dump session."""
        session_id = hashlib.md5(f"{manga_id}{datetime.now().timestamp()}".encode()).hexdigest()[:8]
        self.dump_sessions[session_id] = {
            'manga_id': manga_id,
            'chapters': chapters,
            'user_id': user_id,
            'timestamp': datetime.now(),
            'progress': 0,
            'total': len(chapters),
            'sent': 0  # Track number of chapters sent
        }
        return session_id

    def get_dump_session(self, session_id: str) -> Optional[Dict]:
        session = self.dump_sessions.get(session_id)
        if session and datetime.now() - session['timestamp'] < timedelta(hours=1):
            return session
        return None

    def update_dump_progress(self, session_id: str, progress: int, sent: int):
        """Update dump progress and sent count."""
        session = self.get_dump_session(session_id)
        if session:
            session['progress'] = progress
            session['sent'] = sent
            session['timestamp'] = datetime.now()

# Initialize clients
mdex = MangaDexClient()
sessions = SessionManager()

async def generate_search_message(session_id: str) -> Tuple[str, InlineKeyboardMarkup]:
    """Generate search results message."""
    session = sessions.get_search_session(session_id)
    if not session:
        return "", InlineKeyboardMarkup([])

    results = session['results']
    total = session['total']
    current_offset = session['offset']

    caption = f"**{small_caps('search results')}**\n{mdex.SYMBOLS['divider']}\n"
    for idx, res in enumerate(results):
        caption += f"{idx+1}. [{res['title']}]({res['cover_url']})\n★ {res['score']}/100\n"

    buttons = []
    for idx in range(len(results)):
        buttons.append([InlineKeyboardButton(
            f"{idx+1}. {results[idx]['title'][:25]}",
            callback_data=f"manga_detail:{session_id}:{idx}"
        )])

    pagination_buttons = []
    if current_offset > 0:
        pagination_buttons.append(InlineKeyboardButton(
            mdex.SYMBOLS['back'], callback_data=f"pg:{session_id}:prev"
        ))

    if (current_offset + 5) < total:
        pagination_buttons.append(InlineKeyboardButton(
            mdex.SYMBOLS['page'], callback_data=f"pg:{session_id}:next"
        ))

    if pagination_buttons:
        buttons.append(pagination_buttons)

    return caption[:1024], InlineKeyboardMarkup(buttons)

# /mdump Command
@shivuu.on_message(filters.command("mdump"))
@error_handler
async def mdump_command(client, message: Message):
    """Handle /mdump command to search for manga and dump chapters."""
    query = " ".join(message.command[1:])
    if not query:
        return await message.reply(small_caps("provide manga name"), parse_mode=ParseMode.MARKDOWN)

    results, total = mdex.search_manga(query)
    if not results:
        return await message.reply(small_caps("no results found"), parse_mode=ParseMode.MARKDOWN)

    session_id = sessions.create_search_session(results, total, query, 0)
    caption, reply_markup = await generate_search_message(session_id)
    await message.reply(
        text=caption,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=False
    )

@shivuu.on_callback_query(filters.regex(r"^manga_detail:"))
@error_handler
async def handle_manga_detail(client, callback: CallbackQuery):
    """Handle manga detail view with MDump button."""
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
    chapters = mdex.get_all_chapters(manga['id'])
    if not chapters:
        await callback.answer("No chapters available", show_alert=True)
        return
    caption = (
        f"**[{manga['title']}]({manga['cover_url']})**\n"
        f"{mdex.SYMBOLS['divider']}\n"
        f"{mdex.SYMBOLS['list_item']} Status: {manga['status']}\n"
        f"{mdex.SYMBOLS['list_item']} Year: {manga['year']}\n"
        f"{mdex.SYMBOLS['list_item']} Chapters: {len(chapters)}\n"
        f"{mdex.SYMBOLS['divider']}\n"
        f"{manga['description']}"
    )
    buttons = [[InlineKeyboardButton("Dump All Chapters", callback_data=f"mdump:{manga['id']}:{callback.from_user.id}")]]
    buttons.append([InlineKeyboardButton("🔙 Back to Results", callback_data=f"back_to_search:{session_id}")])
    await callback.message.edit_text(
        text=caption[:1024],
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=False
    )

@shivuu.on_callback_query(filters.regex(r"^back_to_search:"))
@error_handler
async def handle_back_to_search(client, callback: CallbackQuery):
    """Handle back navigation to search results."""
    _, session_id = callback.data.split(":")
    caption, reply_markup = await generate_search_message(session_id)
    await callback.message.edit_text(
        text=caption,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=False
    )

@shivuu.on_callback_query(filters.regex(r"^mdump:"))
@error_handler
async def handle_mdump(client, callback: CallbackQuery):
    """Handle MDump button to dump all chapters into DMs."""
    _, manga_id, user_id = callback.data.split(":")
    user_id = int(user_id)
    chapters = mdex.get_all_chapters(manga_id)
    if not chapters:
        await callback.answer("No chapters available", show_alert=True)
        return

    # Check DM accessibility
    try:
        await client.send_message(user_id, small_caps("starting chapter dump..."), parse_mode=ParseMode.MARKDOWN)
    except (UserIsBlocked, PeerIdInvalid):
        await callback.answer("Cannot access your DMs. Please start a chat with the bot first.", show_alert=True)
        return

    session_id = sessions.create_dump_session(manga_id, chapters, user_id)
    await callback.message.edit_text(small_caps(f"dumping {len(chapters)} chapters to your DMs..."), parse_mode=ParseMode.MARKDOWN)

    # Download all chapters concurrently
    async def download_all_chapters():
        tasks = [mdex.download_chapter(chapter['id'], chapter['chapter']) for chapter in chapters]
        return await asyncio.gather(*tasks)

    chapter_pdfs = await download_all_chapters()
    downloaded_chapters = [(pdf, num) for pdf, num in chapter_pdfs if pdf is not None]

    # Send chapters in order, 30 per minute
    RATE_LIMIT = 30  # Chapters per minute
    SECONDS_PER_CHAPTER = 60 / RATE_LIMIT  # 2 seconds per chapter

    sent_count = 0
    for pdf, chapter_num in downloaded_chapters:
        session = sessions.get_dump_session(session_id)
        if not session:
            break
        try:
            await client.send_document(
                user_id,
                document=pdf,
                file_name=f"{small_caps('chapter')}_{chapter_num}.pdf",
                caption=f"Chapter {chapter_num} ({chapters[sent_count]['group']})",
                parse_mode=ParseMode.DISABLED
            )
            sent_count += 1
            sessions.update_dump_progress(session_id, sent_count, sent_count)
            await callback.message.edit_text(
                small_caps(f"dumping progress: {sent_count}/{len(chapters)} chapters"),
                parse_mode=ParseMode.MARKDOWN
            )
            await asyncio.sleep(SECONDS_PER_CHAPTER)  # Rate limit to 30 per minute
        except Exception as e:
            logger.error(f"Failed to send chapter {chapter_num}: {e}")
        finally:
            pdf.close()

    await client.send_message(user_id, small_caps("chapter dump completed!"), parse_mode=ParseMode.MARKDOWN)
    await callback.message.edit_text(small_caps("chapter dump completed!"), parse_mode=ParseMode.MARKDOWN)

@shivuu.on_callback_query(filters.regex(r"^pg:"))
@error_handler
async def handle_search_pagination(client, callback: CallbackQuery):
    """Handle pagination for search results."""
    _, session_id, direction = callback.data.split(":")
    session = sessions.get_search_session(session_id)
    if not session:
        await callback.answer("Session expired", show_alert=True)
        return
    offset = session['offset']
    limit = 5
    if direction == "next":
        new_offset = offset + limit
    elif direction == "prev":
        new_offset = max(0, offset - limit)
    else:
        await callback.answer("Invalid direction", show_alert=True)
        return
    results, total = mdex.search_manga(session['query'], new_offset, limit)
    if not results:
        await callback.answer("No more results", show_alert=True)
        return
    session['results'] = results
    session['offset'] = new_offset
    session['timestamp'] = datetime.now()
    new_session_id = sessions.create_search_session(results, total, session['query'], new_offset)
    caption, reply_markup = await generate_search_message(new_session_id)
    await callback.message.edit_text(
        text=caption,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=False
    )
