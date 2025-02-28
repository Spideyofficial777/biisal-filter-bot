import sys
import glob
import importlib
import asyncio
import logging
import logging.config
from pathlib import Path
from pyrogram import idle, Client, __version__, filters
from pyrogram.raw.all import layer
from database.ia_filterdb import Media
from database.users_chats_db import db
from info import *
from utils import temp
from typing import Union, Optional, AsyncGenerator
from pyrogram import types
from Script import script
from datetime import date, datetime
import pytz
from aiohttp import web
from plugins import web_server, check_expired_premium
import time


logging.config.fileConfig('logging.conf')
logging.getLogger().setLevel(logging.INFO)
logging.getLogger("pyrogram").setLevel(logging.ERROR)
logging.getLogger("aiohttp").setLevel(logging.ERROR)
logging.getLogger("aiohttp.web").setLevel(logging.ERROR)

# Spidey 
from Spidey.bot import SpideyBot
from Spidey.util.keepalive import ping_server
from Spidey.bot.clients import initialize_clients


ppath = "plugins/*.py"
files = glob.glob(ppath)
loop = asyncio.get_event_loop()
SpideyBot.start()

async def Spidey_start():
    print("\nInitializing Spidey Bot...")
    
    bot_info = await SpideyBot.get_me()
    SpideyBot.username = bot_info.username

    await initialize_clients()

    for name in files:
        with open(name) as a:
            patt = Path(a.name)
            plugin_name = patt.stem.replace(".py", "")
            plugins_dir = Path(f"plugins/{plugin_name}.py")
            import_path = f"plugins.{plugin_name}"
            spec = importlib.util.spec_from_file_location(import_path, plugins_dir)
            load = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(load)
            sys.modules[f"plugins.{plugin_name}"] = load
            print(f"Spidey Bot Imported => {plugin_name}")

    if ON_HEROKU:
        asyncio.create_task(ping_server())


    b_users, b_chats = await db.get_banned()
    temp.BANNED_USERS = b_users
    temp.BANNED_CHATS = b_chats

    await Media.ensure_indexes()

    me = await SpideyBot.get_me()
    temp.ME = me.id
    temp.U_NAME = me.username
    temp.B_NAME = me.first_name
    temp.B_LINK = me.mention
    SpideyBot.username = f"@{me.username}"

    logging.info(f"{me.first_name} (Pyrogram v{__version__} | Layer {layer}) started as {me.username}.")
    logging.info(script.LOGO)

   
    tz = pytz.timezone("Asia/Kolkata")
    today = date.today()
    now = datetime.now(tz)
    time_str = now.strftime("%H:%M:%S %p")

    # Send Restart Messages
    await SpideyBot.send_message(chat_id=LOG_CHANNEL, text=script.RESTART_TXT.format(me.mention, today, time_str))
    await SpideyBot.send_message(chat_id=SUPPORT_GROUP, text=f"<b>{me.mention} ʀᴇsᴛᴀʀᴛᴇᴅ 🤖</b>")

   
    app = web.AppRunner(await web_server())
    await app.setup()
    bind_address = "0.0.0.0"
    await web.TCPSite(app, bind_address, PORT).start()

    await idle()


    for admin in ADMINS:
        await SpideyBot.send_message(chat_id=admin, text=f"<b>{me.mention} ʙᴏᴛ ʀᴇsᴛᴀʀᴛᴇᴅ ✅</b>")

if __name__ == '__main__':
    try:
        loop.run_until_complete(Spidey_start())
    except KeyboardInterrupt:
        logging.info("Service Stopped. Bye 👋")
