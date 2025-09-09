#!/usr/bin/env python3

import os
import asyncio
import signal
import sys

# Set environment variables (use Replit secrets if available, otherwise fallback)
if not os.getenv('API_ID'):
    os.environ['API_ID'] = '21102617'
if not os.getenv('API_HASH'):
    os.environ['API_HASH'] = '31de0d24a6b8048c48730bc420f4b70c'
if not os.getenv('BOT_TOKEN'):
    os.environ['BOT_TOKEN'] = '8406796286:AAG-AvbST58ZYwD9IgOd7bu9nCnZNEtofKI'
if not os.getenv('WASABI_ACCESS_KEY'):
    os.environ['WASABI_ACCESS_KEY'] = '1R6V3YS9HFQPEW9QS81H'
if not os.getenv('WASABI_SECRET_KEY'):
    os.environ['WASABI_SECRET_KEY'] = 'pWHDJM6eH8TJo8Pd2e3h7zZzMLWIY1nK62eci1yy'
if not os.getenv('WASABI_BUCKET'):
    os.environ['WASABI_BUCKET'] = 'nraprguild3'
if not os.getenv('WASABI_REGION'):
    os.environ['WASABI_REGION'] = 'ap-northeast-1'
if not os.getenv('STORAGE_CHANNEL_ID'):
    os.environ['STORAGE_CHANNEL_ID'] = '-1003004425377'

print("🚀 Starting Telegram File Bot...")

try:
    from main import TelegramFileBot
    from web_interface import WebInterface
    from aiohttp import web
    import aiohttp
    
    bot = None
    web_app = None
    
    async def start_bot():
        global bot, web_app
        
        print("📱 Initializing Telegram Bot...")
        bot = TelegramFileBot()
        
        print("🌐 Starting Web Interface...")
        web_app = bot.web_app.app
        
        # Start both bot and web server
        print("🔄 Starting services...")
        
        # Start web server
        runner = web.AppRunner(web_app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', 5000)
        await site.start()
        print("✅ Web interface started on http://0.0.0.0:5000")
        
        # Start Telegram bot
        await bot.app.start()
        print("✅ Telegram bot started successfully!")
        
        print("🎉 All services running!")
        print("📝 Available commands:")
        print("   /start - Welcome message")
        print("   /help - Help information")  
        print("   /test - Test Wasabi connection")
        print("   /upload - Upload files")
        print("   /list - List files")
        print("   /stream <file_id> - Stream files")
        print("   /web <file_id> - Web player")
        print("")
        print("🌐 Web interface: http://0.0.0.0:5000")
        print("📱 Bot is ready to receive files!")
        
        # Keep running
        await asyncio.sleep(float('inf'))
    
    def signal_handler(signum, frame):
        print("\n🛑 Stopping services...")
        if bot:
            asyncio.create_task(bot.app.stop())
        sys.exit(0)
    
    # Handle graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run the bot
    asyncio.run(start_bot())
    
except KeyboardInterrupt:
    print("\n🛑 Bot stopped by user")
except Exception as e:
    print(f"❌ Error starting bot: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
