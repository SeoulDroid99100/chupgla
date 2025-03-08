import hashlib
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
import requests
from requests.exceptions import RequestException
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.enums import ParseMode
from pyrogram.errors import FloodWait, QueryIdInvalid
import logging
from functools import wraps

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Small caps text converter
SMALL_CAPS_TRANS = str.maketrans(
    'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ',
    'ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀsᴛᴜᴠᴡxʏᴢᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀsᴛᴜᴠᴡxʏᴢ'
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
        self.session.headers.update({"User-Agent": self._generate_user_agent()})
        self.tags = self._fetch_tags()  # Cache tags on initialization

    def _generate_user_agent(self) -> str:
        return "MangaBot/1.0"

    def _handle_response(self, response: requests.Response) -> Dict:
        try:
            response.raise_for_status()
            return response.json()
        except RequestException as e:
            logger.error(f"Response error: {e}")
            return {}

    def _fetch_tags(self) -> List[Dict]:
        """Fetch all tags from MangaDex."""
        try:
            response = self.session.get(f"{self.BASE_URL}/tag")
            data = self._handle_response(response)
            return data.get('data', [])
        except Exception as e:
            logger.error(f"Failed to fetch tags: {e}")
            return []

    @property
    def genres(self) -> List[Dict]:
        """Get list of genre tags."""
        return [tag for tag in self.tags if tag['attributes']['group'] == 'genre']

    def _truncate_description(self, desc: str) -> str:
        return desc[:200] + "..." if len(desc) > 200 else desc

    def search_manga(self, query: str = "", offset: int = 0, limit: int = 5, 
                     genre_ids: List[str] = None, 
                     content_rating: List[str] = ["safe", "suggestive", "erotica", "pornographic"]) -> Tuple[List[Dict], int]:
        """Search manga with optional genre and content rating filters."""
        try:
            params = {
                "limit": limit,
                "offset": offset,
                "includes[]": ["cover_art"],
                "contentRating[]": content_rating,
                "order[relevance]": "desc"
            }
            if query:
                params["title"] = query
            if genre_ids:
                params["includedTags[]"] = genre_ids
            response = self.session.get(f"{self.BASE_URL}/manga", params=params)
            data = self._handle_response(response)
            results = []
            for manga in data.get('data', []):
                attrs = manga.get('attributes', {})
                cover = next((rel for rel in manga.get('relationships', []) if rel['type'] == 'cover_art'), None)
                cover_url = f"https://uploads.mangadex.org/covers/{manga['id']}/{cover['attributes']['fileName']}" if cover else ""
                genre_tags = [{'id': tag['id'], 'name': tag['attributes']['name']['en']} 
                              for tag in attrs.get('tags', []) if tag['attributes']['group'] == 'genre']
                results.append({
                    'id': manga['id'],
                    'title': attrs.get('title', {}).get('en', 'Untitled'),
                    'year': attrs.get('year', 'N/A'),
                    'status': str(attrs.get('status', 'N/A')).capitalize(),
                    'score': round(attrs.get('rating', {}).get('bayesian', 0) * 10),
                    'description': self._truncate_description(attrs.get('description', {}).get('en', '')),
                    'cover_url': cover_url,
                    'url': f"https://mangadex.org/title/{manga['id']}",
                    'genre_tags': genre_tags
                })
            return results, data.get('total', 0)
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return [], 0

class SessionManager:
    def __init__(self):
        self.search_sessions = {}
        self.genre_selection_sessions = {}
        self.navigation_history = {}  # New: Track navigation history

    def create_search_session(self, results: List[Dict], total: int, query: str = "", 
                              genre_ids: List[str] = None, 
                              content_rating: List[str] = ["safe", "suggestive", "erotica", "pornographic"], 
                              offset: int = 0, navigation_state: str = "") -> str:
        """Create a search session with genre, content rating, and navigation state."""
        session_id = hashlib.md5(f"{datetime.now().timestamp()}".encode()).hexdigest()[:8]
        self.search_sessions[session_id] = {
            'results': results,
            'total': total,
            'query': query,
            'genre_ids': genre_ids,
            'content_rating': content_rating,
            'offset': offset,
            'timestamp': datetime.now(),
            'navigation_state': navigation_state  # Store navigation state
        }
        return session_id

    def get_search_session(self, session_id: str) -> Optional[Dict]:
        session = self.search_sessions.get(session_id)
        if session and datetime.now() - session['timestamp'] < timedelta(hours=1):
            return session
        return None

    def create_genre_selection_session(self, selected_genres: List[str] = None, 
                                      navigation_state: str = "") -> str:
        """Create a session for genre selection with navigation state."""
        session_id = hashlib.md5(f"{datetime.now().timestamp()}".encode()).hexdigest()[:8]
        self.genre_selection_sessions[session_id] = {
            'selected_genres': selected_genres or [],
            'timestamp': datetime.now(),
            'navigation_state': navigation_state  # Store navigation state
        }
        return session_id

    def get_genre_selection_session(self, session_id: str) -> Optional[Dict]:
        session = self.genre_selection_sessions.get(session_id)
        if session and datetime.now() - session['timestamp'] < timedelta(hours=1):
            return session
        return None

    def update_genre_selection_session(self, session_id: str, selected_genres: List[str]):
        """Update the selected genres in a session."""
        session = self.get_genre_selection_session(session_id)
        if session:
            session['selected_genres'] = selected_genres
            session['timestamp'] = datetime.now()

    def add_navigation_state(self, session_id: str, state: str, prev_session_id: str = ""):
        """Add navigation state to history."""
        self.navigation_history[session_id] = {
            'state': state,
            'prev_session_id': prev_session_id,
            'timestamp': datetime.now()
        }

    def get_navigation_state(self, session_id: str) -> Optional[Dict]:
        nav = self.navigation_history.get(session_id)
        if nav and datetime.now() - nav['timestamp'] < timedelta(hours=1):
            return nav
        return None

# Initialize clients
mdex = MangaDexClient()
sessions = SessionManager()

async def generate_search_message(session_id: str) -> Tuple[str, InlineKeyboardMarkup]:
    """Generate search results message with back navigation."""
    session = sessions.get_search_session(session_id)
    if not session:
        return "", InlineKeyboardMarkup([])

    results = session['results']
    total = session['total']
    current_offset = session['offset']
    navigation_state = session.get('navigation_state', '')

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

    # Add Back button based on navigation state
    if navigation_state == "genre_selection":
        nav = sessions.get_navigation_state(session_id)
        if nav and nav['prev_session_id']:
            buttons.append([InlineKeyboardButton(
                "🔙 Back to Genre Selection", 
                callback_data=f"back_to_genre:{nav['prev_session_id']}"
            )])
    elif navigation_state == "horny":
        buttons.append([InlineKeyboardButton(
            "🔙 Restart /horny", 
            callback_data="restart_horny"
        )])

    return caption[:1024], InlineKeyboardMarkup(buttons)

# /recommend Command
@shivuu.on_message(filters.command("recommend"))
@error_handler
async def recommend_command(client, message: Message):
    """Handle /recommend command to suggest manga based on genres."""
    query = " ".join(message.command[1:])
    if not query:
        return await message.reply(small_caps("provide manga name"), parse_mode=ParseMode.MARKDOWN)

    results, total = mdex.search_manga(query, limit=1)  # Try to find an exact match
    if results:
        manga = results[0]
        genres = manga['genre_tags']
        if genres:
            caption = f"**Genres for {manga['title']}**\nSelect a genre to find similar manga:"
            buttons = [[InlineKeyboardButton(genre['name'], callback_data=f"rec_genre:{genre['id']}")] 
                       for genre in genres]
            await message.reply(
                text=caption,
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await message.reply(small_caps("no genres found for this manga"), parse_mode=ParseMode.MARKDOWN)
    else:
        caption = f"**Title not found: {query}**\nWould you like to select genres manually?"
        buttons = [[InlineKeyboardButton("Select Genres", callback_data=f"select_genres:{query}")]]
        await message.reply(
            text=caption,
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode=ParseMode.MARKDOWN
        )

# /horny Command
@shivuu.on_message(filters.command("horny"))
@error_handler
async def horny_command(client, message: Message):
    """Handle /horny command to find adult-themed manhwas."""
    manhwa_tag = next((tag for tag in mdex.tags if tag['attributes']['name']['en'].lower() == 'manhwa'), None)
    if not manhwa_tag:
        return await message.reply(small_caps("manhwa tag not found"), parse_mode=ParseMode.MARKDOWN)
    manhwa_id = manhwa_tag['id']
    results, total = mdex.search_manga(
        "", 
        limit=5, 
        genre_ids=[manhwa_id], 
        content_rating=["erotica", "pornographic"]
    )
    if not results:
        return await message.reply(small_caps("no adult manhwas found"), parse_mode=ParseMode.MARKDOWN)
    session_id = sessions.create_search_session(
        results, 
        total, 
        "", 
        [manhwa_id], 
        ["erotica", "pornographic"],
        navigation_state="horny"
    )
    sessions.add_navigation_state(session_id, "horny")
    caption, reply_markup = await generate_search_message(session_id)
    await message.reply(
        text=caption,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=False
    )

# Generate Genre Selection Buttons
async def generate_genre_buttons(session_id: str, page: int = 0) -> InlineKeyboardMarkup:
    """Generate paginated inline buttons for genre selection with back navigation."""
    session = sessions.get_genre_selection_session(session_id)
    if not session:
        return InlineKeyboardMarkup([])

    selected_genres = session['selected_genres']
    navigation_state = session.get('navigation_state', '')
    PAGE_SIZE = 10
    genres = mdex.genres
    total_pages = (len(genres) + PAGE_SIZE - 1) // PAGE_SIZE
    buttons = []
    for genre in genres[page * PAGE_SIZE:(page + 1) * PAGE_SIZE]:
        genre_id = genre['id']
        genre_name = genre['attributes']['name']['en']
        button_text = f"✅ {genre_name}" if genre_id in selected_genres else genre_name
        buttons.append([InlineKeyboardButton(
            button_text, 
            callback_data=f"toggle_genre:{session_id}:{genre_id}:{page}"
        )])

    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(mdex.SYMBOLS['back'], callback_data=f"genre_pg:{session_id}:{page-1}"))
    nav_buttons.append(InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="noop"))
    if (page + 1) * PAGE_SIZE < len(genres):
        nav_buttons.append(InlineKeyboardButton(mdex.SYMBOLS['page'], callback_data=f"genre_pg:{session_id}:{page+1}"))
    if nav_buttons:
        buttons.append(nav_buttons)

    if selected_genres:
        buttons.append([InlineKeyboardButton("Search with Selected Genres", callback_data=f"search_genres:{session_id}")])
    
    # Add Back button based on navigation state
    if navigation_state:
        buttons.append([InlineKeyboardButton(
            "🔙 Back to Initial Prompt", 
            callback_data=f"back_to_initial:{navigation_state}"
        )])

    return InlineKeyboardMarkup(buttons)

