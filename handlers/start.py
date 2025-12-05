from pyrogram import Client, filters
from pyrogram.types import Message
from datetime import datetime

from config import is_owner, BOT_CREATOR
from core.database import db
from core.error_handler import handle_errors
from utils.keyboards import get_main_keyboard, get_verification_keyboard
from utils.messages import Messages


def format_remaining_time(expired_at) -> str:
    if expired_at is None:
        return "—"

    if isinstance(expired_at, str):
        try:
            expired_at = datetime.fromisoformat(expired_at)
        except:
            return "—"

    now = datetime.now()
    if expired_at < now:
        return "Expired"

    diff = expired_at - now
    days = diff.days
    hours, remainder = divmod(diff.seconds, 3600)
    minutes, _ = divmod(remainder, 60)

    if days > 0:
        return f"{days} hari {hours} jam"
    elif hours > 0:
        return f"{hours} jam {minutes} menit"
    else:
        return f"{minutes} menit"


def get_user_display_name(user) -> str:
    if user.first_name and user.last_name:
        return f"{user.first_name} {user.last_name}"
    elif user.first_name:
        return user.first_name
    elif user.username:
        return f"@{user.username}"
    return "User"


@handle_errors
async def start_command(client: Client, message: Message):
    user = message.from_user
    if not user:
        return

    user_id = user.id
    username = user.username or ""
    first_name = user.first_name or ""
    last_name = user.last_name or ""

    is_private = message.chat.type == "private"

    display_name = get_user_display_name(user)
    role = "Reguler"
    expired_at = "—"
    limit_remaining = 10
    total_requests = 0
    verification_status = "Belum Terverifikasi"

    if is_owner(user_id):
        role = "OWNER"
        limit_remaining = "∞"
        verification_status = "BYPASS (Owner)"
    else:
        db_user = await db.create_or_update_user(
            user_id=user_id,
            username=username,
            first_name=first_name,
            last_name=last_name
        )

        if db_user:
            user_role = db_user.get("role", "reguler")
            total_requests = db_user.get("operation_count", 0)
            daily_limit = db_user.get("daily_limit", 10)
            daily_used = db_user.get("daily_used", 0)
            limit_remaining = max(0, daily_limit - daily_used)

            if user_role == "vvip":
                role = "VVIP"
                if db_user.get("expired_at"):
                    expired_at = format_remaining_time(db_user.get("expired_at"))
            elif user_role == "vip":
                role = "VIP"
                if db_user.get("expired_at"):
                    expired_at = format_remaining_time(db_user.get("expired_at"))

            verification = await db.get_user_verification(user_id)
            if verification:
                if verification.get("status") == "verified":
                    verification_status = "Terverifikasi ✅"
                else:
                    verification_status = "Belum Terverifikasi ❌"

    await db.log_action(user_id, "start", {"first_name": first_name})

    welcome_text = Messages.get_start_message(
        display_name=display_name,
        user_id=user_id,
        role=role,
        verification_status=verification_status,
        expired_at=expired_at,
        limit_remaining=str(limit_remaining),
        total_requests=total_requests
    )

    keyboard = get_main_keyboard(user_id, is_private)

    try:
        photos = await client.get_chat_photos(user_id, limit=1)
        photo_list = [p async for p in photos]
        if photo_list:
            await message.reply_photo(
                photo=photo_list[0].file_id,
                caption=welcome_text,
                reply_markup=keyboard
            )
        else:
            await message.reply_text(
                welcome_text,
                reply_markup=keyboard
            )
    except Exception:
        await message.reply_text(
            welcome_text,
            reply_markup=keyboard
        )


async def back_to_start(client: Client, message: Message):
    await start_command(client, message)


def register_start_handlers(app: Client):
    app.on_message(filters.command("start") & filters.private)(start_command)
    app.on_message(filters.regex("^🔙 KEMBALI 🔙$") & filters.private)(back_to_start)
