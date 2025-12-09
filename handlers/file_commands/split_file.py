import os
import re
import vobject
from pyrogram import Client, filters
from pyrogram.types import Message

from config import is_owner
from core.database import db
from core.limit_manager import limit_manager
from core.error_handler import handle_errors
from utils.keyboards import get_cancel_keyboard, get_menu_keyboard, get_split_mode_keyboard, get_limit_upgrade_inline
from utils.messages import Messages
from utils.file_utils import FileUtils
from utils.session_manager import SessionManager


def rename_contacts_split(contacts, start_index, contact_prefix):
    renamed_contacts = []
    for index, contact in enumerate(contacts, start=start_index):
        if hasattr(contact, 'fn'):
            clean_name = re.sub(r'\d+', '', contact.fn.value).strip()
            clean_name = FileUtils.remove_emojis(clean_name)
            contact.fn.value = f'{clean_name} {str(index).zfill(2)}'
        renamed_contacts.append(contact)
    return renamed_contacts


@handle_errors
async def split_file_start(client: Client, message: Message):
    user_id = message.from_user.id

    can_proceed, status = await limit_manager.check_limit(user_id)
    
    if not can_proceed:
        await message.reply_text(
            status["message"],
            reply_markup=get_limit_upgrade_inline()
        )
        return

    await SessionManager.save(user_id, "split_file", step=1)

    await message.reply_text(
        Messages.split_file_start(),
        reply_markup=get_cancel_keyboard()
    )


