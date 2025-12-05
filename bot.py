import os
import asyncio
import logging
import time
from pyrogram import Client, filters
from pyrogram.types import Message

from config import API_ID, API_HASH, BOT_TOKEN, BOT_CREATOR, BOT_NAME, is_owner, OWNER_ID
from core.database import db
from core.logger import setup_logger
from core.background_tasks import BackgroundTasks
from core.monitoring import BotMonitor, MetricsCollector, AlertManager
from core.limit_manager import limit_manager

from handlers.start import register_start_handlers
from handlers.menu import register_menu_handlers
from handlers.verify import register_verify_handlers
from handlers.redeem import register_redeem_handlers
from handlers.owner import register_owner_handlers, handle_owner_input

from handlers.file_commands.buat_admin_navy import register_admin_navy_handlers, handle_admin_navy_input
from handlers.file_commands.split_file import register_split_handlers, handle_split_file
from handlers.file_commands.gabung_file import register_gabung_handlers, handle_gabung_file
from handlers.file_commands.msg_to_txt import register_msg_to_txt_handlers, handle_msg_to_txt
from handlers.file_commands.txt_to_vcf import register_txt_to_vcf_handlers, handle_txt_to_vcf
from handlers.file_commands.vcf_to_txt import register_vcf_to_txt_handlers, handle_vcf_to_txt
from handlers.file_commands.xlsx_to_vcf import register_xlsx_to_vcf_handlers, handle_xlsx_to_vcf
from handlers.file_commands.rapikan_txt import register_rapikan_handlers, handle_rapikan_txt
from handlers.file_commands.hitung_kontak import register_hitung_handlers, handle_hitung_kontak
from handlers.file_commands.cek_nama_kontak import register_cek_nama_handlers, handle_cek_nama

logger = setup_logger("bot", "bot.log")

monitor = BotMonitor()


def print_startup_banner():
    print("\n" + "=" * 50)
    print("⏳ KIFZL DEV BOT V2 PYROGRAM Initializing...")
    print("=" * 50 + "\n")
    print("📦 Loading modules...")
    print(f"👨‍💻 Created by: {BOT_CREATOR}")
    print(f"🤖 Bot Name: {BOT_NAME}")
    print("✅ Using Pyrogram v2 + SQLite")
    print("✅ Multi-bot Management System")
    print("✅ Comprehensive Monitoring")
    print("=" * 50 + "\n")


