import os
import json
import logging
import hashlib
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Tuple, Dict, List
from functools import wraps
from io import BytesIO
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from shivu import shivuu
from PIL import Image
import img2pdf
import aiohttp
from pyrogram import filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
from pyrogram.errors import FloodWait, QueryIdInvalid
from difflib import SequenceMatcher
import asyncio 

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class ParseMode(Enum):
    MARKDOWN = enums.ParseMode.MARKDOWN
    HTML = enums.ParseMode.HTML
    DISABLED = enums.ParseMode.DISABLED

SMALL_CAPS_TRANS = str.maketrans(
    'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ',
    'ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀsᴛᴜᴠᴡxʏᴢᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀsᴛᴜᴠᴡxʏᴢ'
)

def small_caps(text: str) -> str:
    return text.translate(SMALL_CAPS_TRANS)

class MangaDexClient:
    BASE_URL = "https://api.mangadex.org"
    SYMBOLS = {
        'title': '⌖',
        'divider': '▰▱'*5,
        'list_item': '▢',
        'arrow': '➾',
        'nav_prev': '◀',
        'nav_next': '▶',
        'progress': '▰',
        'inactive': '▱',
        'page': '⫸',
        'back': '⫷'
    }

    def __init__(self):
        self.session = None

    async def init_session(self):
        self.session = aiohttp.ClientSession()
        self.session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})

    async def _handle_response(self, response: aiohttp.ClientResponse) -> dict:
        try:
            if response.status >= 400:
                raise aiohttp.ClientResponseError(
                    response.request_info,
                    response.history,
                    status=response.status
                )
            return await response.json()
        except (json.JSONDecodeError, aiohttp.ClientResponseError) as e:
            logger.error(f"Response error: {e}")
            return {}

    async def search_manga(self, query: str, offset: int = 0, limit: int = 5) -> Tuple[List[Dict], int]:
        try:
            params = {
                "title": query,
                "limit": limit,
                "offset": offset,
                "includes[]": ["cover_art"],
                "contentRating[]": ["safe", "suggestive", "erotica", "pornographic"],
                "order[relevance]": "desc"
            }
            async with self.session.get(f"{self.BASE_URL}/manga", params=params) as response:
                data = await self._handle_response(response)
                
                results = []
                for manga in data.get('data', []):
                    attrs = manga.get('attributes', {})
                    relationships = manga.get('relationships', [])
                    
                    cover_art = next(
                        (r for r in relationships if r.get('type') == 'cover_art'), None
                    )
                    cover_file = cover_art.get('attributes', {}).get('fileName', '') if cover_art else ''
                    cover_url = f"https://uploads.mangadex.org/covers/{manga['id']}/{cover_file}" if cover_file else ''
                    
                    results.append({
                        'id': manga['id'],
                        'title': attrs.get('title', {}).get('en', 'Untitled'),
                        'year': attrs.get('year', 'N/A'),
                        'status': str(attrs.get('status', 'N/A')).capitalize(),
                        'score': round(attrs.get('rating', {}).get('bayesian', 0) * 10),
                        'description': self._truncate_description(attrs.get('description', {}).get('en', '')),
                        'cover_url': cover_url,
                        'url': f"https://mangadex.org/title/{manga['id']}"
                    })
                
                return results, data.get('total', 0)
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return [], 0

    def _truncate_description(self, text: str) -> str:
        if len(text) <= 350:
            return text
        return text[:347].rsplit(' ', 1)[0] + "..."

    async def get_all_chapters(self, manga_id: str) -> List[Dict]:
        all_chapters = []
        offset = 0
        limit = 100
        while True:
            params = {
                "translatedLanguage[]": "en",
                "order[chapter]": "asc",
                "includes[]": ["scanlation_group"],
                "limit": limit,
                "offset": offset,
                "contentRating[]": ["safe", "suggestive", "erotica", "pornographic"]
            }
            async with self.session.get(f"{self.BASE_URL}/manga/{manga_id}/feed", params=params) as response:
                data = await self._handle_response(response)
                chapters = data.get('data', [])
                if not chapters:
                    break
                all_chapters.extend(chapters)
                offset += limit
                await asyncio.sleep(1.5)
        
        seen = set()
        unique_chapters = []
        for ch in all_chapters:
            attributes = ch.get('attributes', {})
            relationships = ch.get('relationships', [])
            group = next(
                (r for r in relationships if r.get('type') == 'scanlation_group'), None
            )
            group_name = group.get('attributes', {}).get('name', 'Unknown') if group else 'Unknown'
            chapter_data = {
                'id': ch['id'],
                'chapter': str(attributes.get('chapter', 'Oneshot')),
                'title': attributes.get('title', ''),
                'group': group_name
            }
            identifier = f"{chapter_data['chapter']}-{chapter_data['group']}"
            if identifier not in seen:
                seen.add(identifier)
                unique_chapters.append(chapter_data)
        
        return unique_chapters

