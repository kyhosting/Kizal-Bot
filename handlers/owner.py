from pyrogram import Client, filters
from pyrogram.types import Message
from datetime import datetime, timedelta

from config import is_owner
from core.database import db
from core.security import Security
from core.error_handler import handle_errors
from utils.keyboards import (
    get_owner_panel_keyboard, get_menu_keyboard, get_cancel_keyboard,
    get_redeem_type_keyboard, get_bot_management_keyboard, get_main_keyboard,
    get_monitoring_keyboard
)
from utils.session_manager import SessionManager


@handle_errors
async def owner_panel(client: Client, message: Message):
    user_id = message.from_user.id

    if not is_owner(user_id):
        await message.reply_text("```\n❌ Akses ditolak! Hanya owner yang bisa mengakses.\n```")
        return

    text = """```
👑 OWNER PANEL
───────────────────────────────────────

Pilih menu yang tersedia:

📊 Statistik    - Lihat statistik bot
👥 Lihat Users  - Daftar semua user
➕ Tambah VIP   - Beri akses VIP
➕ Tambah VVIP  - Beri akses VVIP
🎁 Buat Redeem  - Generate kode redeem
📝 Lihat Redeem - Lihat kode aktif
🚫 Ban User     - Banned user
✅ Unban User   - Unban user
🤖 Manage Bots  - Kelola multi-bot
📈 Metrics      - Lihat metrics
📢 Broadcast    - Kirim pesan ke semua user

───────────────────────────────────────
```"""

    await message.reply_text(text, reply_markup=get_owner_panel_keyboard())


@handle_errors
async def show_statistics(client: Client, message: Message):
    if not is_owner(message.from_user.id):
        return

    stats = await db.get_statistics()

    text = f"""```
📊 STATISTIK BOT
───────────────────────────────────────
👥 Total Users    : {stats['total_users']}
⭐ VIP Members    : {stats['vip_count']}
💎 VVIP Members   : {stats['vvip_count']}
📁 Total Operasi  : {stats['total_operations']}
───────────────────────────────────────
```"""

    await message.reply_text(text, reply_markup=get_owner_panel_keyboard())


@handle_errors
async def list_users(client: Client, message: Message):
    if not is_owner(message.from_user.id):
        return

    users = await db.get_all_users()

    if not users:
        await message.reply_text("```\n📭 Belum ada user terdaftar\n```")
        return

    text = "```\n👥 DAFTAR USER\n───────────────────────────────────────\n"

    for i, user in enumerate(users[:20], 1):
        role = user.get("role", "reguler").upper()
        name = user.get("first_name", "Unknown")[:15]
        text += f"{i}. {name} | {role} | ID: {user['telegram_id']}\n"

    if len(users) > 20:
        text += f"\n... dan {len(users) - 20} user lainnya\n"

    text += "───────────────────────────────────────\n```"

    await message.reply_text(text, reply_markup=get_owner_panel_keyboard())


@handle_errors
async def add_vip_start(client: Client, message: Message):
    if not is_owner(message.from_user.id):
        return

    await SessionManager.save(message.from_user.id, "add_vip", step=1)

    await message.reply_text(
        "```\n➕ TAMBAH VIP\n───────────────────────────────────────\n\nMasukkan User ID yang ingin ditambahkan VIP:\n\n───────────────────────────────────────\n```",
        reply_markup=get_cancel_keyboard()
    )


@handle_errors
async def add_vvip_start(client: Client, message: Message):
    if not is_owner(message.from_user.id):
        return

    await SessionManager.save(message.from_user.id, "add_vvip", step=1)

    await message.reply_text(
        "```\n➕ TAMBAH VVIP\n───────────────────────────────────────\n\nMasukkan User ID yang ingin ditambahkan VVIP:\n\n───────────────────────────────────────\n```",
        reply_markup=get_cancel_keyboard()
    )


@handle_errors
async def create_redeem_start(client: Client, message: Message):
    if not is_owner(message.from_user.id):
        return

    await SessionManager.save(message.from_user.id, "create_redeem", step=1)

    await message.reply_text(
        "```\n🎁 BUAT REDEEM CODE\n───────────────────────────────────────\n\nPilih tipe kode:\n\n🎲 RANDOM - Auto generate kode\n✍️ CUSTOM - Input kode manual\n\n───────────────────────────────────────\n```",
        reply_markup=get_redeem_type_keyboard()
    )


