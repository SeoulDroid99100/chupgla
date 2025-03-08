from shivu import shivuu
from pyrogram import filters as f, enums, types as t
import asyncio, aiohttp, hashlib, logging, img2pdf, time
from io import BytesIO
from PIL import Image
from functools import partial

# Small caps translation and symbols
u = str.maketrans('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ', 
                 'ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀsᴛᴜᴠᴡxʏᴢ'*2)
SYM = {'d': '▰▱'*5, 'li': '▢', 'pg': '⫸', 'bk': '⫷'}

sessions = {}

class MangaClient:
    def __init__(self):
        self.session = aiohttp.ClientSession()
    
    async def fetch(self, endpoint, params):
        async with self.session.get(f"https://api.mangadex.org/{endpoint}", params=params) as res:
            return await res.json() if res.status == 200 else {}

    async def search(self, query, offset=0):
        params = {
            "title": query, 
            "limit": 5, 
            "offset": offset,
            "includes[]": ["cover_art"],
            "order[relevance]": "desc"
        }
        data = await self.fetch("manga", params)
        return [
            {
                'id': m['id'],
                'title': m['attributes']['title'].get('en', '?'),
                'cover': f"https://uploads.mangadex.org/covers/{m['id']}/"
                        f"{next(r['attributes']['fileName'] for r in m['relationships'] if r['type'] == 'cover_art')}"
            } for m in data.get('data', [])
        ], data.get('total', 0)

    async def chapters(self, manga_id):
        all_chaps = []
        offset = 0
        while True:
            params = {
                "translatedLanguage[]": "en",
                "order[chapter]": "asc",
                "limit": 100,
                "offset": offset
            }
            data = await self.fetch(f"manga/{manga_id}/feed", params)
            if not data.get('data'):
                break
            all_chaps.extend([
                {
                    'id': x['id'],
                    'chapter': x['attributes']['chapter'],
                    'group': next(g['attributes']['name'] for g in x['relationships'] if g['type'] == 'scanlation_group')
                } for x in data['data']
            ])
            offset += 100
            await asyncio.sleep(1.5)
        return {f"{c['chapter']}-{c['group']}": c for c in all_chaps}.values()

@shivuu.on_callback_query(f.regex(r"^dl:"))
async def download_handler(_, query):
    try:
        _, session_id, ch_id, ch_num = query.data.split(':')
        data = sessions.get(session_id, {})
        if not data:
            await query.answer("Session expired!")
            return

        manga_title = data['title']
        cover_url = data['cover']
        chapters = data['chapters']
        
        # Get target chapter
        chapter = next((c for c in chapters if c['id'] == ch_id), None)
        if not chapter:
            await query.answer("Chapter not found!")
            return

        # Send initial progress message
        progress_msg = await query.message.reply("**📥 Download Started**\n▰▱▰▱▰▱▰▱▰▱\nProgress: 0%")

        async with aiohttp.ClientSession() as http:
            # Download cover
            async with http.get(cover_url) as resp:
                cover_img = await resp.read()
            
            # Download chapter pages
            images = []
            total_pages = 50  # Example limit
            for idx in range(1, total_pages+1):
                # Simulated download - replace with actual image URLs
                async with http.get(f"https://uploads.mangadex.org/data/{ch_id}/{idx}") as resp:
                    images.append(await resp.read())
                
                # Update progress every 20%
                if idx % (total_pages//5) == 0:
                    progress = int((idx/total_pages)*100)
                    await progress_msg.edit(
                        f"**📥 Downloading**\n{SYM['d']}\n"
                        f"{SYM['li']} Progress: {progress}%"
                    )

            # Create PDF
            pdf_buffer = BytesIO()
            with ThreadPoolExecutor() as executor:
                # Process images in parallel
                process_image = partial(Image.open(BytesIO).convert('RGB'))
                images = await asyncio.get_event_loop().run_in_executor(
                    executor, 
                    lambda: [process_image(img) for img in images]
                )
                
                # Add cover as first page
                cover = Image.open(BytesIO(cover_img)).convert('RGB')
                images.insert(0, cover)
                
                # Generate PDF
                pdf_buffer.write(img2pdf.convert([img.tobytes() for img in images]))
                pdf_buffer.seek(0)

            # Send final document
            await query.message.reply_document(
                document=pdf_buffer,
                file_name=f"Ch - {ch_num} {manga_title[:40].translate(str.maketrans(' ', '_'))}.pdf",
                thumb=cover_img
            )
            await progress_msg.delete()

    except Exception as e:
        logging.error(f"Download error: {str(e)}")
        await query.message.reply(f"🚫 Error: {str(e)}")
    finally:
        if 'http' in locals():
            await http.close()

@shivuu.on_callback_query(f.regex(r"^srch:"))
async def search_handler(_, query):
    try:
        _, session_id, idx = query.data.split(':')
        session = sessions.get(session_id)
        if not session:
            await query.answer("Session expired!")
            return

        manga = session['results'][int(idx)]
        client = MangaClient()
        chapters = await client.chapters(manga['id'])
        
        # Store chapter data
        ch_session = hashlib.md5(manga['id'].encode()).hexdigest()[:8]
        sessions[ch_session] = {
            'chapters': list(chapters),
            'title': manga['title'],
            'cover': manga['cover'],
            'timestamp': time.time()
        }

        # Create buttons
        buttons = [
            [t.InlineKeyboardButton(
                f"Ch.{c['chapter']} | {c['group'][:10]}", 
                callback_data=f"dl:{ch_session}:{c['id']}:{c['chapter']}"
            )] for c in list(chapters)[:8]
        ]
        buttons.append([t.InlineKeyboardButton("🔙 Back", callback_data=f"bk:{session_id}")])

        await query.message.edit(
            text=f"**{manga['title']}**\n{SYM['d']}\nSelect Chapter:",
            reply_markup=t.InlineKeyboardMarkup(buttons)
        )

    except Exception as e:
        logging.error(f"Search handler error: {str(e)}")
        await query.answer("Operation failed!")

@shivuu.on_callback_query(f.regex(r"^bk:"))
async def back_handler(_, query):
    try:
        _, session_id = query.data.split(':')
        session = sessions.get(session_id)
        if session:
            await query.message.edit(
                text=query.message.text,
                reply_markup=session['original_markup']
            )
    except Exception as e:
        logging.error(f"Back handler error: {str(e)}")
        await query.answer("Couldn't return to previous menu")