class SessionManager:
    def __init__(self):
        self.search_sessions = {}
        self.chapter_sessions = {}

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

    def create_chapter_session(self, manga_id: str, chapters: List[Dict], search_session_id: str) -> str:
        session_id = hashlib.md5(f"{manga_id}{datetime.now().timestamp()}".encode()).hexdigest()[:8]
        self.chapter_sessions[session_id] = {
            'manga_id': manga_id,
            'chapters': chapters,
            'search_session_id': search_session_id,
            'timestamp': datetime.now()
        }
        return session_id

    def get_search_session(self, session_id: str) -> Optional[Dict]:
        session = self.search_sessions.get(session_id)
        if session and datetime.now() - session['timestamp'] < timedelta(hours=1):
            return session
        return None

    def get_chapter_session(self, session_id: str) -> Optional[Dict]:
        session = self.chapter_sessions.get(session_id)
        if session and datetime.now() - session['timestamp'] < timedelta(hours=1):
            return session
        return None

mdex = MangaDexClient()
sessions = SessionManager()

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
                await update.reply(small_caps("operation failed: internal error"), parse_mode=ParseMode.MARKDOWN.value)
            elif isinstance(update, CallbackQuery):
                try:
                    await update.answer(small_caps("operation failed"), show_alert=True)
                except QueryIdInvalid:
                    pass
    return wrapper

async def generate_search_message(session_id: str) -> Tuple[str, InlineKeyboardMarkup]:
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
            callback_data=f"srch:{session_id}:{idx}"
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

@shivuu.on_message(filters.command("mangadex"))
@error_handler
async def mangadex_command(client, message: Message):
    query = " ".join(message.command[1:])
    if not query:
        return await message.reply(small_caps("provide manga name"), parse_mode=ParseMode.MARKDOWN.value)

    results, total = await mdex.search_manga(query)
    if not results:
        words = query.split()[:3]
        suggestion_candidates = defaultdict(lambda: {'manga': None, 'freq': 0})

        for word in words:
            word_results, _ = await mdex.search_manga(word, limit=10)
            for manga in word_results:
                manga_id = manga['id']
                if suggestion_candidates[manga_id]['manga'] is None:
                    suggestion_candidates[manga_id]['manga'] = manga
                suggestion_candidates[manga_id]['freq'] += 1
            await asyncio.sleep(0.5)

        suggestions = []
        for candidate in suggestion_candidates.values():
            manga = candidate['manga']
            title = manga['title'].lower()
            similarity = SequenceMatcher(None, query.lower(), title).ratio()
            suggestions.append((manga, similarity, candidate['freq']))

        suggestions.sort(key=lambda x: (x[1], x[2]), reverse=True)
        top_suggestions = suggestions[:5]

        if top_suggestions:
            caption = "**Did you mean...**\n"
            buttons = []
            temp_session_id = sessions.create_search_session(
                [s[0] for s in top_suggestions], len(top_suggestions), query, 0
            )
            for idx, (manga, sim, freq) in enumerate(top_suggestions):
                caption += f"{idx+1}. {manga['title']} (Similarity: {int(sim*100)}%)\n"
                buttons.append([InlineKeyboardButton(
                    f"{idx+1}. {manga['title'][:25]}",
                    callback_data=f"srch:{temp_session_id}:{idx}"
                )])
            await message.reply(
                text=caption,
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=ParseMode.MARKDOWN.value,
                disable_web_page_preview=False
            )
            return
        else:
            await message.reply(small_caps("no results found"), parse_mode=ParseMode.MARKDOWN.value)
            return

    session_id = sessions.create_search_session(results, total, query, 0)
    caption, reply_markup = await generate_search_message(session_id)
    await message.reply(
        text=caption,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN.value,
        disable_web_page_preview=False
    )

@shivuu.on_callback_query(filters.regex(r"^srch:"))
@error_handler
async def handle_search_select(client, callback: CallbackQuery):
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
    chapters = await mdex.get_all_chapters(manga['id'])
    if not chapters:
        await callback.answer("No chapters available", show_alert=True)
        return
    ch_session = sessions.create_chapter_session(manga['id'], chapters, session_id)
    caption = (
        f"**[{manga['title']}]({manga['cover_url']})**\n"
        f"{mdex.SYMBOLS['divider']}\n"
        f"{mdex.SYMBOLS['list_item']} Status: {manga['status']}\n"
        f"{mdex.SYMBOLS['list_item']} Year: {manga['year']}\n"
        f"{mdex.SYMBOLS['divider']}\n"
        f"{manga['description']}"
    )
    await callback.message.edit_text(
        text=caption[:1024],
        reply_markup=await create_chapter_buttons(ch_session),
        parse_mode=ParseMode.MARKDOWN.value,
        disable_web_page_preview=False
    )