@handle_errors
async def handle_split_file(client: Client, message: Message):
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
    if not session or session.get("mode") != "split_file":
        return

    step = session.get("step", 0)
    data = session.get("data") or {}

    if step == 1:
        if not message.document:
            await message.reply_text("```\n❌ Kirim file .txt atau .vcf!\n```")
            return

        filename = message.document.file_name

        if not (filename.endswith('.txt') or filename.endswith('.vcf')):
            await message.reply_text("```\n❌ File harus .txt atau .vcf!\n```")
            return

        filepath = FileUtils.get_temp_path(user_id, filename)
        await message.download(file_name=filepath)

        file_type = 'txt' if filename.endswith('.txt') else 'vcf'
        data["split_file"] = filepath
        data["split_type"] = file_type

        await SessionManager.save(user_id, "split_file", 2, data)
        await message.reply_text(
            Messages.split_ask_output_name(),
            reply_markup=get_cancel_keyboard()
        )

    elif step == 2:
        data["output_name"] = message.text.strip()
        await SessionManager.save(user_id, "split_file", 3, data)
        await message.reply_text(
            Messages.split_ask_file_prefix(),
            reply_markup=get_cancel_keyboard()
        )

    elif step == 3:
        try:
            file_prefix = int(message.text.strip())
            data["file_prefix"] = file_prefix
            await SessionManager.save(user_id, "split_file", 4, data)
            await message.reply_text(
                Messages.split_ask_contact_prefix(),
                reply_markup=get_cancel_keyboard()
            )
        except ValueError:
            await message.reply_text("```\n❌ Masukkan angka yang valid!\n```")

    elif step == 4:
        try:
            contact_prefix = int(message.text.strip())
            data["contact_prefix"] = contact_prefix
            await SessionManager.save(user_id, "split_file", 5, data)
            await message.reply_text(
                Messages.split_mode_select(),
                reply_markup=get_split_mode_keyboard()
            )
        except ValueError:
            await message.reply_text("```\n❌ Masukkan angka yang valid!\n```")

    elif step == 5:
        mode = message.text

        if mode not in ["🜲 PER KONTAK 🜲", "🜲 PER BAGIAN 🜲"]:
            await message.reply_text("```\n❌ Pilih mode yang valid!\n```")
            return

        split_mode = "PER KONTAK" if "KONTAK" in mode else "PER BAGIAN"
        data["split_mode"] = split_mode
        await SessionManager.save(user_id, "split_file", 6, data)

        if split_mode == "PER KONTAK":
            prompt = "```\n🔢 JUMLAH KONTAK PER FILE\n───────────────────────────────────────\n\nMasukkan jumlah kontak per file\n\nContoh: 50\n(Setiap file akan berisi 50 kontak)\n\n───────────────────────────────────────\n```"
        else:
            prompt = "```\n🔢 JUMLAH BAGIAN\n───────────────────────────────────────\n\nMasukkan berapa bagian file akan dibagi\n\nContoh: 5\n(File akan dibagi menjadi 5 file)\n\n───────────────────────────────────────\n```"

        await message.reply_text(prompt, reply_markup=get_cancel_keyboard())

    elif step == 6:
        try:
            split_value = int(message.text.strip())
        except ValueError:
            await message.reply_text("```\n❌ Masukkan angka yang valid!\n```")
            return

        filepath = data.get("split_file")
        file_type = data.get("split_type")
        output_name = data.get("output_name")
        file_prefix = data.get("file_prefix")
        contact_prefix = data.get("contact_prefix")
        split_mode = data.get("split_mode")

        keyboard = get_menu_keyboard(user_id)
        output_files = []

        try:
            if file_type == 'vcf':
                with open(filepath, 'r', encoding='utf-8') as f:
                    vcf_content = f.read()
                contacts = list(vobject.readComponents(vcf_content))
                total_contacts = len(contacts)

                if split_mode == "PER KONTAK":
                    contacts_per_file = split_value
                    num_files = (total_contacts + contacts_per_file - 1) // contacts_per_file
                else:
                    num_files = split_value
                    contacts_per_file = (total_contacts + num_files - 1) // num_files

                global_contact_index = contact_prefix

                for i in range(num_files):
                    start_idx = i * contacts_per_file
                    end_idx = min(start_idx + contacts_per_file, total_contacts)
                    chunk = contacts[start_idx:end_idx]

                    if not chunk:
                        continue

                    renamed_chunk = rename_contacts_split(chunk, global_contact_index, contact_prefix)

                    output_file = FileUtils.get_temp_path(user_id, f"{output_name} {file_prefix + i}.vcf")
                    with open(output_file, 'w', encoding='utf-8') as f:
                        for contact in renamed_chunk:
                            f.write(contact.serialize())

                    output_files.append(output_file)
                    global_contact_index += len(chunk)

            else:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                numbers = re.findall(r'\d+', content)
                total_numbers = len(numbers)

                if split_mode == "PER KONTAK":
                    numbers_per_file = split_value
                    num_files = (total_numbers + numbers_per_file - 1) // numbers_per_file
                else:
                    num_files = split_value
                    numbers_per_file = (total_numbers + num_files - 1) // num_files

                for i in range(num_files):
                    start_idx = i * numbers_per_file
                    end_idx = min(start_idx + numbers_per_file, total_numbers)
                    chunk = numbers[start_idx:end_idx]

                    if not chunk:
                        continue

                    output_file = FileUtils.get_temp_path(user_id, f"{output_name} {file_prefix + i}.txt")
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write('\n'.join(chunk))

                    output_files.append(output_file)

            for i, output_file in enumerate(output_files):
                is_last = (i == len(output_files) - 1)
                await message.reply_document(
                    document=output_file,
                    file_name=os.path.basename(output_file).replace(f"temp_{user_id}_", ""),
                    reply_markup=keyboard if is_last else None
                )

            await message.reply_text(
                f"✅ Berhasil split!\n📂 Total: {len(output_files)} file\n📁 Nama: {output_name}",
                reply_markup=keyboard
            )

            success, status = await limit_manager.use_operation(user_id, "split_file")
            
            if status.get("message") and status.get("warning_level") in ["low", "moderate"]:
                await message.reply_text(status["message"], reply_markup=keyboard)

        except Exception as e:
            await message.reply_text(f"```\n❌ Error: {str(e)}\n```", reply_markup=keyboard)
        finally:
            FileUtils.safe_remove(filepath)
            for output_file in output_files:
                FileUtils.safe_remove(output_file)
            await SessionManager.clear(user_id)


def register_split_handlers(app: Client):
    app.on_message(filters.regex("^🜲 SPLIT FILE 🜲$") & filters.private)(split_file_start)
