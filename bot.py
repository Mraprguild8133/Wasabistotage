import asyncio
import os
import uuid
import tempfile
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import mimetypes

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.enums import ChatAction
import aiofiles

from database import db
from wasabi_storage import storage

class TelegramFileBot:
    def __init__(self):
        self.app = Client(
            "filebot",
            api_id=os.getenv('API_ID'),
            api_hash=os.getenv('API_HASH'),
            bot_token=os.getenv('BOT_TOKEN')
        )
        
        # Register handlers
        self.setup_handlers()
    
    def setup_handlers(self):
        @self.app.on_message(filters.command("start"))
        async def start_command(client, message: Message):
            await self.save_user_info(message.from_user)
            
            welcome_text = """
🚀 **Welcome to Telegram File Bot!**

📁 **Features:**
• Upload files up to 4GB
• Cloud storage with Wasabi
• MX Player & VLC integration
• File sharing & collaboration
• No expiration links
• Mobile optimized streaming

📋 **Commands:**
/upload - Upload a file
/list - List your files
/search <query> - Search files
/share <file_id> <user_id> - Share file
/stream <file_id> - Get streaming link
/download <file_id> - Download file
/test - Test cloud connection
/help - Show this help

Just send any file to upload it instantly!
            """
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("📤 Upload File", callback_data="upload")],
                [InlineKeyboardButton("📁 My Files", callback_data="list_files")],
                [InlineKeyboardButton("🔍 Search Files", callback_data="search")],
                [InlineKeyboardButton("🔗 Shared Files", callback_data="shared_files")]
            ])
            
            await message.reply_text(welcome_text, reply_markup=keyboard)

        # other commands remain the same ...

    async def generate_download_link(self, message: Message, file_id: str):
        file_data = await db.get_file(file_id)
        if not file_data:
            await message.reply_text("❌ File not found!")
            return

        if file_data['uploader_id'] != message.from_user.id and not file_data['is_public']:
            await message.reply_text("❌ Access denied!")
            return

        download_url = storage.generate_presigned_url(
            file_data['wasabi_key'], 
            expiration=3600,
            response_content_disposition=f'attachment; filename="{file_data["original_name"]}"'
        )

        await db.increment_download_count(file_id)

        if download_url.startswith("http"):
            keyboard = InlineKeyboardMarkup(
                [[InlineKeyboardButton("📥 Download Now", url=download_url)]]
            )
            await message.reply_text(
                f"📥 **Download Ready!**\n\n"
                f"📁 **File:** {file_data['original_name']}\n"
                f"📊 **Size:** {self.format_file_size(file_data['file_size'])}\n"
                f"⏰ **Link expires in 1 hour**",
                reply_markup=keyboard
            )
        else:
            await message.reply_text(f"📥 Download URL: {download_url}")

    async def generate_streaming_link(self, message: Message, file_id: str):
        file_data = await db.get_file(file_id)
        if not file_data:
            await message.reply_text("❌ File not found!")
            return
        if not file_data['mime_type'] or not (
            file_data['mime_type'].startswith('video/') or 
            file_data['mime_type'].startswith('audio/')
        ):
            await message.reply_text("❌ File is not streamable!")
            return

        streaming_url = storage.generate_streaming_url(file_data['wasabi_key'])

        if streaming_url.startswith("http"):
            keyboard = InlineKeyboardMarkup(
                [[InlineKeyboardButton("🎬 Stream Now", url=streaming_url)]]
            )
            await message.reply_text(
                f"🎬 **Streaming Ready!**\n\n"
                f"📁 **File:** {file_data['original_name']}\n"
                f"🎯 **Type:** {file_data['mime_type']}\n"
                f"⏰ **Link expires in 24 hours**",
                reply_markup=keyboard
            )
        else:
            await message.reply_text(f"🎬 Streaming URL: {streaming_url}")

    async def generate_mx_link(self, message: Message, file_id: str):
        file_data = await db.get_file(file_id)
        if not file_data:
            await message.reply_text("❌ File not found!")
            return

        mx_url = storage.get_mx_player_url(file_data['wasabi_key'], file_data['original_name'])

        # send as plain text, not button (Telegram rejects mxplayer://)
        await message.reply_text(
            f"📱 **MX Player Ready!**\n\n"
            f"📁 **File:** {file_data['original_name']}\n"
            f"👉 Open this link in MX Player: {mx_url}"
        )

    async def generate_vlc_link(self, message: Message, file_id: str):
        file_data = await db.get_file(file_id)
        if not file_data:
            await message.reply_text("❌ File not found!")
            return

        vlc_url = storage.get_vlc_url(file_data['wasabi_key'])

        # send as plain text, not button (Telegram rejects vlc://)
        await message.reply_text(
            f"🎯 **VLC Player Ready!**\n\n"
            f"📁 **File:** {file_data['original_name']}\n"
            f"👉 Open this link in VLC: {vlc_url}"
        )

    async def create_temporary_link(self, message: Message, file_id: str):
        file_data = await db.get_file(file_id)
        if not file_data:
            await message.reply_text("❌ File not found!")
            return
        if file_data['uploader_id'] != message.from_user.id:
            await message.reply_text("❌ Access denied!")
            return

        expires_at = datetime.now() + timedelta(hours=24)
        link_id = await db.create_download_link(
            file_id, 
            message.from_user.id, 
            expires_at, 
            max_access=10
        )
        temp_url = f"https://{os.getenv('REPLIT_DEV_DOMAIN', 'localhost:5000')}/d/{link_id}"

        if temp_url.startswith("http") and "localhost" not in temp_url:
            keyboard = InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔗 Open Link", url=temp_url)]]
            )
            await message.reply_text(
                f"🔗 **Temporary Link Created!**\n\n"
                f"📁 **File:** {file_data['original_name']}\n"
                f"⏰ **Expires:** 24 hours\n"
                f"📊 **Max downloads:** 10",
                reply_markup=keyboard
            )
        else:
            await message.reply_text(
                f"🔗 **Temporary Link Created!**\n\n"
                f"📁 **File:** {file_data['original_name']}\n"
                f"👉 Link: {temp_url}\n"
                f"⏰ **Expires:** 24 hours\n"
                f"📊 **Max downloads:** 10"
            )

    # other methods (upload, list, search, etc.) remain unchanged

    def format_file_size(self, size_bytes: int) -> str:
        if size_bytes == 0:
            return "0B"
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        return f"{size_bytes:.1f}{size_names[i]}"

    def start_bot(self):
        print("🚀 Starting Telegram File Bot...")
        self.app.run()

    async def stop(self):
        await self.app.stop()
        print("🛑 Telegram File Bot stopped!")

# Global bot instance
bot = TelegramFileBot()
            