async def main():
    print_startup_banner()

    if not BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not found in environment variables!")
        print("❌ TELEGRAM_BOT_TOKEN tidak ditemukan!")
        print("Silakan set environment variable TELEGRAM_BOT_TOKEN")
        return

    if not API_ID or not API_HASH:
        logger.error("API_ID or API_HASH not found!")
        print("❌ API_ID atau API_HASH tidak ditemukan!")
        print("Silakan set environment variable API_ID dan API_HASH")
        return

    logger.info("Connecting to database...")
    await db.connect()
    logger.info("Database connected!")

    from core.bot_manager import bot_manager
    await bot_manager.initialize()
    logger.info("Bot manager initialized!")
    
    status_result = await bot_manager.check_all_bots_status()
    if status_result.get('bots'):
        print(f"🤖 Multi-bot status: {status_result['online']} ONLINE, {status_result['offline']} OFFLINE")

    app = Client(
        "kifzl_bot",
        api_id=API_ID,
        api_hash=API_HASH,
        bot_token=BOT_TOKEN,
        workers=100,
        workdir="."
    )

    register_start_handlers(app)
    register_menu_handlers(app)
    register_verify_handlers(app)
    register_redeem_handlers(app)
    register_owner_handlers(app)

    register_admin_navy_handlers(app)
    register_split_handlers(app)
    register_gabung_handlers(app)
    register_msg_to_txt_handlers(app)
    register_txt_to_vcf_handlers(app)
    register_vcf_to_txt_handlers(app)
    register_xlsx_to_vcf_handlers(app)
    register_rapikan_handlers(app)
    register_hitung_handlers(app)
    register_cek_nama_handlers(app)

    @app.on_message(filters.private & filters.text & ~filters.command(["start"]))
    async def handle_text_input(client: Client, message: Message):
        from utils.session_manager import SessionManager
        
        start_time = time.time()
        user_id = message.from_user.id
        text = message.text

        session = await SessionManager.get(user_id)
        if not session:
            return

        mode = session.get("mode", "")

        try:
            if mode == "admin_navy":
                await handle_admin_navy_input(client, message)
            elif mode == "split_file":
                await handle_split_file(client, message)
            elif mode == "gabung_file":
                await handle_gabung_file(client, message)
            elif mode == "msg_to_txt":
                await handle_msg_to_txt(client, message)
            elif mode == "txt_to_vcf":
                await handle_txt_to_vcf(client, message)
            elif mode == "vcf_to_txt":
                await handle_vcf_to_txt(client, message)
            elif mode == "xlsx_to_vcf":
                await handle_xlsx_to_vcf(client, message)
            elif mode == "rapikan_txt":
                await handle_rapikan_txt(client, message)
            elif mode == "hitung_kontak":
                await handle_hitung_kontak(client, message)
            elif mode == "cek_nama":
                await handle_cek_nama(client, message)
            elif mode == "redeem":
                from handlers.redeem import redeem_process
                await redeem_process(client, message)
            elif mode in ["add_vip", "add_vvip", "create_redeem", "ban_user", "unban_user", 
                          "add_bot", "start_bot", "stop_bot", "delete_bot", "bot_stats",
                          "check_bot_token", "check_bot_username"]:
                await handle_owner_input(client, message)
            
            response_time = (time.time() - start_time) * 1000
            monitor.record_response_time(mode or "text", response_time)
            
        except Exception as e:
            monitor.record_error("handler_error", str(e))
            logger.error(f"Error handling text input: {e}")

    @app.on_message(filters.private & filters.document)
    async def handle_document_input(client: Client, message: Message):
        from utils.session_manager import SessionManager
        
        start_time = time.time()
        user_id = message.from_user.id

        session = await SessionManager.get(user_id)
        if not session:
            return

        mode = session.get("mode", "")

        try:
            if mode == "split_file":
                await handle_split_file(client, message)
            elif mode == "gabung_file":
                await handle_gabung_file(client, message)
            elif mode == "txt_to_vcf":
                await handle_txt_to_vcf(client, message)
            elif mode == "vcf_to_txt":
                await handle_vcf_to_txt(client, message)
            elif mode == "xlsx_to_vcf":
                await handle_xlsx_to_vcf(client, message)
            elif mode == "rapikan_txt":
                await handle_rapikan_txt(client, message)
            elif mode == "hitung_kontak":
                await handle_hitung_kontak(client, message)
            elif mode == "cek_nama":
                await handle_cek_nama(client, message)
            
            response_time = (time.time() - start_time) * 1000
            monitor.record_response_time(f"doc_{mode}", response_time)
            
        except Exception as e:
            monitor.record_error("document_error", str(e))
            logger.error(f"Error handling document input: {e}")

    logger.info("Starting bot...")
    print("🚀 Bot starting...")

    async with app:
        background_tasks = BackgroundTasks(app)
        await background_tasks.start()

        metrics_collector = MetricsCollector(monitor)
        await metrics_collector.start()

        alert_manager = AlertManager(monitor, app)
        alert_manager.set_owner(OWNER_ID)
        await alert_manager.start()
        
        await limit_manager.start_auto_reset_task()
        logger.info("Limit manager auto-reset task started")

        bot_info = await app.get_me()
        print("✅ Bot is running!")
        print(f"📱 Bot: @{bot_info.username}")
        print(f"🆔 Bot ID: {bot_info.id}")
        logger.info(f"Bot is running! @{bot_info.username}")

        await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
