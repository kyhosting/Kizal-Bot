from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery

from config import is_owner, REQUIRED_GROUPS
from core.database import db
from core.error_handler import handle_errors
from utils.keyboards import get_verification_keyboard, get_main_keyboard
from utils.messages import Messages


async def check_user_membership(client: Client, user_id: int) -> tuple:
    joined_group1 = False
    joined_group2 = False

    try:
        if len(REQUIRED_GROUPS) >= 1:
            chat_id = REQUIRED_GROUPS[0].get("chat_id")
            if chat_id:
                try:
                    member = await client.get_chat_member(chat_id, user_id)
                    if member.status in ["member", "administrator", "creator"]:
                        joined_group1 = True
                except Exception:
                    pass

        if len(REQUIRED_GROUPS) >= 2:
            chat_id = REQUIRED_GROUPS[1].get("chat_id")
            if chat_id:
                try:
                    member = await client.get_chat_member(chat_id, user_id)
                    if member.status in ["member", "administrator", "creator"]:
                        joined_group2 = True
                except Exception:
                    pass
    except Exception:
        pass

    return joined_group1, joined_group2


async def verify_user_access(client: Client, message: Message, show_message: bool = True) -> bool:
    user_id = message.from_user.id

    if is_owner(user_id):
        return True

    joined_group1, joined_group2 = await check_user_membership(client, user_id)

    await db.update_verification(user_id, joined_group1, joined_group2)

    if joined_group1 and joined_group2:
        return True

    if show_message:
        user_name = message.from_user.first_name or message.from_user.username or "User"
        await message.reply_text(
            Messages.verification_required(user_name),
            reply_markup=get_verification_keyboard()
        )

    return False


@handle_errors
async def verify_callback(client: Client, callback: CallbackQuery):
    user_id = callback.from_user.id

    if is_owner(user_id):
        await callback.answer("✅ Owner bypass - akses penuh!", show_alert=True)
        return

    joined_group1, joined_group2 = await check_user_membership(client, user_id)

    await db.update_verification(user_id, joined_group1, joined_group2)

    if joined_group1 and joined_group2:
        await callback.answer("✅ Verifikasi berhasil!", show_alert=True)
        keyboard = get_main_keyboard(user_id, True)
        await callback.message.reply_text(
            "✅ Verifikasi berhasil! Sekarang kamu bisa menggunakan bot.",
            reply_markup=keyboard
        )
    else:
        missing = []
        if not joined_group1:
            missing.append("Grup 1")
        if not joined_group2:
            missing.append("Grup 2")

        await callback.answer(
            f"❌ Belum bergabung ke: {', '.join(missing)}",
            show_alert=True
        )


def register_verify_handlers(app: Client):
    app.on_callback_query(filters.regex("^verify_recheck$"))(verify_callback)