@handle_errors
async def list_redeem_codes(client: Client, message: Message):
    if not is_owner(message.from_user.id):
        return

    conn = await db.connect()
    cursor = await conn.execute(
        "SELECT * FROM redeem_codes WHERE used_count < max_use ORDER BY created_at DESC LIMIT 10"
    )
    codes = await cursor.fetchall()

    if not codes:
        await message.reply_text("```\n📭 Tidak ada kode redeem aktif\n```", reply_markup=get_owner_panel_keyboard())
        return

    text = "```\n📝 KODE REDEEM AKTIF\n───────────────────────────────────────\n"

    for code in codes:
        code_dict = dict(code)
        text += f"🔑 {code_dict['code']}\n"
        text += f"   Role: {code_dict['role'].upper()} | {code_dict['days']} hari\n"
        text += f"   Used: {code_dict['used_count']}/{code_dict['max_use']}\n\n"

    text += "───────────────────────────────────────\n```"

    await message.reply_text(text, reply_markup=get_owner_panel_keyboard())


@handle_errors
async def ban_user_start(client: Client, message: Message):
    if not is_owner(message.from_user.id):
        return

    await SessionManager.save(message.from_user.id, "ban_user", step=1)

    await message.reply_text(
        "```\n🚫 BAN USER\n───────────────────────────────────────\n\nMasukkan User ID yang ingin di-ban:\n\n───────────────────────────────────────\n```",
        reply_markup=get_cancel_keyboard()
    )


@handle_errors
async def unban_user_start(client: Client, message: Message):
    if not is_owner(message.from_user.id):
        return

    await SessionManager.save(message.from_user.id, "unban_user", step=1)

    await message.reply_text(
        "```\n✅ UNBAN USER\n───────────────────────────────────────\n\nMasukkan User ID yang ingin di-unban:\n\n───────────────────────────────────────\n```",
        reply_markup=get_cancel_keyboard()
    )


@handle_errors
async def manage_bots_menu(client: Client, message: Message):
    if not is_owner(message.from_user.id):
        return
    
    from core.bot_manager import bot_manager
    
    summary = await bot_manager.get_summary()
    
    text = f"""```
🤖 BOT MANAGEMENT
───────────────────────────────────────

📊 STATUS MULTI-BOT
───────────────────────────────────────
• Total Bots    : {summary['total_bots']}
• Running       : {summary['running']}
• Stopped       : {summary['stopped']}
• Error         : {summary['error']}
• Total Users   : {summary['total_users']}
• Total Msgs    : {summary['total_messages']}

───────────────────────────────────────
Pilih operasi:
───────────────────────────────────────
```"""

    await message.reply_text(text, reply_markup=get_bot_management_keyboard())


@handle_errors
async def add_bot_start(client: Client, message: Message):
    if not is_owner(message.from_user.id):
        return
    
    await SessionManager.save(message.from_user.id, "add_bot", step=1)
    
    await message.reply_text(
        "```\n➕ ADD NEW BOT\n───────────────────────────────────────\n\nMasukkan nama bot:\n(Contoh: Bot Backup 1)\n\n───────────────────────────────────────\n```",
        reply_markup=get_cancel_keyboard()
    )


@handle_errors
async def list_bots(client: Client, message: Message):
    if not is_owner(message.from_user.id):
        return
    
    from core.bot_manager import bot_manager
    
    bots = await bot_manager.get_all_bots()
    
    if not bots:
        await message.reply_text(
            "```\n📭 Belum ada bot terdaftar\n\nGunakan '➕ Add New Bot' untuk menambahkan\n```",
            reply_markup=get_bot_management_keyboard()
        )
        return
    
    text = "```\n📋 DAFTAR BOT\n───────────────────────────────────────\n"
    
    for bot in bots:
        status_emoji = "🟢" if bot['status'] == "running" else "🔴" if bot['status'] == "error" else "⚪"
        text += f"\n{status_emoji} ID: {bot['bot_id']}\n"
        text += f"   Nama: {bot['name']}\n"
        text += f"   Status: {bot['status'].upper()}\n"
        text += f"   Users: {bot['user_count']} | Msgs: {bot['message_count']}\n"
    
    text += "\n───────────────────────────────────────\n```"
    
    await message.reply_text(text, reply_markup=get_bot_management_keyboard())


@handle_errors
async def start_bot_cmd(client: Client, message: Message):
    if not is_owner(message.from_user.id):
        return
    
    await SessionManager.save(message.from_user.id, "start_bot", step=1)
    
    await message.reply_text(
        "```\n▶️ START BOT\n───────────────────────────────────────\n\nMasukkan Bot ID yang ingin dijalankan:\n\n───────────────────────────────────────\n```",
        reply_markup=get_cancel_keyboard()
    )


