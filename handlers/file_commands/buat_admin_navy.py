import os
from pyrogram import Client, filters
from pyrogram.types import Message

from config import is_owner
from core.database import db
from core.limit_manager import limit_manager
from core.error_handler import handle_errors
from utils.keyboards import get_cancel_keyboard, get_menu_keyboard, get_mode_keyboard, get_limit_upgrade_inline
from utils.messages import Messages
from utils.file_utils import FileUtils
from utils.vcf_utils import VCFUtils
from utils.session_manager import SessionManager


@handle_errors
async def create_admin_navy_start(client: Client, message: Message):
    user_id = message.from_user.id

    can_proceed, status = await limit_manager.check_limit(user_id)
    
    if not can_proceed:
        await message.reply_text(
            status["message"],
            reply_markup=get_limit_upgrade_inline()
        )
        return

    await SessionManager.save(user_id, "admin_navy", step=1)

    await message.reply_text(
        Messages.create_admin_mode_select(),
        reply_markup=get_mode_keyboard()
    )


@handle_errors
async def handle_admin_navy_input(client: Client, message: Message):
    user_id = message.from_user.id
    text = message.text

    if text == "❌ BATAL ❌":
        await SessionManager.clear(user_id)
        FileUtils.cleanup_user_files(user_id)
        await message.reply_text(
            Messages.cancelled(),
            reply_markup=get_menu_keyboard(user_id)
        )
        return

    session = await SessionManager.get(user_id)
    if not session or session.get("mode") != "admin_navy":
        return

    step = session.get("step", 0)
    data = session.get("data") or {}

    if step == 1:
        if text == "🜲 MODE A - GUIDED 🜲":
            data["admin_mode"] = "A"
            await SessionManager.save(user_id, "admin_navy", 2, data)
            await message.reply_text(
                Messages.ask_admin_number(),
                reply_markup=get_cancel_keyboard()
            )
        elif text == "🜲 MODE B - AUTO PARSE 🜲":
            data["admin_mode"] = "B"
            await SessionManager.save(user_id, "admin_navy", 6, data)
            await message.reply_text(
                "```\n📋 INPUT BLOCK\n───────────────────────────────────────\n\nMODE B - AUTO PARSE\n\nKirim block teks dengan format:\nADMIN\n+628123456789\nNAVY\n+628987654321\n\nBot akan parse otomatis!\n\n───────────────────────────────────────\n```",
                reply_markup=get_cancel_keyboard()
            )
        elif text == "🜲 MODE C - MINIMAL 🜲":
            data["admin_mode"] = "C"
            await SessionManager.save(user_id, "admin_navy", 2, data)
            await message.reply_text(
                "```\n📞 NOMOR TELEPON\n───────────────────────────────────────\n\nMODE C - MINIMAL\n\nKirim 1 nomor telepon\n(format +62... atau 0...)\n\n───────────────────────────────────────\n```",
                reply_markup=get_cancel_keyboard()
            )
        else:
            await message.reply_text("```\n❌ Pilih mode yang valid!\n```")

    elif step == 2:
        admin_numbers = text.strip().split('\n')
        admin_numbers = [num.strip() for num in admin_numbers if num.strip()]
        data["admin_numbers"] = admin_numbers

        mode = data.get("admin_mode")

        if mode == "C":
            data["navy_numbers"] = []
            await SessionManager.save(user_id, "admin_navy", 4, data)
            await message.reply_text(
                Messages.ask_filename(),
                reply_markup=get_cancel_keyboard()
            )
        else:
            await SessionManager.save(user_id, "admin_navy", 3, data)
            await message.reply_text(
                Messages.ask_navy_number(),
                reply_markup=get_cancel_keyboard()
            )

    elif step == 3:
        navy_numbers = text.strip().split('\n')
        navy_numbers = [num.strip() for num in navy_numbers if num.strip()]
        data["navy_numbers"] = navy_numbers

        await SessionManager.save(user_id, "admin_navy", 4, data)
        await message.reply_text(
            Messages.ask_filename(),
            reply_markup=get_cancel_keyboard()
        )

    elif step == 4:
        data["vcf_filename"] = text.strip()

        await SessionManager.save(user_id, "admin_navy", 5, data)
        await message.reply_text(
            Messages.ask_contact_format(),
            reply_markup=get_cancel_keyboard()
        )

    elif step == 5:
        contact_format = text.strip()
        admin_numbers = data.get("admin_numbers", [])
        navy_numbers = data.get("navy_numbers", [])
        vcf_filename = data.get("vcf_filename", "output")

        vcf_filepath = FileUtils.get_temp_path(user_id, f"{vcf_filename}.vcf")
        keyboard = get_menu_keyboard(user_id)

        try:
            with open(vcf_filepath, 'w', encoding='utf-8') as f:
                index = 1
                for phone in admin_numbers:
                    vcf_entry = VCFUtils.create_vcf_entry(phone, f"{contact_format} {str(index).zfill(2)}")
                    f.write(vcf_entry)
                    index += 1

                for phone in navy_numbers:
                    vcf_entry = VCFUtils.create_vcf_entry(phone, f"navy {str(index).zfill(2)}")
                    f.write(vcf_entry)
                    index += 1

            total_contacts = len(admin_numbers) + len(navy_numbers)

            await message.reply_document(
                document=vcf_filepath,
                file_name=f"{vcf_filename}.vcf",
                caption=f"✅ Berhasil create ADMIN & NAVY!\n📂 Total: {total_contacts} kontak\n   Admin: {len(admin_numbers)} | Navy: {len(navy_numbers)}"
            )

            success, status = await limit_manager.use_operation(user_id, "admin_navy")
            
            if status.get("message") and status.get("warning_level") in ["low", "moderate"]:
                await message.reply_text(status["message"], reply_markup=keyboard)

        except Exception as e:
            await message.reply_text(f"```\n❌ Error: {str(e)}\n```", reply_markup=keyboard)
        finally:
            FileUtils.safe_remove(vcf_filepath)
            await SessionManager.clear(user_id)

    elif step == 6:
        block_text = text.strip()
        lines = block_text.split('\n')

        admin_numbers = []
        navy_numbers = []
        current_category = None

        for line in lines:
            line = line.strip()
            if line.upper() == 'ADMIN':
                current_category = 'ADMIN'
            elif line.upper() == 'NAVY':
                current_category = 'NAVY'
            elif line and (line.startswith('+') or line.startswith('0') or line.isdigit()):
                if current_category == 'ADMIN':
                    admin_numbers.append(line)
                elif current_category == 'NAVY':
                    navy_numbers.append(line)

        if not admin_numbers and not navy_numbers:
            await message.reply_text("```\n❌ Tidak ada nomor valid ditemukan!\n```")
            return

        data["admin_numbers"] = admin_numbers
        data["navy_numbers"] = navy_numbers

        await SessionManager.save(user_id, "admin_navy", 4, data)
        await message.reply_text(
            f"```\n📝 NAMA FILE\n───────────────────────────────────────\n\nTotal parsed:\nAdmin: {len(admin_numbers)}\nNavy: {len(navy_numbers)}\n\nMasukkan nama file output\n(tanpa ekstensi .vcf)\n\n───────────────────────────────────────\n```",
            reply_markup=get_cancel_keyboard()
        )


def register_admin_navy_handlers(app: Client):
    app.on_message(filters.regex("^🜲 CREATE ADM/NAVY 🜲$") & filters.private)(create_admin_navy_start)