# Callback Handlers
@shivuu.on_callback_query(filters.regex(r"^select_genres:"))
@error_handler
async def handle_select_genres(client, callback: CallbackQuery):
    """Show genre selection when title is not found."""
    _, query = callback.data.split(":")
    session_id = sessions.create_genre_selection_session(navigation_state=query)
    sessions.add_navigation_state(session_id, "genre_selection")
    await callback.message.edit_text(
        "Select genres (you can select multiple):",
        reply_markup=await generate_genre_buttons(session_id, 0)
    )

@shivuu.on_callback_query(filters.regex(r"^toggle_genre:"))
@error_handler
async def handle_toggle_genre(client, callback: CallbackQuery):
    """Toggle genre selection."""
    _, session_id, genre_id, page = callback.data.split(":")
    session = sessions.get_genre_selection_session(session_id)
    if not session:
        await callback.answer("Session expired", show_alert=True)
        return
    selected_genres = session['selected_genres']
    if genre_id in selected_genres:
        selected_genres.remove(genre_id)
    else:
        selected_genres.append(genre_id)
    sessions.update_genre_selection_session(session_id, selected_genres)
    await callback.message.edit_reply_markup(await generate_genre_buttons(session_id, int(page)))

@shivuu.on_callback_query(filters.regex(r"^genre_pg:"))
@error_handler
async def handle_genre_pagination(client, callback: CallbackQuery):
    """Handle pagination for genre selection."""
    _, session_id, page = callback.data.split(":")
    await callback.message.edit_reply_markup(await generate_genre_buttons(session_id, int(page)))

