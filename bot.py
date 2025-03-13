from datetime import datetime
from pytz import timezone
from pyrogram import Client, __version__
from pyrogram.raw.all import layer
from config import Config
from aiohttp import web
from route import web_server
import pyromod
import pyrogram.utils

# Set minimum ID constants
pyrogram.utils.MIN_CHAT_ID = -999999999999
pyrogram.utils.MIN_CHANNEL_ID = -1009999999999

class Bot(Client):
    def __init__(self):
        super().__init__(
            name="renamer",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            bot_token=Config.BOT_TOKEN,
            workers=200,
            plugins={"root": "plugins"},
            sleep_threshold=15,
        )
        self.mention = None
        self.username = None
        self.uptime = Config.BOT_UPTIME

    async def start(self):
        await super().start()
        try:
            me = await self.get_me()
            self.mention = me.mention
            self.username = me.username
            
            print(f"{me.first_name} Is Started.....✨️")
            
            # Notify admins
            for admin_id in Config.ADMIN:
                try:
                    await self.send_message(
                        admin_id,
                        f"**{me.first_name} Is Started...**"
                    )
                except Exception as e:
                    print(f"Failed to notify admin {admin_id}: {str(e)}")
            
            # Start webhook if enabled
            if Config.WEBHOOK:
                try:
                    app = web.AppRunner(await web_server())
                    await app.setup()
                    await web.TCPSite(app, "0.0.0.0", 8080).start()
                    print("Webhook server started on port 8080")
                except Exception as e:
                    print(f"Webhook setup failed: {str(e)}")
            
            # Log channel message
            if Config.LOG_CHANNEL:
                try:
                    curr = datetime.now(timezone("Asia/Kolkata"))
                    date = curr.strftime('%d %B, %Y')
                    time = curr.strftime('%I:%M:%S %p')
                    await self.send_message(
                        Config.LOG_CHANNEL,
                        f"**{me.mention} Is Restarted !!**\n\n"
                        f"📅 Date: `{date}`\n"
                        f"⏰ Time: `{time}`\n"
                        f"🌐 Timezone: `Asia/Kolkata`\n"
                        f"🉐 Version: `v{__version__} (Layer {layer})`"
                    )
                except Exception as e:
                    print(f"Log channel error: {str(e)}")
                    print("Please ensure the bot is an admin in the log channel")
                    
        except Exception as e:
            print(f"Bot startup failed: {str(e)}")
            raise

    async def stop(self):
        await super().stop()
        print("Bot stopped")

if __name__ == "__main__":
    try:
        bot = Bot()
        bot.run()
    except Exception as e:
        print(f"Error running bot: {str(e)}")