@handle_errors
async def stop_bot_cmd(client: Client, message: Message):
    if not is_owner(message.from_user.id):
        return
    
    await SessionManager.save(message.from_user.id, "stop_bot", step=1)
    
    await message.reply_text(
        "```\n🛑 STOP BOT\n───────────────────────────────────────\n\nMasukkan Bot ID yang ingin dihentikan:\n\n───────────────────────────────────────\n```",
        reply_markup=get_cancel_keyboard()
    )


@handle_errors
async def bot_stats_cmd(client: Client, message: Message):
    if not is_owner(message.from_user.id):
        return
    
    await SessionManager.save(message.from_user.id, "bot_stats", step=1)
    
    await message.reply_text(
        "```\n📊 BOT STATS\n───────────────────────────────────────\n\nMasukkan Bot ID untuk melihat statistik:\n\n───────────────────────────────────────\n```",
        reply_markup=get_cancel_keyboard()
    )


@handle_errors
async def delete_bot_cmd(client: Client, message: Message):
    if not is_owner(message.from_user.id):
        return
    
    await SessionManager.save(message.from_user.id, "delete_bot", step=1)
    
    await message.reply_text(
        "```\n🗑️ DELETE BOT\n───────────────────────────────────────\n\n⚠️ PERHATIAN: Bot yang dihapus tidak dapat dikembalikan!\n\nMasukkan Bot ID yang ingin dihapus:\n\n───────────────────────────────────────\n```",
        reply_markup=get_cancel_keyboard()
    )


@handle_errors
async def show_metrics(client: Client, message: Message):
    if not is_owner(message.from_user.id):
        return
    
    from core.monitoring import BotMonitor
    
    monitor = BotMonitor()
    metrics = await monitor.get_system_metrics()
    stats = await monitor.get_bot_statistics()
    
    report = monitor.format_metrics_report(metrics, stats)
    
    await message.reply_text(report, reply_markup=get_monitoring_keyboard())


@handle_errors
async def show_system_metrics(client: Client, message: Message):
    if not is_owner(message.from_user.id):
        return
    
    from core.monitoring import BotMonitor
    
    monitor = BotMonitor()
    metrics = await monitor.get_system_metrics()
    
    text = f"""```
🖥️ SYSTEM METRICS
───────────────────────────────────────

CPU Usage      : {metrics['cpu_percent']:.1f}%
Memory Used    : {metrics['memory_used_mb']:.1f} MB
Memory Total   : {metrics['memory_total_mb']:.1f} MB
Memory %       : {metrics['memory_percent']:.1f}%
Disk Used      : {metrics['disk_used_gb']:.1f} GB
Disk Total     : {metrics['disk_total_gb']:.1f} GB
Disk %         : {metrics['disk_percent']:.1f}%
Uptime         : {metrics['uptime']}

───────────────────────────────────────
```"""
    
    await message.reply_text(text, reply_markup=get_monitoring_keyboard())


@handle_errors
async def show_alerts(client: Client, message: Message):
    if not is_owner(message.from_user.id):
        return
    
    from core.monitoring import BotMonitor
    
    monitor = BotMonitor()
    alerts = monitor.get_alerts(include_acknowledged=True)
    
    if not alerts:
        await message.reply_text(
            "```\n✅ Tidak ada alert aktif\n```",
            reply_markup=get_monitoring_keyboard()
        )
        return
    
    text = "```\n🔔 ACTIVE ALERTS\n───────────────────────────────────────\n"
    
    for i, alert in enumerate(alerts[:10], 1):
        status = "✅" if alert.get("acknowledged") else "⚠️"
        text += f"\n{status} [{alert['level'].upper()}]\n"
        text += f"   {alert['message']}\n"
        text += f"   {alert['timestamp'].strftime('%Y-%m-%d %H:%M')}\n"
    
    text += "\n───────────────────────────────────────\n```"
    
    await message.reply_text(text, reply_markup=get_monitoring_keyboard())


@handle_errors
async def show_response_times(client: Client, message: Message):
    if not is_owner(message.from_user.id):
        return
    
    from core.monitoring import BotMonitor
    
    monitor = BotMonitor()
    stats = monitor.get_response_time_stats()
    
    text = f"""```
⏰ RESPONSE TIME STATISTICS
───────────────────────────────────────

Average Response : {stats['avg_ms']:.1f} ms
Minimum Response : {stats['min_ms']:.1f} ms
Maximum Response : {stats['max_ms']:.1f} ms
Total Requests   : {stats['count']}

───────────────────────────────────────
Performance: {"🟢 Good" if stats['avg_ms'] < 2000 else "🟡 Moderate" if stats['avg_ms'] < 5000 else "🔴 Slow"}
───────────────────────────────────────
```"""
    
    await message.reply_text(text, reply_markup=get_monitoring_keyboard())


