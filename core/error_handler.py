import logging
import traceback
from functools import wraps
from pyrogram import Client
from pyrogram.types import Message

logger = logging.getLogger("bot")


def handle_errors(func):
    @wraps(func)
    async def wrapper(client: Client, message: Message, *args, **kwargs):
        try:
            return await func(client, message, *args, **kwargs)
        except Exception as e:
            error_msg = f"Error in {func.__name__}: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            
            try:
                await message.reply_text(
                    "```\n❌ Terjadi kesalahan. Silakan coba lagi.\n```",
                    parse_mode="markdown"
                )
            except:
                pass
    return wrapper


class ErrorHandler:
    @staticmethod
    async def log_error(user_id: int, action: str, error: Exception):
        from core.database import db
        await db.log_action(user_id, "error", {
            "action": action,
            "error": str(error),
            "traceback": traceback.format_exc()
        })
