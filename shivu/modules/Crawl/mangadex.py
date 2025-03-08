from shivu import shivuu;from pyrogram import filters as f,enums,types as t;import asyncio,aiohttp,hashlib,logging,img2pdf,time;from io import BytesIO as B;from PIL import Image as I;from functools import wraps

u=lambda t:t.translate(str.maketrans('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ','ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀsᴛᴜᴠᴡxʏᴢ'*2))
SYM={'d':'▰▱'*5,'li':'▢','ar':'➾','pg':'⫸','bk':'⫷'};s={};p=4

class M:
    def __init__(s):s.s=aiohttp.ClientSession()
    async def q(s,e,p):return await(await s.s.get(f"https://api.mangadex.org/{e}",params=p)).json()
    async def m(s,q,o=0,l=5):
        d=await s.q("manga",{"title":q,"limit":l,"offset":o,"includes[]":"cover_art","order[relevance]":"desc"})
        return [{'id':m['id'],'t':m['attributes']['title'].get('en','?'),'y':m['attributes'].get('year'),'st':str(m['attributes'].get('status','N/A')).capitalize(),'sc':round(m['attributes'].get('rating',{}).get('bayesian',0)*10),'c':f"https://uploads.mangadex.org/covers/{m['id']}/{[r['attributes']['fileName']for r in m['relationships']if r['type']=='cover_art'][0]}",'d':(m['attributes']['description'].get('en','')[:347]+'...')if len(m['attributes']['description'].get('en',''))>350 else m['attributes']['description'].get('en','')}for m in d.get('data',[])],d.get('total',0)
    async def ch(s,i):
        all_chaps=[];o=0
        while 1:
            d=await s.q(f"manga/{i}/feed",{"translatedLanguage[]":"en","order[chapter]":"asc","limit":100,"offset":o});await asyncio.sleep(1.5)
            if not d.get('data'):break
            all_chaps.extend([{'id':x['id'],'ch':x['attributes']['chapter'],'g':[g['attributes']['name']for g in x['relationships']if g['type']=='scanlation_group'][0]}for x in d['data']]);o+=100
        return [dict(y)for y in {f"{x['ch']}-{x['g']}":x for x in all_chaps}.values()]

@shivuu.on_message(f.command("mangadex"))
async def h(_,m):
    q=' '.join(m.command[1:])or await m.reply(u("provide manga name"));r,t=await M().m(q);k:=hashlib.md5(f"{q}{time.time()}".encode()).hexdigest()[:8];s[k]={'r':r,'t':t,'o':0,'q':q}
    await m.reply(f"**{u('search results')}**\n{SYM['d']}\n"+'\n'.join([f"{i+1}. [{x['t']}]({x['c']})\n★ {x['sc']}/100"for i,x in enumerate(r)]),reply_markup=t.InlineKeyboardMarkup([[t.InlineKeyboardButton(f"{i+1}. {x['t'][:25]}",f"srch:{k}:{i}")]for i,x in enumerate(r)]+[[t.InlineKeyboardButton(SYM['bk'],f"pg:{k}:prev"),t.InlineKeyboardButton(SYM['pg'],f"pg:{k}:next")]if t>5 else[]]))

@shivuu.on_callback_query(f.regex(r"^pg:"))
async def p(_,q):
    k,dr=q.data.split(':')[1:];o=s[k]['o']+(-5 if dr=='prev'else5);r,t=await M().m(s[k]['q'],o);s[k].update(r=r,o=o,t=t)
    await q.message.edit_reply_markup(t.InlineKeyboardMarkup([[t.InlineKeyboardButton(f"{i+1}. {x['t'][:25]}",f"srch:{k}:{i}")]for i,x in enumerate(r)]+[[t.InlineKeyboardButton(SYM['bk'],f"pg:{k}:prev"),t.InlineKeyboardButton(SYM['pg'],f"pg:{k}:next")]if t>5 else[]]))

@shivuu.on_callback_query(f.regex(r"^srch:"))
async def s(_,q):
    k,i=q.data.split(':')[1:];m=s[k]['r'][int(i)];c=await M().ch(m['id']);chk=hashlib.md5(m['id'].encode()).hexdigest()[:8];s[chk]={'c':c,'ts':time.time(),'prev':k,'mn':m['t'],'cv':m['c']}
    await q.message.edit(f"**[{m['t']}]({m['c']})**\n{SYM['d']}\n{SYM['li']} Status: {m['st']}\n{SYM['li']} Year: {m['y']}\n{SYM['d']}\n{m['d']}",reply_markup=t.InlineKeyboardMarkup([[t.InlineKeyboardButton(f"Ch.{x['ch']}|{x['g'][:10]}",f"dl:{chk}:{x['id']}:{x['ch']}")]for x in c[:8]]+[[t.InlineKeyboardButton("🔙",f"bk:{k}")]]))

@shivuu.on_callback_query(f.regex(r"^bk:"))
async def b(_,q):
    k=q.data.split(':')[1];await q.message.edit_reply_markup(t.InlineKeyboardMarkup([[t.InlineKeyboardButton(f"{i+1}. {x['t'][:25]}",f"srch:{k}:{i}")]for i,x in enumerate(s[k]['r'])]+[[t.InlineKeyboardButton(SYM['bk'],f"pg:{k}:prev"),t.InlineKeyboardButton(SYM['pg'],f"pg:{k}:next")]if s[k]['t']>5 else[]]))

@shivuu.on_callback_query(f.regex(r"^dl:"))
async def d(_,q):
    k,chid,chn=q.data.split(':')[1:];c=s[k]['c'];cv=s[k]['cv'];mn=s[k]['mn'];pr=0;pm=await q.message.reply(f"**📥 Downloading**\n{SYM['d']}\n{SYM['li']} 0%")
    async with aiohttp.ClientSession() as s,a ThreadPoolExecutor(p)as e:
        cr=await s.get(cv);cover=await cr.read();imgs=[I.open(B(cover)).convert('RGB')]
        for idx,x in enumerate([x for x in c if x['id']==chid][:50]):
            r=await s.get(f"https://uploads.mangadex.org/data/{x['id']}");imgs.append(await asyncio.get_event_loop().run_in_executor(e,lambda:I.open(B(await r.read()).convert('RGB')))
            if (pr:=int((idx+1)/50*100))%20==0:await pm.edit(f"**📥 Downloading**\n{SYM['d']}\n{SYM['li']} {pr}%")
        pdf=B();pdf.write(img2pdf.convert([x.tobytes()for x in imgs]));pdf.seek(0)
        await q.message.reply_document(pdf,file_name=f"Ch - {chn} {mn[:40].replace(' ','_')}.pdf",thumb=cover)
    await pm.delete()
