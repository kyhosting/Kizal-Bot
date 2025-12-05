import os
import re
import vobject
from pyrogram import Client, filters
from pyrogram.types import Message

from config import is_owner
from core.database import db
from core.limit_manager import limit_manager
from core.error_handler import handle_errors
from utils.keyboards import get_cancel_keyboard, get_menu_keyboard, get_merge_keyboard, get_limit_upgrade_inline
from utils.messages import Messages
from utils.file_utils import FileUtils
from utils.session_manager import SessionManager


@handle_errors
async def gabung_file_start(client: Client, message: Message):
    user_id = message.from_user.id

    can_proceed, status = await limit_manager.check_limit(user_id)
    
    if not can_proceed:
        await message.reply_text(
            status["message"],
            reply_markup=get_limit_upgrade_inline()
        )
        return

    await SessionManager.save(user_id, "gabung_file", step=1, data={"merge_files": []})

    await message.reply_text(
        Messages.gabung_file_start(),
        reply_markup=get_merge_keyboard()
    )


@handle_errors
async def handle_gabung_file(client: Client, message: Message):
    user_id = message.from_user.id
    text = message.text if message.text else ""

    session = await SessionManager.get(user_id)
    if not session or session.get("mode") != "gabung_file":
        return

    step = session.get("step", 0)
    data = session.get("data") or {"merge_files": []}

    if text == "❌ BATAL ❌":
        for file_info in data.get("merge_files", []):
            FileUtils.safe_remove(file_info.get("path", ""))
        await SessionManager.clear(user_id)
        await message.reply_text(
            Messages.cancelled(),
            reply_markup=get_menu_keyboard(user_id)
        )
        return

    if step == 1:
        if text == "✅ SELESAI ✅":
            if len(data.get("merge_files", [])) < 2:
                await message.reply_text("```\n❌ Minimal 2 file untuk digabung!\n```")
                return

            await SessionManager.save(user_id, "gabung_file", 2, data)
            await message.reply_text(
                f"```\n📝 NAMA FILE OUTPUT\n───────────────────────────────────────\n\nTotal file: {len(data['merge_files'])}\n\nMasukkan nama file hasil gabungan\n(tanpa ekstensi)\n\n───────────────────────────────────────\n```",
                reply_markup=get_cancel_keyboard()
            )
            return

        if not message.document:
            await message.reply_text("```\n❌ Kirim file .txt atau .vcf!\n```")
            return

        filename = message.document.file_name

        if not (filename.endswith('.txt') or filename.endswith('.vcf')):
            await message.reply_text("```\n❌ File harus .txt atau .vcf!\n```")
            return

        file_type = 'txt' if filename.endswith('.txt') else 'vcf'

        merge_files = data.get("merge_files", [])
        if merge_files:
            first_type = merge_files[0].get("type")
            if file_type != first_type:
                await message.reply_text(f"```\n❌ Semua file harus format .{first_type}!\n```")
                return

        file_index = len(merge_files)
        filepath = FileUtils.get_temp_path(user_id, f"{file_index}_{filename}")
        await message.download(file_name=filepath)

        merge_files.append({
            "path": filepath,
            "type": file_type,
            "name": filename
        })
        data["merge_files"] = merge_files

        await SessionManager.save(user_id, "gabung_file", 1, data)
        await message.reply_text(
            f"```\n✅ File #{len(merge_files)} ditambahkan!\n\nKirim file lagi atau tekan SELESAI\n```"
        )

    elif step == 2:
        output_name = text.strip()
        merge_files = data.get("merge_files", [])
        file_type = merge_files[0].get("type")

        output_filepath = FileUtils.get_temp_path(user_id, f"{output_name}.{file_type}")
        keyboard = get_menu_keyboard(user_id)

        try:
            if file_type == 'txt':
                with open(output_filepath, 'w', encoding='utf-8') as outfile:
                    for file_info in merge_files:
                        with open(file_info["path"], 'r', encoding='utf-8') as infile:
                            outfile.write(infile.read() + '\n')

                with open(output_filepath, 'r') as f:
                    total_numbers = len(re.findall(r'\d+', f.read()))
                total_count = total_numbers
            else:
                all_vcards = []
                for file_info in merge_files:
                    with open(file_info["path"], 'r', encoding='utf-8') as f:
                        vcf_content = f.read()
                    all_vcards.extend(list(vobject.readComponents(vcf_content)))

                with open(output_filepath, 'w', encoding='utf-8') as f:
                    for vcard in all_vcards:
                        f.write(vcard.serialize())

                total_count = len(all_vcards)

            await message.reply_document(
                document=output_filepath,
                file_name=f"{output_name}.{file_type}",
                caption=f"✅ Berhasil gabung {len(merge_files)} file!\n📂 Total: {total_count} kontak"
            )

            success, status = await limit_manager.use_operation(user_id, "gabung_file")
            
            if status.get("message") and status.get("warning_level") in ["low", "moderate"]:
                await message.reply_text(status["message"], reply_markup=keyboard)

        except Exception as e:
            await message.reply_text(f"```\n❌ Error: {str(e)}\n```", reply_markup=keyboard)
        finally:
            for file_info in merge_files:
                FileUtils.safe_remove(file_info.get("path", ""))
            FileUtils.safe_remove(output_filepath)
            await SessionManager.clear(user_id)


def register_gabung_handlers(app: Client):
    app.on_message(filters.regex("^🜲 GABUNG FILE 🜲$") & filters.private)(gabung_file_start)