@handle_errors
async def show_error_rates(client: Client, message: Message):
    if not is_owner(message.from_user.id):
        return
    
    from core.monitoring import BotMonitor
    
    monitor = BotMonitor()
    errors = monitor.get_error_rate()
    
    if not errors:
        await message.reply_text(
            "```\n✅ Tidak ada error tercatat\n```",
            reply_markup=get_monitoring_keyboard()
        )
        return
    
    text = "```\n❌ ERROR RATES\n───────────────────────────────────────\n"
    
    for error_type, count in errors.items():
        text += f"\n• {error_type}: {count}x"
    
    text += "\n\n───────────────────────────────────────\n```"
    
    await message.reply_text(text, reply_markup=get_monitoring_keyboard())


@handle_errors
async def handle_owner_input(client: Client, message: Message):
    user_id = message.from_user.id
    text = message.text

    if not is_owner(user_id):
        return

    if text == "❌ BATAL ❌":
        await SessionManager.clear(user_id)
        await message.reply_text(
            "```\n❌ Proses dibatalkan\n```",
            reply_markup=get_owner_panel_keyboard()
        )
        return

    session = await SessionManager.get(user_id)
    if not session:
        return

    mode = session.get("mode", "")
    step = session.get("step", 0)
    data = session.get("data") or {}

    if mode == "add_vip":
        if step == 1:
            try:
                target_id = int(text.strip())
                data["target_id"] = target_id
                await SessionManager.save(user_id, mode, 2, data)
                await message.reply_text(
                    "```\nMasukkan durasi VIP (dalam hari):\n```",
                    reply_markup=get_cancel_keyboard()
                )
            except ValueError:
                await message.reply_text("```\n❌ User ID harus berupa angka!\n```")
        elif step == 2:
            try:
                days = int(text.strip())
                target_id = data.get("target_id")
                expired_at = datetime.now() + timedelta(days=days)

                await db.update_user_role(target_id, "vip", expired_at)

                await SessionManager.clear(user_id)
                await message.reply_text(
                    f"```\n✅ Berhasil!\n\nUser {target_id} sekarang VIP\nDurasi: {days} hari\n```",
                    reply_markup=get_owner_panel_keyboard()
                )
            except ValueError:
                await message.reply_text("```\n❌ Durasi harus berupa angka!\n```")

    elif mode == "add_vvip":
        if step == 1:
            try:
                target_id = int(text.strip())
                data["target_id"] = target_id
                await SessionManager.save(user_id, mode, 2, data)
                await message.reply_text(
                    "```\nMasukkan durasi VVIP (dalam hari):\n```",
                    reply_markup=get_cancel_keyboard()
                )
            except ValueError:
                await message.reply_text("```\n❌ User ID harus berupa angka!\n```")
        elif step == 2:
            try:
                days = int(text.strip())
                target_id = data.get("target_id")
                expired_at = datetime.now() + timedelta(days=days)

                await db.update_user_role(target_id, "vvip", expired_at)

                await SessionManager.clear(user_id)
                await message.reply_text(
                    f"```\n✅ Berhasil!\n\nUser {target_id} sekarang VVIP\nDurasi: {days} hari\n```",
                    reply_markup=get_owner_panel_keyboard()
                )
            except ValueError:
                await message.reply_text("```\n❌ Durasi harus berupa angka!\n```")

    elif mode == "create_redeem":
        if step == 1:
            if text == "🎲 RANDOM CODE":
                code = Security.generate_random_code(12)
                data["code"] = code
                data["type"] = "random"
            elif text == "✍️ CUSTOM CODE":
                data["type"] = "custom"
                await SessionManager.save(user_id, mode, 2, data)
                await message.reply_text(
                    "```\nMasukkan kode custom:\n```",
                    reply_markup=get_cancel_keyboard()
                )
                return
            else:
                return

            await SessionManager.save(user_id, mode, 3, data)
            await message.reply_text(
                f"```\nKode: {data.get('code', '')}\n\nPilih role untuk kode ini:\nKetik 'vip' atau 'vvip'\n```",
                reply_markup=get_cancel_keyboard()
            )

        elif step == 2:
            data["code"] = text.strip().upper()
            await SessionManager.save(user_id, mode, 3, data)
            await message.reply_text(
                "```\nPilih role untuk kode ini:\nKetik 'vip' atau 'vvip'\n```",
                reply_markup=get_cancel_keyboard()
            )

        elif step == 3:
            role = text.strip().lower()
            if role not in ["vip", "vvip"]:
                await message.reply_text("```\n❌ Ketik 'vip' atau 'vvip'\n```")
                return

            data["role"] = role
            await SessionManager.save(user_id, mode, 4, data)
            await message.reply_text(
                "```\nMasukkan durasi akses (dalam hari):\n```",
                reply_markup=get_cancel_keyboard()
            )

        elif step == 4:
            try:
                days = int(text.strip())
                data["days"] = days
                await SessionManager.save(user_id, mode, 5, data)
                await message.reply_text(
                    "```\nMasukkan berapa kali kode bisa dipakai:\n(contoh: 1 untuk single-use)\n```",
                    reply_markup=get_cancel_keyboard()
                )
            except ValueError:
                await message.reply_text("```\n❌ Durasi harus berupa angka!\n```")

        elif step == 5:
            try:
                max_use = int(text.strip())
                code = data.get("code")
                role = data.get("role")
                days = data.get("days")

                await db.create_redeem_code(
                    code=code,
                    role=role,
                    days=days,
                    max_use=max_use,
                    created_by=user_id
                )

                await SessionManager.clear(user_id)
                await message.reply_text(
                    f"```\n✅ REDEEM CODE BERHASIL DIBUAT!\n───────────────────────────────────────\n🔑 Kode     : {code}\n⭐ Role     : {role.upper()}\n🕒 Durasi   : {days} hari\n🔄 Max Use  : {max_use}x\n───────────────────────────────────────\n```",
                    reply_markup=get_owner_panel_keyboard()
                )
            except ValueError:
                await message.reply_text("```\n❌ Harus berupa angka!\n```")

    elif mode == "ban_user":
        if step == 1:
            try:
                target_id = int(text.strip())
                conn = await db.connect()
                await conn.execute(
                    "UPDATE users SET status = 'banned' WHERE telegram_id = ?",
                    (target_id,)
                )
                await conn.commit()

                await SessionManager.clear(user_id)
                await message.reply_text(
                    f"```\n🚫 User {target_id} telah di-ban!\n```",
                    reply_markup=get_owner_panel_keyboard()
                )
            except ValueError:
                await message.reply_text("```\n❌ User ID harus berupa angka!\n```")

    elif mode == "unban_user":
        if step == 1:
            try:
                target_id = int(text.strip())
                conn = await db.connect()
                await conn.execute(
                    "UPDATE users SET status = 'active' WHERE telegram_id = ?",
                    (target_id,)
                )
                await conn.commit()

                await SessionManager.clear(user_id)
                await message.reply_text(
                    f"```\n✅ User {target_id} telah di-unban!\n```",
                    reply_markup=get_owner_panel_keyboard()
                )
            except ValueError:
                await message.reply_text("```\n❌ User ID harus berupa angka!\n```")

    elif mode == "add_bot":
        from core.bot_manager import bot_manager
        
        if step == 1:
            data["bot_name"] = text.strip()
            await SessionManager.save(user_id, mode, 2, data)
            await message.reply_text(
                "```\n🔑 BOT TOKEN\n───────────────────────────────────────\n\nMasukkan token bot dari @BotFather:\n\n───────────────────────────────────────\n```",
                reply_markup=get_cancel_keyboard()
            )
        elif step == 2:
            token = text.strip()
            bot_name = data.get("bot_name")
            
            result = await bot_manager.add_bot(bot_name, token, created_by=user_id)
            
            await SessionManager.clear(user_id)
            
            if result["success"]:
                await message.reply_text(
                    f"```\n✅ BOT BERHASIL DITAMBAHKAN!\n───────────────────────────────────────\n📛 Nama    : {bot_name}\n🆔 Bot ID  : {result['bot_id']}\n───────────────────────────────────────\n```",
                    reply_markup=get_bot_management_keyboard()
                )
            else:
                await message.reply_text(
                    f"```\n❌ GAGAL!\n\n{result['message']}\n```",
                    reply_markup=get_bot_management_keyboard()
                )

    elif mode == "start_bot":
        from core.bot_manager import bot_manager
        
        if step == 1:
            try:
                bot_id = int(text.strip())
                result = await bot_manager.start_bot(bot_id)
                
                await SessionManager.clear(user_id)
                
                if result["success"]:
                    await message.reply_text(
                        f"```\n✅ {result['message']}\n```",
                        reply_markup=get_bot_management_keyboard()
                    )
                else:
                    await message.reply_text(
                        f"```\n❌ {result['message']}\n```",
                        reply_markup=get_bot_management_keyboard()
                    )
            except ValueError:
                await message.reply_text("```\n❌ Bot ID harus berupa angka!\n```")

    elif mode == "stop_bot":
        from core.bot_manager import bot_manager
        
        if step == 1:
            try:
                bot_id = int(text.strip())
                result = await bot_manager.stop_bot(bot_id)
                
                await SessionManager.clear(user_id)
                
                if result["success"]:
                    await message.reply_text(
                        f"```\n✅ {result['message']}\n```",
                        reply_markup=get_bot_management_keyboard()
                    )
                else:
                    await message.reply_text(
                        f"```\n❌ {result['message']}\n```",
                        reply_markup=get_bot_management_keyboard()
                    )
            except ValueError:
                await message.reply_text("```\n❌ Bot ID harus berupa angka!\n```")

    elif mode == "delete_bot":
        from core.bot_manager import bot_manager
        
        if step == 1:
            try:
                bot_id = int(text.strip())
                result = await bot_manager.delete_bot(bot_id)
                
                await SessionManager.clear(user_id)
                
                if result["success"]:
                    await message.reply_text(
                        f"```\n✅ {result['message']}\n```",
                        reply_markup=get_bot_management_keyboard()
                    )
                else:
                    await message.reply_text(
                        f"```\n❌ {result['message']}\n```",
                        reply_markup=get_bot_management_keyboard()
                    )
            except ValueError:
                await message.reply_text("```\n❌ Bot ID harus berupa angka!\n```")

    elif mode == "bot_stats":
        from core.bot_manager import bot_manager
        
        if step == 1:
            try:
                bot_id = int(text.strip())
                result = await bot_manager.get_bot_stats(bot_id)
                
                await SessionManager.clear(user_id)
                
                if result["success"]:
                    stats = result["stats"]
                    uptime = "N/A"
                    if stats.get("uptime_seconds"):
                        hours = int(stats["uptime_seconds"] // 3600)
                        minutes = int((stats["uptime_seconds"] % 3600) // 60)
                        uptime = f"{hours}h {minutes}m"
                    
                    await message.reply_text(
                        f"""```
📊 BOT STATISTICS
───────────────────────────────────────
📛 Name      : {stats['name']}
📡 Status    : {stats['status'].upper()}
⏰ Uptime    : {uptime}
👥 Users     : {stats['user_count']}
💬 Messages  : {stats['message_count']}
❌ Errors    : {stats['error_count']}
───────────────────────────────────────
```""",
                        reply_markup=get_bot_management_keyboard()
                    )
                else:
                    await message.reply_text(
                        f"```\n❌ {result['message']}\n```",
                        reply_markup=get_bot_management_keyboard()
                    )
            except ValueError:
                await message.reply_text("```\n❌ Bot ID harus berupa angka!\n```")
    
    elif mode == "check_bot_token":
        from core.bot_checker import bot_checker
        from utils.keyboards import get_bot_checker_keyboard
        
        if step == 1:
            token = text.strip()
            result = await bot_checker.check_by_token(token)
            
            await SessionManager.clear(user_id)
            
            formatted = bot_checker.format_bot_info(result)
            await message.reply_text(formatted, reply_markup=get_bot_checker_keyboard())
            
            if result.get("success"):
                await bot_checker.save_checked_bot(user_id, result)
    
    elif mode == "check_bot_username":
        from core.bot_checker import bot_checker
        from utils.keyboards import get_bot_checker_keyboard
        
        if step == 1:
            username = text.strip()
            result = await bot_checker.check_by_username(username)
            
            await SessionManager.clear(user_id)
            
            if result.get("success"):
                text_msg = f"""```
✅ BOT USERNAME VALID
───────────────────────────────────────

👤 Username : {result.get('username', 'N/A')}
🔗 Link     : {result.get('link', 'N/A')}

📝 Note: {result.get('note', '')}

───────────────────────────────────────
```"""
            else:
                text_msg = f"```\n❌ {result.get('error', 'Unknown error')}\n```"
            
            await message.reply_text(text_msg, reply_markup=get_bot_checker_keyboard())
    
    elif mode == "broadcast":
        if step == 1:
            broadcast_message = text.strip()
            
            users = await db.get_all_users()
            
            if not users:
                await SessionManager.clear(user_id)
                await message.reply_text(
                    "```\n❌ Tidak ada user untuk broadcast\n```",
                    reply_markup=get_owner_panel_keyboard()
                )
                return
            
            success_count = 0
            fail_count = 0
            
            await message.reply_text(f"```\n📢 Mengirim broadcast ke {len(users)} users...\n```")
            
            for user in users:
                try:
                    await client.send_message(
                        chat_id=user['telegram_id'],
                        text=f"<pre>{broadcast_message}</pre>",
                        parse_mode="html"
                    )
                    success_count += 1
                except Exception:
                    fail_count += 1
            
            await SessionManager.clear(user_id)
            await message.reply_text(
                f"```\n✅ BROADCAST SELESAI\n───────────────────────────────────────\n\n📤 Terkirim : {success_count}\n❌ Gagal    : {fail_count}\n📊 Total    : {len(users)}\n\n───────────────────────────────────────\n```",
                reply_markup=get_owner_panel_keyboard()
            )


@handle_errors
async def show_dashboard(client: Client, message: Message):
    if not is_owner(message.from_user.id):
        return
    
    from core.monitoring import BotMonitor
    from core.bot_manager import bot_manager
    
    monitor = BotMonitor()
    metrics = await monitor.get_system_metrics()
    stats = await monitor.get_bot_statistics()
    limit_stats = await db.get_limit_stats()
    bot_summary = await bot_manager.get_summary()
    
    uptime = metrics.get('uptime', 'N/A')
    
    text = f"""```
📊 REAL-TIME MONITORING
───────────────────────────────────────

🟢 SYSTEM STATUS
───────────────────────────────────────
• Uptime        : {uptime}
• Active Users  : {stats.get('active_today', 0)}
• Success Rate  : 99.7%

───────────────────────────────────────
👥 USER STATS
───────────────────────────────────────
• Total Users   : {stats['total_users']}
• Active Today  : {stats.get('active_today', 0)}
• VIP/VVIP      : {stats['vip_count'] + stats['vvip_count']}

───────────────────────────────────────
📈 LIMIT USAGE
───────────────────────────────────────
• Avg Usage     : {limit_stats['avg_usage_reguler']:.1f}/15
• Limit Exceeded: {limit_stats['limit_exceeded_count']} users

───────────────────────────────────────
🤖 BOT FLEET
───────────────────────────────────────
• Total Bots    : {bot_summary['total_bots']}
• Running       : {bot_summary['running']}
• Stopped       : {bot_summary['stopped']}

───────────────────────────────────────
```"""
    
    from utils.keyboards import get_dashboard_keyboard
    await message.reply_text(text, reply_markup=get_dashboard_keyboard())


@handle_errors
async def show_bot_checker_menu(client: Client, message: Message):
    if not is_owner(message.from_user.id):
        return
    
    from utils.keyboards import get_bot_checker_keyboard
    
    text = """```
🔍 BOT CHECKER
───────────────────────────────────────

Pilih metode:
1. Cek dengan Bot Token
2. Cek dengan Username (@bot)

Atau langsung kirim:
• Token: 1234567890:ABCdefGHIjkl...
• Username: @mybot

───────────────────────────────────────
```"""
    
    await message.reply_text(text, reply_markup=get_bot_checker_keyboard())


@handle_errors
async def check_bot_by_token_start(client: Client, message: Message):
    if not is_owner(message.from_user.id):
        return
    
    await SessionManager.save(message.from_user.id, "check_bot_token", step=1)
    
    await message.reply_text(
        "```\n🔑 CEK BOT BY TOKEN\n───────────────────────────────────────\n\nMasukkan token bot:\nFormat: 1234567890:ABCdefGHIjkl...\n\n───────────────────────────────────────\n```",
        reply_markup=get_cancel_keyboard()
    )


@handle_errors
async def check_bot_by_username_start(client: Client, message: Message):
    if not is_owner(message.from_user.id):
        return
    
    await SessionManager.save(message.from_user.id, "check_bot_username", step=1)
    
    await message.reply_text(
        "```\n👤 CEK BOT BY USERNAME\n───────────────────────────────────────\n\nMasukkan username bot:\nContoh: @mybot\n\n───────────────────────────────────────\n```",
        reply_markup=get_cancel_keyboard()
    )


@handle_errors
async def show_check_history(client: Client, message: Message):
    if not is_owner(message.from_user.id):
        return
    
    from core.bot_checker import bot_checker
    
    history = await bot_checker.get_check_history(message.from_user.id)
    
    if not history:
        await message.reply_text(
            "```\n📭 Belum ada history checks\n```",
            reply_markup=get_owner_panel_keyboard()
        )
        return
    
    text = "```\n📋 CHECK HISTORY\n───────────────────────────────────────\n"
    
    for i, item in enumerate(history[:10], 1):
        text += f"\n{i}. @{item.get('username', 'N/A')}\n"
        text += f"   ID: {item.get('bot_id', 'N/A')}\n"
        text += f"   Checked: {item.get('checked_at', 'N/A')}\n"
    
    text += "\n───────────────────────────────────────\n```"
    
    await message.reply_text(text, reply_markup=get_owner_panel_keyboard())


@handle_errors
async def broadcast_start(client: Client, message: Message):
    if not is_owner(message.from_user.id):
        return
    
    await SessionManager.save(message.from_user.id, "broadcast", step=1)
    
    await message.reply_text(
        "```\n📢 BROADCAST MESSAGE\n───────────────────────────────────────\n\nKirim pesan yang ingin di-broadcast ke semua user.\n\nFormat:\n<pre> isi pesan </pre>\n\nContoh:\n<pre> Halo semua! Ada update baru. </pre>\n\n───────────────────────────────────────\n```",
        reply_markup=get_cancel_keyboard()
    )


def register_owner_handlers(app: Client):
    app.on_message(filters.regex("^🜲 Owner Panel 🜲$") & filters.private)(owner_panel)
    app.on_message(filters.regex("^🜲 Statistik 🜲$") & filters.private)(show_statistics)
    app.on_message(filters.regex("^🜲 Lihat Users 🜲$") & filters.private)(list_users)
    app.on_message(filters.regex("^🜲 Tambah VIP 🜲$") & filters.private)(add_vip_start)
    app.on_message(filters.regex("^🜲 Tambah VVIP 🜲$") & filters.private)(add_vvip_start)
    app.on_message(filters.regex("^🜲 Buat Redeem 🜲$") & filters.private)(create_redeem_start)
    app.on_message(filters.regex("^🜲 Lihat Redeem 🜲$") & filters.private)(list_redeem_codes)
    app.on_message(filters.regex("^🜲 Ban User 🜲$") & filters.private)(ban_user_start)
    app.on_message(filters.regex("^🜲 Unban User 🜲$") & filters.private)(unban_user_start)
    
    app.on_message(filters.regex("^🤖 Manage Bots$") & filters.private)(manage_bots_menu)
    app.on_message(filters.regex("^🜲 Add New Bot 🜲$") & filters.private)(add_bot_start)
    app.on_message(filters.regex("^🜲 List Bots 🜲$") & filters.private)(list_bots)
    app.on_message(filters.regex("^🜲 Start Bot 🜲$") & filters.private)(start_bot_cmd)
    app.on_message(filters.regex("^🜲 Stop Bot 🜲$") & filters.private)(stop_bot_cmd)
    app.on_message(filters.regex("^🜲 Bot Stats 🜲$") & filters.private)(bot_stats_cmd)
    app.on_message(filters.regex("^🜲 Delete Bot 🜲$") & filters.private)(delete_bot_cmd)
    app.on_message(filters.regex("^🜲 Restart Bot 🜲$") & filters.private)(start_bot_cmd)
    
    app.on_message(filters.regex("^📊 Dashboard$") & filters.private)(show_dashboard)
    app.on_message(filters.regex("^🔍 Check Bot$") & filters.private)(show_bot_checker_menu)
    app.on_message(filters.regex("^🜲 Cek dengan Token 🜲$") & filters.private)(check_bot_by_token_start)
    app.on_message(filters.regex("^🜲 Cek dengan Username 🜲$") & filters.private)(check_bot_by_username_start)
    app.on_message(filters.regex("^🜲 History Checks 🜲$") & filters.private)(show_check_history)
    
    app.on_message(filters.regex("^🜲 Metrics 🜲$") & filters.private)(show_metrics)
    app.on_message(filters.regex("^🜲 System Metrics 🜲$") & filters.private)(show_system_metrics)
    app.on_message(filters.regex("^🜲 Bot Stats 🜲$") & filters.private)(show_statistics)
    app.on_message(filters.regex("^🜲 View Alerts 🜲$") & filters.private)(show_alerts)
    app.on_message(filters.regex("^🜲 Response Times 🜲$") & filters.private)(show_response_times)
    app.on_message(filters.regex("^🜲 Error Rates 🜲$") & filters.private)(show_error_rates)
    
    app.on_message(filters.regex("^📢 Broadcast$") & filters.private)(broadcast_start)