async def create_chapter_buttons(session_id: str, page: int = 0) -> InlineKeyboardMarkup:
    session = sessions.get_chapter_session(session_id)
    if not session:
        return InlineKeyboardMarkup([])
    chapters = session['chapters']
    search_session_id = session['search_session_id']
    PAGE_SIZE = 8
    total_pages = (len(chapters) + PAGE_SIZE - 1) // PAGE_SIZE
    buttons = []
    for ch in chapters[page*PAGE_SIZE : (page+1)*PAGE_SIZE]:
        btn_text = f"Ch. {ch['chapter']} | {ch['group'][:10]}"
        buttons.append([InlineKeyboardButton(
            btn_text, callback_data=f"dl:{session_id}:{ch['id']}:{ch['chapter']}"
        )])
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(
            mdex.SYMBOLS['back'], callback_data=f"chpg:{session_id}:{page-1}"
        ))
    nav_buttons.append(InlineKeyboardButton(
        f"{page+1}/{total_pages}", callback_data="noop"
    ))
    if (page+1)*PAGE_SIZE < len(chapters):
        nav_buttons.append(InlineKeyboardButton(
            mdex.SYMBOLS['page'], callback_data=f"chpg:{session_id}:{page+1}"
        ))
    if nav_buttons:
        buttons.append(nav_buttons)
    buttons.append([
        InlineKeyboardButton(
            "🔙 Back to Results",
            callback_data=f"back:{search_session_id}"
        )
    ])
    return InlineKeyboardMarkup(buttons)

@shivuu.on_callback_query(filters.regex(r"^chpg:"))
@error_handler
async def handle_chapter_pagination(client, callback: CallbackQuery):
    _, session_id, page = callback.data.split(":")
    await callback.message.edit_reply_markup(
        await create_chapter_buttons(session_id, int(page))
    )

@shivuu.on_callback_query(filters.regex(r"^back:"))
@error_handler
async def handle_back_button(client, callback: CallbackQuery):
    _, search_session_id = callback.data.split(":")
    session = sessions.get_search_session(search_session_id)
    if not session:
        await callback.answer("Search session expired", show_alert=True)
        return
    caption, reply_markup = await generate_search_message(search_session_id)
    await callback.message.edit_text(
        text=caption,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN.value,
        disable_web_page_preview=False
    )

@shivuu.on_callback_query(filters.regex(r"^dl:"))
@error_handler
async def handle_download(client, callback: CallbackQuery):
    _, session_id, ch_id, ch_num = callback.data.split(":")
    session = sessions.get_chapter_session(session_id)
    if not session:
        await callback.answer("Session expired", show_alert=True)
        return
    try:
        async with client.session.get(f"{mdex.BASE_URL}/at-home/server/{ch_id}") as response:
            data = await mdex._handle_response(response)
            if not data or 'chapter' not in data:
                raise ValueError("Invalid chapter data")
            base_url = data['baseUrl']
            images = data['chapter']['data']
            image_buffers = []
            last_reported_progress = 0
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = []
                for filename in images:
                    url = f"{base_url}/data/{data['chapter']['hash']}/{filename}"
                    futures.append(executor.submit(
                        lambda u: Image.open(BytesIO(requests.get(u).content)).convert('RGB'),
                        url
                    ))
                for idx, future in enumerate(futures):
                    img = future.result()
                    bio = BytesIO()
                    img.save(bio, format='JPEG', quality=85)
                    image_buffers.append(bio.getvalue())
                    progress = (idx + 1) / len(images) * 100
                    next_threshold = (last_reported_progress // 20 + 1) * 20
                    if progress >= next_threshold or idx == len(images) - 1:
                        await callback.message.edit_text(
                            f"Downloading... {int(progress)}%",
                            parse_mode=ParseMode.DISABLED.value
                        )
                        last_reported_progress = int(progress // 20 * 20)
            pdf_bytes = img2pdf.convert(image_buffers)
            await callback.message.reply_document(
                document=BytesIO(pdf_bytes),
                file_name=f"{small_caps('chapter')}_{ch_num}.pdf",
                parse_mode=ParseMode.DISABLED.value
            )
            if session_id in sessions.chapter_sessions:
                await callback.message.edit_text(
                    text=callback.message.text,
                    reply_markup=await create_chapter_buttons(session_id),
                    parse_mode=ParseMode.DISABLED.value
                )
    except Exception as e:
        logger.error(f"Download failed: {e}")
        await callback.answer("Download failed", show_alert=True)
    finally:
        if session_id in sessions.chapter_sessions:
            del sessions.chapter_sessions[session_id]
