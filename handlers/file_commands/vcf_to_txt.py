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
async def vcf_to_txt_start(client: Client, message: Message):
    user_id = message.from_user.id

    can_proceed, status = await limit_manager.check_limit(user_id)
    
    if not can_proceed:
        await message.reply_text(
            status["message"],
            reply_markup=get_limit_upgrade_inline()
        )
        return

    await SessionManager.save(user_id, "vcf_to_txt", step=1)

    await message.reply_text(
        Messages.vcf_to_txt_start(),
        reply_markup=get_cancel_keyboard()
    )


@handle_errors
async def handle_vcf_to_txt(client: Client, message: Message):
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
    if not session or session.get("mode") != "vcf_to_txt":
        return

    if not message.document:
        await message.reply_text("```\n❌ Kirim file .vcf!\n```")
        return

    if not message.document.file_name.endswith('.vcf'):
        await message.reply_text("```\n❌ File harus berformat .vcf!\n```")
        return

    vcf_filepath = FileUtils.get_temp_path(user_id, message.document.file_name)
    await message.download(file_name=vcf_filepath)

    txt_filename = message.document.file_name.replace('.vcf', '.txt')
    txt_filepath = FileUtils.get_temp_path(user_id, txt_filename)

    keyboard = get_menu_keyboard(user_id)

    try:
        numbers = VCFUtils.extract_phone_numbers(vcf_filepath)

        with open(txt_filepath, 'w', encoding='utf-8') as f:
            for num in numbers:
                f.write(num + '\n')

        await message.reply_document(
            document=txt_filepath,
            file_name=txt_filename,
            caption=f"✅ Berhasil extract VCF to TXT!\n📂 Total: {len(numbers)} nomor"
        )

        success, status = await limit_manager.use_operation(user_id, "vcf_to_txt")
        
        if status.get("message") and status.get("warning_level") in ["low", "moderate"]:
            await message.reply_text(status["message"], reply_markup=keyboard)

    except Exception as e:
        await message.reply_text(f"```\n❌ Error: {str(e)}\n```", reply_markup=keyboard)
    finally:
        FileUtils.safe_remove(vcf_filepath)
        FileUtils.safe_remove(txt_filepath)
        await SessionManager.clear(user_id)


def register_vcf_to_txt_handlers(app: Client):
    app.on_message(filters.regex("^🜲 VCF TO TXT 🜲$") & filters.private)(vcf_to_txt_start)
