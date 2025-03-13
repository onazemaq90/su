from pyrogram import Client, filters
from pyrogram.enums import MessageMediaType
from pyrogram.errors import FloodWait
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ForceReply
from hachoir.metadata import extractMetadata
from helper.ffmpeg import fix_thumb, take_screen_shot, add_metadata
from hachoir.parser import createParser
from helper.utils import progress_for_pyrogram, convert, humanbytes, add_prefix_suffix
from helper.database import jishubotz
from asyncio import sleep
from PIL import Image
import os, time, re, random, asyncio

# Initial file handler
@Client.on_message(filters.private & (filters.document | filters.audio | filters.video))
async def rename_start(client, message):
    file = getattr(message, message.media.value)
    filename = file.file_name
    
    if file.file_size > 2000 * 1024 * 1024:
        return await message.reply_text("Sorry, this bot doesn't support files larger than 2GB")
    
    try:
        await message.reply_text(
            text=f"**Please Enter New Filename**\n\n**Original Name:** `{filename}`",
            reply_to_message_id=message.id,
            reply_markup=ForceReply(True)
        )
    except FloodWait as e:
        await sleep(e.value)
        await message.reply_text(
            text=f"**Please Enter New Filename**\n\n**Original Name:** `{filename}`",
            reply_to_message_id=message.id,
            reply_markup=ForceReply(True)
        )
    except Exception as e:
        await message.reply_text(f"Error occurred: {str(e)}")

# Handle reply with new filename
@Client.on_message(filters.private & filters.reply)
async def refunc(client, message):
    reply_message = message.reply_to_message
    if not (reply_message.reply_markup and isinstance(reply_message.reply_markup, ForceReply)):
        return

    new_name = message.text.strip()
    if not new_name:
        return await message.reply_text("Please provide a valid filename")

    await message.delete()
    msg = await client.get_messages(message.chat.id, reply_message.id)
    file = msg.reply_to_message
    media = getattr(file, file.media.value)

    # Add file extension if missing
    if "." not in new_name:
        extn = media.file_name.rsplit('.', 1)[-1] if '.' in media.file_name else "mkv"
        new_name = f"{new_name}.{extn}"

    await reply_message.delete()

    buttons = [[InlineKeyboardButton("📁 Document", callback_data="upload_document")]]
    if file.media in [MessageMediaType.VIDEO, MessageMediaType.DOCUMENT]:
        buttons.append([InlineKeyboardButton("🎥 Video", callback_data="upload_video")])
    elif file.media == MessageMediaType.AUDIO:
        buttons.append([InlineKeyboardButton("🎵 Audio", callback_data="upload_audio")])

    await message.reply(
        text=f"**Select Output File Type**\n\n**File Name:** `{new_name}`",
        reply_to_message_id=file.id,
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# Handle upload callback
@Client.on_callback_query(filters.regex("upload"))
async def doc(bot, update):
    if not os.path.exists("Metadata"):
        os.makedirs("Metadata", exist_ok=True)

    try:
        new_name = update.message.text.split(":-")[1].strip()
        prefix = await jishubotz.get_prefix(update.message.chat.id)
        suffix = await jishubotz.get_suffix(update.message.chat.id)
        new_filename = add_prefix_suffix(new_name, prefix, suffix)
    except Exception as e:
        return await update.message.edit(f"Error setting prefix/suffix: {str(e)}\nContact @CallAdminRobot")

    file_path = f"downloads/{update.from_user.id}/{new_filename}"
    file = update.message.reply_to_message
    ms = await update.message.edit("🚀 Downloading...")

    try:
        path = await bot.download_media(
            message=file,
            file_name=file_path,
            progress=progress_for_pyrogram,
            progress_args=("🚀 Downloading...", ms, time.time())
        )
    except Exception as e:
        return await ms.edit(f"Download failed: {str(e)}")

    # Handle metadata
    use_metadata = await jishubotz.get_metadata(update.message.chat.id)
    metadata_path = f"Metadata/{new_filename}" if use_metadata else None

    if use_metadata:
        try:
            metadata = await jishubotz.get_metadata_code(update.message.chat.id)
            await add_metadata(path, metadata_path, metadata, ms)
        except Exception as e:
            await ms.edit(f"Metadata error: {str(e)}")
            return

    # Get duration
    duration = 0
    try:
        with createParser(file_path) as parser:
            metadata = extractMetadata(parser)
            if metadata and metadata.has("duration"):
                duration = metadata.get('duration').seconds
    except Exception:
        pass

    # Handle thumbnail
    media = getattr(file, file.media.value)
    c_caption = await jishubotz.get_caption(update.message.chat.id)
    c_thumb = await jishubotz.get_thumbnail(update.message.chat.id)
    ph_path = None

    caption = (c_caption.format(
        filename=new_filename,
        filesize=humanbytes(media.file_size),
        duration=convert(duration)
    ) if c_caption else f"**{new_filename}**") or f"**{new_filename}**"

    if media.thumbs or c_thumb:
        try:
            if c_thumb:
                ph_path = await bot.download_media(c_thumb)
            else:
                ph_path = await take_screen_shot(
                    file_path,
                    os.path.dirname(os.path.abspath(file_path)),
                    random.randint(0, max(0, duration - 1))
                )
            width, height, ph_path = await fix_thumb(ph_path)
        except Exception as e:
            ph_path = None
            print(f"Thumbnail error: {e}")

    # Upload
    await ms.edit("💠 Uploading...")
    upload_type = update.data.split("_")[1]

    try:
        upload_path = metadata_path if use_metadata else file_path
        upload_args = {
            'chat_id': update.message.chat.id,
            'caption': caption,
            'thumb': ph_path,
            'progress': progress_for_pyrogram,
            'progress_args': ("💠 Uploading...", ms, time.time())
        }

        if upload_type == "document":
            await bot.send_document(document=upload_path, **upload_args)
        elif upload_type == "video":
            await bot.send_video(video=upload_path, duration=duration, **upload_args)
        elif upload_type == "audio":
            await bot.send_audio(audio=upload_path, duration=duration, **upload_args)

    except Exception as e:
        await ms.edit(f"Upload failed: {str(e}}")
        return cleanup(file_path, ph_path)

    await ms.delete()
    cleanup(file_path, ph_path)

def cleanup(file_path, ph_path=None):
    """Clean up temporary files"""
    try:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
        if ph_path and os.path.exists(ph_path):
            os.remove(ph_path)
    except Exception:
        pass