@shivuu.on_callback_query(filters.regex(r"^search_genres:"))
@error_handler
async def handle_search_genres(client, callback: CallbackQuery):
    """Search manga based on selected genres."""
    _, session_id = callback.data.split(":")
    session = sessions.get_genre_selection_session(session_id)
    if not session:
        await callback.answer("Session expired", show_alert=True)
        return
    genre_ids = session['selected_genres']
    if not genre_ids:
        await callback.answer("Please select at least one genre", show_alert=True)
        return
    results, total = mdex.search_manga("", limit=5, genre_ids=genre_ids)
    if not results:
        await callback.answer("No manga found with these genres", show_alert=True)
        return
    search_session_id = sessions.create_search_session(
        results, 
        total, 
        "", 
        genre_ids,
        navigation_state="genre_selection"
    )
    sessions.add_navigation_state(search_session_id, "search_results", session_id)
    caption, reply_markup = await generate_search_message(search_session_id)
    await callback.message.edit_text(
        text=caption,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=False
    )

@shivuu.on_callback_query(filters.regex(r"^rec_genre:"))
@error_handler
async def handle_recommend_genre(client, callback: CallbackQuery):
    """Search manga based on selected genre."""
    _, genre_id = callback.data.split(":")
    results, total = mdex.search_manga("", limit=5, genre_ids=[genre_id])
    if not results:
        await callback.answer("No manga found with this genre", show_alert=True)
        return
    session_id = sessions.create_search_session(results, total, "", [genre_id])
    sessions.add_navigation_state(session_id, "search_results")
    caption, reply_markup = await generate_search_message(session_id)
    await callback.message.edit_text(
        text=caption,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=False
    )

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
    results, total = mdex.search_manga(
        session['query'], 
        new_offset, 
        limit, 
        genre_ids=session.get('genre_ids'), 
        content_rating=session.get('content_rating', ["safe", "suggestive", "erotica", "pornographic"])
    )
    if not results:
        await callback.answer("No more results", show_alert=True)
        return
    session['results'] = results
    session['offset'] = new_offset
    session['timestamp'] = datetime.now()
    new_session_id = sessions.create_search_session(
        results, 
        total, 
        session['query'], 
        session.get('genre_ids'), 
        session.get('content_rating', ["safe", "suggestive", "erotica", "pornographic"]), 
        new_offset,
        navigation_state=session.get('navigation_state', '')
    )
    nav = sessions.get_navigation_state(session_id)
    if nav:
        sessions.add_navigation_state(new_session_id, nav['state'], nav['prev_session_id'])
    caption, reply_markup = await generate_search_message(new_session_id)
    await callback.message.edit_text(
        text=caption,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=False
    )

