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
from utils.session_manager import SessionManager


def clean_text_file(content: str) -> tuple:
    lines = content.split('\n')
    
    cleaned_lines = []
    seen = set()
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        clean_line = re.sub(r'[\s\-\(\)\.]', '', line)
        
        if clean_line.isdigit() and len(clean_line) >= 8:
            if clean_line not in seen:
                seen.add(clean_line)
                cleaned_lines.append(clean_line)
    
    return cleaned_lines, len(lines), len(cleaned_lines)


@handle_errors
async def rapikan_txt_start(client: Client, message: Message):
    user_id = message.from_user.id

    can_proceed, status = await limit_manager.check_limit(user_id)
    
    if not can_proceed:
        await message.reply_text(
            status["message"],
            reply_markup=get_limit_upgrade_inline()
        )
        return

    await SessionManager.save(user_id, "rapikan_txt", step=1)

    await message.reply_text(
        Messages.rapikan_txt_start(),
        reply_markup=get_cancel_keyboard()
    )


@handle_errors
async def handle_rapikan_txt(client: Client, message: Message):
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
    if not session or session.get("mode") != "rapikan_txt":
        return

    if not message.document:
        await message.reply_text("```\n❌ Kirim file .txt!\n```")
        return

    if not message.document.file_name.endswith('.txt'):
        await message.reply_text("```\n❌ File harus berformat .txt!\n```")
        return

    filepath = FileUtils.get_temp_path(user_id, message.document.file_name)
    await message.download(file_name=filepath)

    output_filepath = FileUtils.get_temp_path(user_id, f"rapikan_{message.document.file_name}")
    keyboard = get_menu_keyboard(user_id)

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        cleaned_lines, original_count, cleaned_count = clean_text_file(content)

        with open(output_filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(cleaned_lines))

        removed = original_count - cleaned_count

        await message.reply_document(
            document=output_filepath,
            file_name=f"rapikan_{message.document.file_name}",
            caption=f"✅ Berhasil rapikan TXT!\n📊 Sebelum: {original_count} baris\n📊 Sesudah: {cleaned_count} nomor\n🗑️ Dihapus: {removed} (duplikat/invalid)"
        )

        success, status = await limit_manager.use_operation(user_id, "rapikan_txt")
        
        if status.get("message") and status.get("warning_level") in ["low", "moderate"]:
            await message.reply_text(status["message"], reply_markup=keyboard)

    except Exception as e:
        await message.reply_text(f"```\n❌ Error: {str(e)}\n```", reply_markup=keyboard)
    finally:
        FileUtils.safe_remove(filepath)
        FileUtils.safe_remove(output_filepath)
        await SessionManager.clear(user_id)


def register_rapikan_handlers(app: Client):
    app.on_message(filters.regex("^🜲 RAPIKAN TXT 🜲$") & filters.private)(rapikan_txt_start)
