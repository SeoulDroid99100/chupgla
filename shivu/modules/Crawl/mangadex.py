from shivu import shivuu;from pyrogram import filters as f,enums,types as t;import asyncio,aiohttp,hashlib,logging,img2pdf,time,os;from io import BytesIO as B;from PIL import Image as I;from functools import wraps

u=lambda t:t.translate(str.maketrans('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ','ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀsᴛᴜᴠᴡxʏᴢ'*2))
SYM={'d':'▰▱'*5,'li':'▢','pg':'⫸','bk':'⫷'};s={}

class M:
    def __init__(s):s.s=aiohttp.ClientSession()
    async def q(s,e,p):return await(await s.s.get(f"https://api.mangadex.org/{e}",params=p)).json()
    async def m(s,q,o=0):
        d=await s.q("manga",{"title":q,"limit":5,"offset":o,"includes[]":"cover_art","order[relevance]":"desc"})
        return [{'id':m['id'],'t':m['attributes']['title'].get('en','?'),'c':f"https://uploads.mangadex.org/covers/{m['id']}/{[r['attributes']['fileName']for r in m['relationships']if r['type']=='cover_art'][0]}"}for m in d.get('data',[])],d.get('total',0)
    async def ch(s,i):
        all_chaps=[];o=0
        while 1:
            d=await s.q(f"manga/{i}/feed",{"translatedLanguage[]":"en","order[chapter]":"asc","limit":100,"offset":o})
            if not d.get('data'):break
            all_chaps.extend([{'id':x['id'],'ch':x['attributes']['chapter'],'g':[g['attributes']['name']for g in x['relationships']if g['type']=='scanlation_group'][0]}for x in d['data']])
            o+=100;await asyncio.sleep(1.5)
        return [dict(y)for y in {f"{x['ch']}-{x['g']}":x for x in all_chaps}.values()]

@shivuu.on_callback_query(f.regex(r"^dl:"))
async def d(_,q):
    k,chid,chn=q.data.split(':')[1:];c=s[k]['c'];mn=s[k]['mn'];pr=0;imgs=[];cover=B()
    
    # Get cover thumbnail
    async with aiohttp.ClientSession() as session:
        async with session.get(s[k]['cv']) as r:
            cover.write(await r.read())
            cover.seek(0)
            thumb=I.open(cover).convert('RGB').resize((320,480))
    
    # Download chapter images
    async with aiohttp.ClientSession() as session:
        total=len([x for x in c if x['id']==chid][:50])
        for idx,x in enumerate([x for x in c if x['id']==chid][:50]):
            async with session.get(f"https://uploads.mangadex.org/data/{x['id']}")as r:
                imgs.append(await asyncio.to_thread(lambda:I.open(B(await r.read()).convert('RGB')))
                # Progress update every 20%
                if (pr:=int((idx+1)/total*100))//20 > pr//20:
                    await q.message.edit(f"**📥 Downloading**\n{SYM['d']}\n{SYM['li']} Progress: {pr}%")
    
    # PDF generation with cover
    with B() as pdf_buf,B() as thumb_buf:
        thumb.save(thumb_buf,format='JPEG')
        pdf_buf.write(img2pdf.convert([thumb_buf.getvalue()]+[x.tobytes()for x in imgs]))
        pdf_buf.seek(0)
        await q.message.reply_document(
            document=pdf_buf,
            file_name=f"Ch - {chn} {mn.replace(' ','_')[:40]}.pdf",
            thumb=thumb_buf.getvalue()
        )
    
    await q.message.edit_reply_markup(t.InlineKeyboardMarkup([[t.InlineKeyboardButton(f"✅ Ch.{chn} Complete",'noop')]]))

@shivuu.on_callback_query(f.regex(r"^srch:"))
async def s(_,q):
    k,i=q.data.split(':')[1:];m=s[k]['r'][int(i)];c=await M().ch(m['id']);chk=hashlib.md5(m['id'].encode()).hexdigest()[:8]
    s[chk]={'c':c,'ts':time.time(),'prev':k,'mn':m['t'],'cv':m['c']}  # Store manga name and cover
    btn=[[t.InlineKeyboardButton(f"Ch.{x['ch']} | {x['g'][:10]}",f"dl:{chk}:{x['id']}:{x['ch']}")]for x in c[:8]]
    btn+=[[t.InlineKeyboardButton("🔙 Back",f"bk:{k}")]]
    await q.message.edit(f"**{m['t']}**\n{SYM['d']}\nSelect Chapter:",reply_markup=t.InlineKeyboardMarkup(btn))
