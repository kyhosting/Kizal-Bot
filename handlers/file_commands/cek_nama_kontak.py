from pyrogram import Client, filters
from pyrogram.types import Message

from config import is_owner
from core.database import db
from core.limit_manager import limit_manager
from core.error_handler import handle_errors
from utils.keyboards import get_cancel_keyboard, get_menu_keyboard, get_limit_upgrade_inline
from utils.messages import Messages
from utils.file_utils import FileUtils
from utils.vcf_utils import VCFUtils
from utils.session_manager import SessionManager


@handle_errors
async def cek_nama_start(client: Client, message: Message):
    user_id = message.from_user.id

    can_proceed, status = await limit_manager.check_limit(user_id)
    
    if not can_proceed:
        await message.reply_text(
            status["message"],
            reply_markup=get_limit_upgrade_inline()
        )
        return

    await SessionManager.save(user_id, "cek_nama", step=1)

    await message.reply_text(
        Messages.cek_nama_start(),
        reply_markup=get_cancel_keyboard()
    )


@handle_errors
async def handle_cek_nama(client: Client, message: Message):
    user_id = message.from_user.id

    if message.text == "❌ BATAL ❌":
        await SessionManager.clear(user_id)
        FileUtils.cleanup_user_files(user_id)
        await message.reply_text(
            Messages.cancelled(),
            reply_markup=get_menu_keyboard(user_id)
        )
        return

    session = await SessionManager.get(user_id)
    if not session or session.get("mode") != "cek_nama":
        return

    if not message.document:
        await message.reply_text("```\n❌ Kirim file .vcf!\n```")
        return

    if not message.document.file_name.endswith('.vcf'):
        await message.reply_text("```\n❌ File harus berformat .vcf!\n```")
        return

    filepath = FileUtils.get_temp_path(user_id, message.document.file_name)
    await message.download(file_name=filepath)

    keyboard = get_menu_keyboard(user_id)

    try:
        contacts = VCFUtils.extract_contacts(filepath)

        if not contacts:
            await message.reply_text("```\n❌ Tidak ada kontak ditemukan!\n```", reply_markup=keyboard)
            await SessionManager.clear(user_id)
            FileUtils.safe_remove(filepath)
            return

        result_text = f"```\n🔍 CEK NAMA KONTAK\n───────────────────────────────────────\n📁 File: {message.document.file_name}\n📊 Total: {len(contacts)} kontak\n───────────────────────────────────────\n\n"

        display_contacts = contacts[:50]
        for i, (name, phone) in enumerate(display_contacts, 1):
            name_display = name[:20] if name else "(Tanpa Nama)"
            result_text += f"{i}. {name_display}\n   📞 {phone}\n"

        if len(contacts) > 50:
            result_text += f"\n... dan {len(contacts) - 50} kontak lainnya\n"

        result_text += "───────────────────────────────────────\n```"

        if len(result_text) > 4000:
            result_text = result_text[:3900] + "\n... (terpotong)\n```"

        await message.reply_text(result_text, reply_markup=keyboard)

        success, status = await limit_manager.use_operation(user_id, "cek_nama")
        
        if status.get("message") and status.get("warning_level") in ["low", "moderate"]:
            await message.reply_text(status["message"], reply_markup=keyboard)

    except Exception as e:
        await message.reply_text(f"```\n❌ Error: {str(e)}\n```", reply_markup=keyboard)
    finally:
        FileUtils.safe_remove(filepath)
        await SessionManager.clear(user_id)


def register_cek_nama_handlers(app: Client):
    app.on_message(filters.regex("^🜲 CEK NAMA 🜲$") & filters.private)(cek_nama_start)
