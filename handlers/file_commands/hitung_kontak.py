import re
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
async def hitung_kontak_start(client: Client, message: Message):
    user_id = message.from_user.id

    can_proceed, status = await limit_manager.check_limit(user_id)
    
    if not can_proceed:
        await message.reply_text(
            status["message"],
            reply_markup=get_limit_upgrade_inline()
        )
        return

    await SessionManager.save(user_id, "hitung_kontak", step=1)

    await message.reply_text(
        Messages.hitung_kontak_start(),
        reply_markup=get_cancel_keyboard()
    )


@handle_errors
async def handle_hitung_kontak(client: Client, message: Message):
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
    if not session or session.get("mode") != "hitung_kontak":
        return

    if not message.document:
        await message.reply_text("```\n❌ Kirim file .txt atau .vcf!\n```")
        return

    filename = message.document.file_name
    if not (filename.endswith('.txt') or filename.endswith('.vcf')):
        await message.reply_text("```\n❌ File harus .txt atau .vcf!\n```")
        return

    filepath = FileUtils.get_temp_path(user_id, filename)
    await message.download(file_name=filepath)

    keyboard = get_menu_keyboard(user_id)

    try:
        if filename.endswith('.vcf'):
            numbers = VCFUtils.extract_phone_numbers(filepath)
            total_count = len(numbers)
            file_type = "VCF"
        else:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            numbers = re.findall(r'\d+', content)
            numbers = [n for n in numbers if len(n) >= 8]
            total_count = len(numbers)
            file_type = "TXT"

        result_text = f"""```
🔢 HASIL HITUNG KONTAK
───────────────────────────────────────
📁 File      : {filename}
📂 Tipe      : {file_type}
📊 Total     : {total_count} kontak
───────────────────────────────────────
```"""

        await message.reply_text(result_text, reply_markup=keyboard)

        success, status = await limit_manager.use_operation(user_id, "hitung_kontak")
        
        if status.get("message") and status.get("warning_level") in ["low", "moderate"]:
            await message.reply_text(status["message"], reply_markup=keyboard)

    except Exception as e:
        await message.reply_text(f"```\n❌ Error: {str(e)}\n```", reply_markup=keyboard)
    finally:
        FileUtils.safe_remove(filepath)
        await SessionManager.clear(user_id)


def register_hitung_handlers(app: Client):
    app.on_message(filters.regex("^🜲 HITUNG KONTAK 🜲$") & filters.private)(hitung_kontak_start)
