from datetime import datetime
from pytz import timezone
from pyrogram import Client, __version__
from pyrogram.raw.all import layer
from pyrogram.errors import exceptions  # Added for better error handling
from config import Config
from aiohttp import web
from route import web_server
import pyromod
import pyrogram.utils
import logging  # Added for better logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
MIN_CHAT_ID = -999999999999
MIN_CHANNEL_ID = -1009999999999
pyrogram.utils.MIN_CHAT_ID = MIN_CHAT_ID
pyrogram.utils.MIN_CHANNEL_ID = MIN_CHANNEL_ID

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
        self.uptime = Config.BOT_UPTIME

    async def start(self):
        try:
            await super().start()
            me = await self.get_me()
            self.mention = me.mention
            self.username = me.username

            # Setup webhook if enabled
            if Config.WEBHOOK:
                try:
                    app = web.AppRunner(await web_server())
                    await app.setup()
                    await web.TCPSite(app, "0.0.0.0", 8080).start()
                    logger.info("Webhook server started successfully")
                except Exception as e:
                    logger.error(f"Failed to start webhook server: {str(e)}")

            logger.info(f"{me.first_name} Bot is started successfully")

            # Notify admins
            for admin_id in Config.ADMIN:
                try:
                    await self.send_message(admin_id, f"**{me.first_name} Bot is now online**")
                except Exception as e:
                    logger.warning(f"Failed to notify admin {admin_id}: {str(e)}")

            # Log channel notification
            if Config.LOG_CHANNEL:
                try:
                    curr = datetime.now(timezone("Asia/Kolkata"))
                    await self._send_startup_log(me, curr)
                except Exception as e:
                    logger.error(f"Failed to send startup log: {str(e)}")

        except Exception as e:
            logger.error(f"Failed to start bot: {str(e)}")
            raise

    async def _send_startup_log(self, me, curr):
        """Send startup notification to log channel"""
        date = curr.strftime('%d %B, %Y')
        time = curr.strftime('%I:%M:%S %p')
        
        log_message = (
            f"**{me.mention} Bot Status Update**\n\n"
            f"📅 Date: `{date}`\n"
            f"⏰ Time: `{time}`\n"
            f"🌐 Timezone: `Asia/Kolkata`\n"
            f"🉐 Version: `v{__version__} (Layer {layer})`"
        )
        
        await self.send_message(Config.LOG_CHANNEL, log_message)

def main():
    try:
        logger.info("Starting bot...")
        Bot().run()
    except Exception as e:
        logger.error(f"Failed to run bot: {str(e)}")
        raise

if __name__ == "__main__":
    main()
