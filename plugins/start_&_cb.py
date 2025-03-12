# Standard library imports
import random

# Third party imports
from pyrogram import Client, filters
from pyrogram.types import (
    InlineKeyboardButton, 
    InlineKeyboardMarkup, 
    ForceReply, 
    CallbackQuery
)

# Local imports
from helper.database import jishubotz
from config import Config, Txt

@Client.on_message(filters.private & filters.command("start"))
async def start_command(client, message):
    """
    Handle /start command in private chats.
    
    Args:
        client: The Pyrogram client instance
        message: The message object containing the command
    """
    # Get user info
    user = message.from_user
    
    # Add user to database
    await jishubotz.add_user(client, message)
    
    # Create keyboard markup
    keyboard = [
        [
            InlineKeyboardButton('🔊 Updates', url='https://t.me/Madflix_Bots'),
            InlineKeyboardButton('♻️ Support', url='https://t.me/MadflixBots_Support')
        ],
        [
            InlineKeyboardButton('❤️‍🩹 About', callback_data='about'),
            InlineKeyboardButton('🛠️ Help', callback_data='help')
        ],
        [
            InlineKeyboardButton("👨‍💻 Developer", url='https://t.me/CallAdminRobot')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Send response
    if Config.START_PIC:
        await message.reply_photo(
            photo=Config.START_PIC,
            caption=Txt.START_TXT.format(user.mention),
            reply_markup=reply_markup
        )
    else:
        await message.reply_text(
            text=Txt.START_TXT.format(user.mention),
            reply_markup=reply_markup,
            disable_web_page_preview=True
	)
	    
@Client.on_callback_query()
async def handle_callbacks(client, query: CallbackQuery):
    """
    Handle callback queries from inline keyboard buttons.
    
    Args:
        client: The Pyrogram client instance
        query: The callback query object
    """
    try:
        data = query.data
        
        if data == "start":
            keyboard = [
                [
                    InlineKeyboardButton('🔊 Updates', url='https://t.me/Madflix_Bots'),
                    InlineKeyboardButton('♻️ Support', url='https://t.me/MadflixBots_Support')
                ],
                [
                    InlineKeyboardButton('❤️‍🩹 About', callback_data='about'),
                    InlineKeyboardButton('🛠️ Help', callback_data='help')
                ],
                [
                    InlineKeyboardButton("👨‍💻 Developer", url='https://t.me/CallAdminRobot')
                ]
            ]
            await query.message.edit_text(
                text=Txt.START_TXT.format(query.from_user.mention),
                disable_web_page_preview=True,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
        elif data == "help":
            keyboard = [
                [
                    InlineKeyboardButton("⚡ 4GB Rename Bot", url="https://t.me/FileRenameXProBot")
                ],
                [
                    InlineKeyboardButton("🔒 Close", callback_data="close"),
                    InlineKeyboardButton("◀️ Back", callback_data="start")
                ]
            ]
            await query.message.edit_text(
                text=Txt.HELP_TXT,
                disable_web_page_preview=True,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
        elif data == "about":
            keyboard = [
                [
                    InlineKeyboardButton("🤖 More Bots", url="https://t.me/Madflix_Bots/7")
                ],
                [
                    InlineKeyboardButton("🔒 Close", callback_data="close"),
                    InlineKeyboardButton("◀️ Back", callback_data="start")
                ]
            ]
            await query.message.edit_text(
                text=Txt.ABOUT_TXT.format(client.mention),
                disable_web_page_preview=True,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
        elif data == "close":
            await handle_close_callback(query)

    except Exception as e:
        print(f"Error in callback handler: {e}")
        await query.answer("An error occurred!", show_alert=True)

async def handle_close_callback(query: CallbackQuery):
    """
    Handle the close callback by deleting messages.
    
    Args:
        query: The callback query object
    """
    try:
        await query.message.delete()
        if query.message.reply_to_message:
            await query.message.reply_to_message.delete()
    except Exception as e:
        print(f"Error in close callback: {e}")
    finally:
        await query.message.continue_propagation()
	    
@Client.on_message(filters.private & filters.command(["donate", "d"]))
async def donate_command(client, message):
    """
    Handle donation command.
    
    Args:
        client: The Pyrogram client instance
        message: The message object containing the command
    """
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🦋 Admin", url="https://t.me/CallAdminRobot"),
            InlineKeyboardButton("✖️ Close", callback_data="close")
        ]
    ])
    
    await message.reply_text(
        text=Txt.DONATE_TXT,
        reply_markup=keyboard)
	
