from pyrogram import Client, filters
from pyrogram.types import Message

from config import is_owner
from core.database import db
from core.limit_manager import limit_manager
from core.error_handler import handle_errors
from utils.keyboards import get_cancel_keyboard, get_menu_keyboard, get_limit_upgrade_inline
from utils.messages import Messages
from utils.file_utils import FileUtils
from utils.session_manager import SessionManager


@handle_errors
async def msg_to_txt_start(client: Client, message: Message):
    user_id = message.from_user.id

    can_proceed, status = await limit_manager.check_limit(user_id)
    
    if not can_proceed:
        await message.reply_text(
            status["message"],
            reply_markup=get_limit_upgrade_inline()
        )
        return

    await SessionManager.save(user_id, "msg_to_txt", step=1)

    await message.reply_text(
        Messages.msg_to_txt_start(),
        reply_markup=get_cancel_keyboard()
    )


@handle_errors
async def handle_msg_to_txt(client: Client, message: Message):
    user_id = message.from_user.id
    text = message.text

    if text == "❌ BATAL ❌":
        await SessionManager.clear(user_id)
        await message.reply_text(
            Messages.cancelled(),
            reply_markup=get_menu_keyboard(user_id)
        )
        return

    session = await SessionManager.get(user_id)
    if not session or session.get("mode") != "msg_to_txt":
        return

    step = session.get("step", 0)
    data = session.get("data") or {}

    if step == 1:
        data["message_content"] = text
        await SessionManager.save(user_id, "msg_to_txt", 2, data)
        await message.reply_text(
            "```\n📝 NAMA FILE\n───────────────────────────────────────\n\nMasukkan nama file output\n(tanpa ekstensi .txt)\n\n───────────────────────────────────────\n```",
            reply_markup=get_cancel_keyboard()
        )

    elif step == 2:
        filename = text.strip()
        content = data.get("message_content", "")

        filepath = FileUtils.get_temp_path(user_id, f"{filename}.txt")
        keyboard = get_menu_keyboard(user_id)

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)

            await message.reply_document(
                document=filepath,
                file_name=f"{filename}.txt",
                caption=f"✅ Berhasil convert MSG to TXT!\n📂 Total: {len(content)} karakter",
                reply_markup=keyboard
            )

            success, status = await limit_manager.use_operation(user_id, "msg_to_txt")
            
            if status.get("message") and status.get("warning_level") in ["low", "moderate"]:
                await message.reply_text(status["message"], reply_markup=keyboard)

        except Exception as e:
            await message.reply_text(f"```\n❌ Error: {str(e)}\n```", reply_markup=keyboard)
        finally:
            FileUtils.safe_remove(filepath)
            await SessionManager.clear(user_id)


def register_msg_to_txt_handlers(app: Client):
    app.on_message(filters.regex("^🜲 MSG TO TXT 🜲$") & filters.private)(msg_to_txt_start)
