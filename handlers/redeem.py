from pyrogram import Client, filters
from pyrogram.types import Message

from core.database import db
from core.error_handler import handle_errors
from utils.keyboards import get_cancel_keyboard, get_menu_keyboard
from utils.messages import Messages
from utils.session_manager import SessionManager


@handle_errors
async def redeem_start(client: Client, message: Message):
    user_id = message.from_user.id

    await SessionManager.save(user_id, "redeem", step=1)

    await message.reply_text(
        Messages.redeem_prompt(),
        reply_markup=get_cancel_keyboard()
    )


@handle_errors
async def redeem_process(client: Client, message: Message):
    user_id = message.from_user.id
    text = message.text

    if text == "❌ BATAL ❌":
        await SessionManager.clear(user_id)
        keyboard = get_menu_keyboard(user_id)
        await message.reply_text(
            Messages.cancelled(),
            reply_markup=keyboard
        )
        return

    session = await SessionManager.get(user_id)
    if not session or session.get("mode") != "redeem":
        return

    code = text.strip().upper()
    keyboard = get_menu_keyboard(user_id)

    result = await db.redeem_code(code, user_id)

    if result.get("success"):
        await db.log_action(user_id, "redeem", {
            "code": code,
            "type": result.get("type"),
            "duration": result.get("duration")
        })

        await message.reply_text(
            Messages.redeem_success(code, result.get("type", "VIP"), result.get("duration", 7)),
            reply_markup=keyboard
        )
    else:
        await message.reply_text(
            Messages.redeem_failed(result.get("message", "Kode tidak valid")),
            reply_markup=keyboard
        )

    await SessionManager.clear(user_id)


def register_redeem_handlers(app: Client):
    app.on_message(filters.regex("^🎁 Redeem Code$") & filters.private)(redeem_start)