@shivuu.on_callback_query(filters.regex(r"^back_to_genre:"))
@error_handler
async def handle_back_to_genre(client, callback: CallbackQuery):
    """Handle back navigation to genre selection."""
    _, session_id = callback.data.split(":")
    session = sessions.get_genre_selection_session(session_id)
    if not session:
        await callback.answer("Session expired", show_alert=True)
        return
    await callback.message.edit_text(
        "Select genres (you can select multiple):",
        reply_markup=await generate_genre_buttons(session_id, 0)
    )

@shivuu.on_callback_query(filters.regex(r"^back_to_initial:"))
@error_handler
async def handle_back_to_initial(client, callback: CallbackQuery):
    """Handle back navigation to initial prompt."""
    _, query = callback.data.split(":")
    caption = f"**Title not found: {query}**\nWould you like to select genres manually?"
    buttons = [[InlineKeyboardButton("Select Genres", callback_data=f"select_genres:{query}")]]
    await callback.message.edit_text(
        text=caption,
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode=ParseMode.MARKDOWN
    )

@shivuu.on_callback_query(filters.regex(r"^restart_horny$"))
@error_handler
async def handle_restart_horny(client, callback: CallbackQuery):
    """Handle restart of /horny command."""
    manhwa_tag = next((tag for tag in mdex.tags if tag['attributes']['name']['en'].lower() == 'manhwa'), None)
    if not manhwa_tag:
        await callback.message.edit_text(small_caps("manhwa tag not found"), parse_mode=ParseMode.MARKDOWN)
        return
    manhwa_id = manhwa_tag['id']
    results, total = mdex.search_manga(
        "", 
        limit=5, 
        genre_ids=[manhwa_id], 
        content_rating=["erotica", "pornographic"]
    )
    if not results:
        await callback.message.edit_text(small_caps("no adult manhwas found"), parse_mode=ParseMode.MARKDOWN)
        return
    session_id = sessions.create_search_session(
        results, 
        total, 
        "", 
        [manhwa_id], 
        ["erotica", "pornographic"],
        navigation_state="horny"
    )
    sessions.add_navigation_state(session_id, "horny")
    caption, reply_markup = await generate_search_message(session_id)
    await callback.message.edit_text(
        text=caption,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=False
    )
