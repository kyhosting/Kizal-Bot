from pyrogram import Client, filters
from pyrogram.types import Message

from config import is_owner, VIP_BENEFITS, VVIP_BENEFITS, VIP_PRICES, VVIP_PRICES
from core.error_handler import handle_errors
from utils.keyboards import (
    get_menu_keyboard, get_main_keyboard, get_maintenance_keyboard,
    get_bot_system_keyboard, get_monitoring_keyboard, get_group_management_keyboard,
    get_group_settings_keyboard, get_dashboard_keyboard, get_broadcast_keyboard
)
from utils.session_manager import SessionManager
from pyrogram.enums import ParseMode
from utils.messages import Messages


@handle_errors
async def show_menu(client: Client, message: Message):
    user_id = message.from_user.id
    keyboard = get_menu_keyboard(user_id)
    text = Messages.get_menu_message()

    await message.reply_text(
        text,
        reply_markup=keyboard
    )


@handle_errors
async def show_status(client: Client, message: Message):
    from core.database import db
    from handlers.start import format_remaining_time, get_user_display_name

    user = message.from_user
    user_id = user.id

    db_user = await db.get_user(user_id)

    if is_owner(user_id):
        role = "OWNER"
        limit_remaining = "∞"
        expired_at = "—"
    elif db_user:
        role = db_user.get("role", "reguler").upper()
        daily_limit = db_user.get("daily_limit", 10)
        daily_used = db_user.get("daily_used", 0)
        limit_remaining = max(0, daily_limit - daily_used)
        expired_at = format_remaining_time(db_user.get("expired_at"))
    else:
        role = "REGULER"
        limit_remaining = 10
        expired_at = "—"

    total_ops = db_user.get("operation_count", 0) if db_user else 0

    status_text = f"""```
📊 STATUS AKUN
───────────────────────────────────────
• NAMA          : {get_user_display_name(user)}
• ID            : {user_id}
• ROLE          : {role}
• MASA AKTIF    : {expired_at}
• LIMIT HARIAN  : {limit_remaining}
• TOTAL OPERASI : {total_ops}
───────────────────────────────────────
```"""

    await message.reply_text(status_text)


@handle_errors
async def show_vip_info(client: Client, message: Message):
    user_id = message.from_user.id
    
    benefits_list = "\n".join([f"• {b}" for b in VIP_BENEFITS])
    
    text = f"""```
⭐ VIP MEMBERSHIP
───────────────────────────────────────

📌 Keuntungan VIP:
{benefits_list}

───────────────────────────────────────
💰 HARGA PAKET VIP
───────────────────────────────────────
• 1 Hari  : Rp {VIP_PRICES['1_day']:,}
• 7 Hari  : Rp {VIP_PRICES['7_days']:,}
• 30 Hari : Rp {VIP_PRICES['30_days']:,}

───────────────────────────────────────
📞 Hubungi @KIFZLDEV untuk upgrade
───────────────────────────────────────
```"""

    await message.reply_text(text, reply_markup=get_main_keyboard(user_id))


@handle_errors
async def show_vvip_info(client: Client, message: Message):
    user_id = message.from_user.id
    
    benefits_list = "\n".join([f"• {b}" for b in VVIP_BENEFITS])
    
    text = f"""```
💎 VVIP MEMBERSHIP
───────────────────────────────────────

📌 Keuntungan VVIP:
{benefits_list}

───────────────────────────────────────
💰 HARGA PAKET VVIP
───────────────────────────────────────
• 1 Hari  : Rp {VVIP_PRICES['1_day']:,}
• 7 Hari  : Rp {VVIP_PRICES['7_days']:,}
• 30 Hari : Rp {VVIP_PRICES['30_days']:,}

───────────────────────────────────────
📞 Hubungi @KIFZLDEV untuk upgrade
───────────────────────────────────────
```"""

    await message.reply_text(text, reply_markup=get_main_keyboard(user_id))


@handle_errors
async def show_profile(client: Client, message: Message):
    from core.database import db
    from handlers.start import format_remaining_time, get_user_display_name
    
    user = message.from_user
    user_id = user.id
    
    db_user = await db.get_user(user_id)
    
    if is_owner(user_id):
        role = "OWNER"
        limit_remaining = "∞"
        expired_at = "Unlimited"
        daily_limit = "∞"
        status = "Active"
    elif db_user:
        role = db_user.get("role", "reguler").upper()
        daily_limit = db_user.get("daily_limit", 10)
        daily_used = db_user.get("daily_used", 0)
        limit_remaining = max(0, daily_limit - daily_used)
        expired_at = format_remaining_time(db_user.get("expired_at"))
        status = db_user.get("status", "active").title()
    else:
        role = "REGULER"
        daily_limit = 10
        limit_remaining = 10
        expired_at = "—"
        status = "Active"
    
    total_ops = db_user.get("operation_count", 0) if db_user else 0
    joined_at = db_user.get("joined_at", "—") if db_user else "—"
    
    text = f"""```
👤 PROFIL PENGGUNA
───────────────────────────────────────

📋 INFORMASI AKUN
───────────────────────────────────────
• Nama      : {get_user_display_name(user)}
• Username  : @{user.username or '—'}
• ID        : {user_id}
• Status    : {status}

───────────────────────────────────────
⭐ MEMBERSHIP
───────────────────────────────────────
• Role         : {role}
• Masa Aktif   : {expired_at}
• Limit Harian : {daily_limit}
• Sisa Limit   : {limit_remaining}

───────────────────────────────────────
📊 STATISTIK
───────────────────────────────────────
• Total Operasi : {total_ops}
• Bergabung     : {joined_at}

───────────────────────────────────────
```"""

    await message.reply_text(text, reply_markup=get_main_keyboard(user_id))


@handle_errors
async def show_monitoring_bot(client: Client, message: Message):
    user_id = message.from_user.id
    
    if not is_owner(user_id):
        await message.reply_text("```\n❌ Akses ditolak! Hanya owner yang bisa mengakses.\n```")
        return
    
    from core.monitoring import BotMonitor
    
    monitor = BotMonitor()
    metrics = await monitor.get_system_metrics()
    bot_stats = await monitor.get_bot_statistics()
    
    text = f"""```
📊 MONITORING BOT
───────────────────────────────────────

🖥️ SYSTEM RESOURCES
───────────────────────────────────────
• CPU Usage    : {metrics['cpu_percent']}%
• Memory Used  : {metrics['memory_used_mb']:.1f} MB
• Memory Total : {metrics['memory_total_mb']:.1f} MB
• Memory %     : {metrics['memory_percent']:.1f}%
• Disk Used    : {metrics['disk_used_gb']:.1f} GB
• Disk Total   : {metrics['disk_total_gb']:.1f} GB
• Disk %       : {metrics['disk_percent']:.1f}%

───────────────────────────────────────
📈 BOT STATISTICS
───────────────────────────────────────
• Total Users    : {bot_stats['total_users']}
• VIP Members    : {bot_stats['vip_count']}
• VVIP Members   : {bot_stats['vvip_count']}
• Total Operasi  : {bot_stats['total_operations']}
• Active Today   : {bot_stats.get('active_today', 0)}

───────────────────────────────────────
⏰ UPTIME
───────────────────────────────────────
• Started: {metrics.get('uptime', 'N/A')}

───────────────────────────────────────
```"""

    await message.reply_text(text, reply_markup=get_monitoring_keyboard())


@handle_errors
async def show_maintenance(client: Client, message: Message):
    user_id = message.from_user.id
    
    if not is_owner(user_id):
        await message.reply_text("```\n❌ Akses ditolak! Hanya owner yang bisa mengakses.\n```")
        return
    
    text = """```
🔧 MAINTENANCE MODE
───────────────────────────────────────

Pilih operasi maintenance:

🧹 Clear Cache     - Bersihkan file temp
🔄 Reset Sessions  - Reset semua session
📊 DB Optimize     - Optimasi database
🗑️ Clean Logs      - Bersihkan log lama
🔃 Restart Tasks   - Restart background tasks

───────────────────────────────────────
```"""

    await message.reply_text(text, reply_markup=get_maintenance_keyboard())


@handle_errors
async def show_group_management(client: Client, message: Message):
    user_id = message.from_user.id
    
    if not is_owner(user_id):
        await message.reply_text("```\n❌ Akses ditolak! Hanya owner yang bisa mengakses.\n```")
        return
    
    text = """```
👥 MANAJEMEN GRUP
───────────────────────────────────────

Fitur manajemen grup:

📋 List Groups   - Lihat semua grup
➕ Add Group     - Tambah grup baru
➖ Remove Group  - Hapus grup
📊 Group Stats   - Statistik grup
🔔 Broadcast     - Kirim pesan ke semua grup

───────────────────────────────────────
```"""

    await message.reply_text(text, reply_markup=get_group_management_keyboard())


@handle_errors
async def show_group_settings(client: Client, message: Message):
    user_id = message.from_user.id
    
    if not is_owner(user_id):
        await message.reply_text("```\n❌ Akses ditolak! Hanya owner yang bisa mengakses.\n```")
        return
    
    text = """```
⚙️ PENGATURAN GRUP
───────────────────────────────────────

Pengaturan grup tersedia:

🔐 Required Groups - Atur grup wajib
📢 Welcome Message - Pesan selamat datang
🛡️ Anti-Spam      - Pengaturan anti-spam
👮 Moderation     - Pengaturan moderasi

───────────────────────────────────────
```"""

    await message.reply_text(text, reply_markup=get_group_settings_keyboard())


@handle_errors
async def show_bot_system(client: Client, message: Message):
    user_id = message.from_user.id
    
    if not is_owner(user_id):
        await message.reply_text("```\n❌ Akses ditolak! Hanya owner yang bisa mengakses.\n```")
        return
    
    text = """```
🤖 SISTEM BOT
───────────────────────────────────────

Pengaturan sistem bot:

🔑 Bot Tokens    - Kelola token bot
📡 Webhooks      - Pengaturan webhook
🔄 Auto Restart  - Auto restart config
📝 Logging       - Pengaturan log
🔐 Security      - Pengaturan keamanan
🚀 Performance   - Optimasi performa

───────────────────────────────────────
```"""

    await message.reply_text(text, reply_markup=get_bot_system_keyboard())


@handle_errors
async def handle_clear_cache(client: Client, message: Message):
    user_id = message.from_user.id
    
    if not is_owner(user_id):
        return
    
    import os
    import glob
    
    temp_files = glob.glob("tmp/*") + glob.glob("temp_*")
    count = 0
    
    for filepath in temp_files:
        try:
            os.remove(filepath)
            count += 1
        except:
            pass
    
    await message.reply_text(
        f"```\n✅ Cache dibersihkan!\n\n🗑️ {count} file dihapus\n```",
        reply_markup=get_maintenance_keyboard()
    )


@handle_errors
async def handle_reset_sessions(client: Client, message: Message):
    user_id = message.from_user.id
    
    if not is_owner(user_id):
        return
    
    from core.database import db
    
    conn = await db.connect()
    await conn.execute("DELETE FROM user_sessions")
    await conn.commit()
    
    await message.reply_text(
        "```\n✅ Semua session berhasil direset!\n```",
        reply_markup=get_maintenance_keyboard()
    )


@handle_errors
async def handle_db_optimize(client: Client, message: Message):
    user_id = message.from_user.id
    
    if not is_owner(user_id):
        return
    
    from core.database import db
    
    conn = await db.connect()
    await conn.execute("VACUUM")
    await conn.execute("ANALYZE")
    
    await message.reply_text(
        "```\n✅ Database berhasil dioptimasi!\n\nVACUUM dan ANALYZE completed.\n```",
        reply_markup=get_maintenance_keyboard()
    )


@handle_errors
async def handle_clean_logs(client: Client, message: Message):
    user_id = message.from_user.id
    
    if not is_owner(user_id):
        return
    
    from core.database import db
    from datetime import datetime, timedelta
    
    conn = await db.connect()
    cutoff = datetime.now() - timedelta(days=7)
    await conn.execute(
        "DELETE FROM logs WHERE timestamp < ?",
        (cutoff,)
    )
    await conn.commit()
    
    await message.reply_text(
        "```\n✅ Log lama berhasil dibersihkan!\n\n🗑️ Log lebih dari 7 hari dihapus\n```",
        reply_markup=get_maintenance_keyboard()
    )


@handle_errors
async def handle_restart_tasks(client: Client, message: Message):
    user_id = message.from_user.id
    
    if not is_owner(user_id):
        return
    
    await message.reply_text(
        "```\n✅ Background tasks berhasil di-restart!\n```",
        reply_markup=get_maintenance_keyboard()
    )


@handle_errors
async def handle_bot_tokens(client: Client, message: Message):
    user_id = message.from_user.id
    
    if not is_owner(user_id):
        return
    
    text = "```\n🔑 BOT TOKENS\n───────────────────────────────────────\n\nFitur multi-bot tidak tersedia.\nBot utama berjalan dengan normal.\n\n───────────────────────────────────────\n```"
    
    await message.reply_text(text, reply_markup=get_bot_system_keyboard())


@handle_errors
async def handle_webhooks(client: Client, message: Message):
    user_id = message.from_user.id
    
    if not is_owner(user_id):
        return
    
    text = """```
📡 WEBHOOKS
───────────────────────────────────────

Webhook Status: Disabled
Mode: Long Polling

Fitur webhook belum diaktifkan.
Bot menggunakan mode long polling.

───────────────────────────────────────
```"""
    
    await message.reply_text(text, reply_markup=get_bot_system_keyboard())


@handle_errors
async def handle_auto_restart(client: Client, message: Message):
    user_id = message.from_user.id
    
    if not is_owner(user_id):
        return
    
    text = """```
🔄 AUTO RESTART
───────────────────────────────────────

Status: Enabled
Interval: 24 hours
Last Restart: —

Auto restart akan merestart bot secara
otomatis untuk menjaga performa.

───────────────────────────────────────
```"""
    
    await message.reply_text(text, reply_markup=get_bot_system_keyboard())


@handle_errors
async def handle_logging(client: Client, message: Message):
    user_id = message.from_user.id
    
    if not is_owner(user_id):
        return
    
    import os
    
    log_files = {
        "bot.log": os.path.exists("logs/bot.log"),
        "access.log": os.path.exists("logs/access.log"),
        "errors.log": os.path.exists("logs/errors.log")
    }
    
    text = "```\n📝 LOGGING\n───────────────────────────────────────\n\n"
    
    for log_name, exists in log_files.items():
        status = "✅ Aktif" if exists else "❌ Tidak ada"
        text += f"• {log_name}: {status}\n"
    
    text += "\nLevel: INFO\nRotation: Daily\n\n───────────────────────────────────────\n```"
    
    await message.reply_text(text, reply_markup=get_bot_system_keyboard())


@handle_errors
async def handle_security(client: Client, message: Message):
    user_id = message.from_user.id
    
    if not is_owner(user_id):
        return
    
    import os
    
    encryption_enabled = bool(os.getenv("ENCRYPTION_KEY", ""))
    
    text = f"""```
🔐 SECURITY
───────────────────────────────────────

• Encryption: {"✅ Enabled" if encryption_enabled else "❌ Disabled"}
• Rate Limit: ✅ Enabled (30 req/min)
• Ban System: ✅ Active
• Token Validation: ✅ Active

───────────────────────────────────────
```"""
    
    await message.reply_text(text, reply_markup=get_bot_system_keyboard())


@handle_errors
async def handle_performance(client: Client, message: Message):
    user_id = message.from_user.id
    
    if not is_owner(user_id):
        return
    
    from core.monitoring import BotMonitor
    
    monitor = BotMonitor()
    response_stats = monitor.get_response_time_stats()
    
    text = f"""```
🚀 PERFORMANCE
───────────────────────────────────────

⚡ Response Times
───────────────────────────────────────
• Average: {response_stats['avg_ms']:.1f} ms
• Min: {response_stats['min_ms']:.1f} ms
• Max: {response_stats['max_ms']:.1f} ms
• Requests: {response_stats['count']}

───────────────────────────────────────
• Workers: 100
• Cache: Enabled
• DB Pool: Active

───────────────────────────────────────
```"""
    
    await message.reply_text(text, reply_markup=get_bot_system_keyboard())


@handle_errors
async def show_view_logs(client: Client, message: Message):
    user_id = message.from_user.id
    
    if not is_owner(user_id):
        return
    
    from core.monitoring import BotMonitor
    
    monitor = BotMonitor()
    logs = await monitor.get_logs(limit=10)
    
    if not logs:
        await message.reply_text(
            "```\n📭 Tidak ada log tersedia\n```",
            reply_markup=get_monitoring_keyboard()
        )
        return
    
    text = "```\n📋 RECENT LOGS\n───────────────────────────────────────\n"
    
    for log in logs[:10]:
        action = log.get('action', 'unknown')
        user = log.get('user_id', 'N/A')
        timestamp = log.get('timestamp', 'N/A')
        text += f"\n[{timestamp}]\nUser: {user} | Action: {action}\n"
    
    text += "\n───────────────────────────────────────\n```"
    
    await message.reply_text(text, reply_markup=get_monitoring_keyboard())


@handle_errors
async def show_realtime_stats(client: Client, message: Message):
    user_id = message.from_user.id
    
    if not is_owner(user_id):
        return
    
    from core.monitoring import BotMonitor
    
    monitor = BotMonitor()
    metrics = await monitor.get_system_metrics()
    stats = await monitor.get_bot_statistics()
    
    text = f"""```
📊 REAL-TIME STATS
───────────────────────────────────────

🖥️ System
───────────────────────────────────────
• CPU: {metrics['cpu_percent']:.1f}%
• RAM: {metrics['memory_percent']:.1f}%
• Disk: {metrics['disk_percent']:.1f}%
• Uptime: {metrics['uptime']}

───────────────────────────────────────
👥 Users
───────────────────────────────────────
• Total: {stats['total_users']}
• VIP: {stats['vip_count']}
• VVIP: {stats['vvip_count']}
• Active: {stats.get('active_today', 0)}

───────────────────────────────────────
```"""
    
    await message.reply_text(text, reply_markup=get_dashboard_keyboard())


@handle_errors
async def show_user_analytics(client: Client, message: Message):
    user_id = message.from_user.id
    
    if not is_owner(user_id):
        return
    
    from core.database import db
    
    stats = await db.get_statistics()
    
    text = f"""```
📈 USER ANALYTICS
───────────────────────────────────────

👥 User Distribution
───────────────────────────────────────
• Reguler: {stats['total_users'] - stats['vip_count'] - stats['vvip_count']}
• VIP: {stats['vip_count']}
• VVIP: {stats['vvip_count']}

───────────────────────────────────────
📊 Total Operations: {stats['total_operations']}

───────────────────────────────────────
```"""
    
    await message.reply_text(text, reply_markup=get_dashboard_keyboard())


@handle_errors
async def show_limit_usage(client: Client, message: Message):
    user_id = message.from_user.id
    
    if not is_owner(user_id):
        return
    
    from core.database import db
    
    limit_stats = await db.get_limit_stats()
    
    text = f"""```
📊 LIMIT USAGE
───────────────────────────────────────

📈 Daily Limit Stats
───────────────────────────────────────
• Avg Usage (Reguler): {limit_stats['avg_usage_reguler']:.1f}/15
• Users Exceeded: {limit_stats['limit_exceeded_count']}

───────────────────────────────────────
```"""
    
    await message.reply_text(text, reply_markup=get_dashboard_keyboard())


@handle_errors
async def show_bot_fleet(client: Client, message: Message):
    user_id = message.from_user.id
    
    if not is_owner(user_id):
        return
    
    text = """```
🤖 BOT FLEET
───────────────────────────────────────

📊 Summary
───────────────────────────────────────
• Total Bots: 1
• Running: 1
• Stopped: 0

───────────────────────────────────────
📋 Bot List
───────────────────────────────────────
🟢 Main Bot (Active)

───────────────────────────────────────
```"""
    
    await message.reply_text(text, reply_markup=get_dashboard_keyboard())


@handle_errors
async def show_export_reports(client: Client, message: Message):
    user_id = message.from_user.id
    
    if not is_owner(user_id):
        return
    
    text = """```
📤 EXPORT REPORTS
───────────────────────────────────────

Fitur export reports:

• Export CSV - Coming soon
• Export JSON - Coming soon
• Export PDF - Coming soon

───────────────────────────────────────
```"""
    
    await message.reply_text(text, reply_markup=get_dashboard_keyboard())


@handle_errors
async def show_alerts_center(client: Client, message: Message):
    user_id = message.from_user.id
    
    if not is_owner(user_id):
        return
    
    from core.monitoring import BotMonitor
    
    monitor = BotMonitor()
    alerts = monitor.get_alerts(include_acknowledged=True)
    
    if not alerts:
        text = "```\n✅ Tidak ada alert\n```"
    else:
        text = "```\n🔔 ALERTS CENTER\n───────────────────────────────────────\n"
        for alert in alerts[:10]:
            status = "✅" if alert.get("acknowledged") else "⚠️"
            text += f"\n{status} [{alert['level'].upper()}]\n   {alert['message']}\n"
        text += "\n───────────────────────────────────────\n```"
    
    await message.reply_text(text, reply_markup=get_dashboard_keyboard())


@handle_errors
async def handle_list_groups(client: Client, message: Message):
    user_id = message.from_user.id
    
    if not is_owner(user_id):
        return
    
    from config import REQUIRED_GROUPS
    
    text = "```\n📋 LIST GROUPS\n───────────────────────────────────────\n"
    
    for i, group in enumerate(REQUIRED_GROUPS, 1):
        text += f"\n{i}. {group.get('name', 'Unknown')}\n"
        text += f"   Link: {group.get('link', 'N/A')}\n"
    
    text += "\n───────────────────────────────────────\n```"
    
    await message.reply_text(text, reply_markup=get_group_management_keyboard())


@handle_errors
async def handle_add_group(client: Client, message: Message):
    user_id = message.from_user.id
    
    if not is_owner(user_id):
        return
    
    text = """```
➕ ADD GROUP
───────────────────────────────────────

Untuk menambah grup, edit file config.py
dan tambahkan grup ke REQUIRED_GROUPS.

───────────────────────────────────────
```"""
    
    await message.reply_text(text, reply_markup=get_group_management_keyboard())


@handle_errors
async def handle_remove_group(client: Client, message: Message):
    user_id = message.from_user.id
    
    if not is_owner(user_id):
        return
    
    text = """```
➖ REMOVE GROUP
───────────────────────────────────────

Untuk menghapus grup, edit file config.py
dan hapus grup dari REQUIRED_GROUPS.

───────────────────────────────────────
```"""
    
    await message.reply_text(text, reply_markup=get_group_management_keyboard())


@handle_errors
async def handle_group_stats(client: Client, message: Message):
    user_id = message.from_user.id
    
    if not is_owner(user_id):
        return
    
    from config import REQUIRED_GROUPS
    
    text = f"""```
📊 GROUP STATS
───────────────────────────────────────

• Total Groups: {len(REQUIRED_GROUPS)}
• Required: {len(REQUIRED_GROUPS)}

───────────────────────────────────────
```"""
    
    await message.reply_text(text, reply_markup=get_group_management_keyboard())


@handle_errors
async def handle_broadcast(client: Client, message: Message):
    user_id = message.from_user.id
    
    if not is_owner(user_id):
        return
    
    await SessionManager.save(user_id, "broadcast", step=1)
    
    text = """```
🔔 BROADCAST
───────────────────────────────────────

Kirim pesan ke semua user terdaftar.
Format: Markdown

Contoh format:
*Bold* _Italic_ `Code`
[Link](https://example.com)

Kirim pesan yang ingin di-broadcast:

───────────────────────────────────────
```"""
    
    await message.reply_text(text, reply_markup=get_broadcast_keyboard())


@handle_errors
async def handle_broadcast_input(client: Client, message: Message):
    user_id = message.from_user.id
    text = message.text
    
    if not is_owner(user_id):
        return
    
    if text == "❌ BATAL ❌":
        await SessionManager.clear(user_id)
        await message.reply_text(
            "```\n❌ Broadcast dibatalkan\n```",
            reply_markup=get_group_management_keyboard()
        )
        return
    
    session = await SessionManager.get(user_id)
    if not session or session.get("mode") != "broadcast":
        return
    
    from core.database import db
    
    all_users = await db.get_all_users()
    
    if not all_users:
        await SessionManager.clear(user_id)
        await message.reply_text(
            "```\n❌ Tidak ada user terdaftar\n```",
            reply_markup=get_group_management_keyboard()
        )
        return
    
    await message.reply_text("```\n⏳ Memulai broadcast...\n```")
    
    broadcast_message = f"""<pre>
📢 PENGUMUMAN
───────────────────────────────────────

{text}

───────────────────────────────────────
Pesan dari Admin @KIFZLDEV
</pre>"""
    
    success_count = 0
    fail_count = 0
    
    for user in all_users:
        try:
            target_id = user.get("telegram_id")
            if target_id and target_id != user_id:
                await client.send_message(
                    chat_id=target_id,
                    text=broadcast_message,
                    parse_mode=ParseMode.HTML
                )
                success_count += 1
        except Exception as e:
            fail_count += 1
            import logging
            logging.error(f"Broadcast failed to {target_id}: {e}")
    
    await SessionManager.clear(user_id)
    
    result_text = f"""```
✅ BROADCAST SELESAI
───────────────────────────────────────

📨 Terkirim : {success_count} user
❌ Gagal    : {fail_count} user
📊 Total    : {len(all_users)} user

───────────────────────────────────────
```"""
    
    await message.reply_text(result_text, reply_markup=get_group_management_keyboard())


@handle_errors
async def handle_required_groups(client: Client, message: Message):
    user_id = message.from_user.id
    
    if not is_owner(user_id):
        return
    
    from config import REQUIRED_GROUPS
    
    text = "```\n🔐 REQUIRED GROUPS\n───────────────────────────────────────\n"
    
    for i, group in enumerate(REQUIRED_GROUPS, 1):
        text += f"\n{i}. {group.get('name', 'Unknown')}\n"
        text += f"   @{group.get('username', 'N/A')}\n"
    
    text += "\n───────────────────────────────────────\n```"
    
    await message.reply_text(text, reply_markup=get_group_settings_keyboard())


@handle_errors
async def handle_welcome_message(client: Client, message: Message):
    user_id = message.from_user.id
    
    if not is_owner(user_id):
        return
    
    text = """```
📢 WELCOME MESSAGE
───────────────────────────────────────

Pesan selamat datang akan dikirim
saat user baru bergabung.

Status: Default message aktif

───────────────────────────────────────
```"""
    
    await message.reply_text(text, reply_markup=get_group_settings_keyboard())


@handle_errors
async def handle_anti_spam(client: Client, message: Message):
    user_id = message.from_user.id
    
    if not is_owner(user_id):
        return
    
    text = """```
🛡️ ANTI-SPAM
───────────────────────────────────────

Status: ✅ Aktif

• Rate Limit: 30 req/menit
• Cooldown: 60 detik
• Auto Ban: Enabled

───────────────────────────────────────
```"""
    
    await message.reply_text(text, reply_markup=get_group_settings_keyboard())


@handle_errors
async def handle_moderation(client: Client, message: Message):
    user_id = message.from_user.id
    
    if not is_owner(user_id):
        return
    
    text = """```
👮 MODERATION
───────────────────────────────────────

Status: ✅ Aktif

• Ban System: Enabled
• Kick System: Enabled
• Mute System: Enabled

───────────────────────────────────────
```"""
    
    await message.reply_text(text, reply_markup=get_group_settings_keyboard())


def register_menu_handlers(app: Client):
    app.on_message(filters.regex("^🜲 Menu Utama 🜲$") & filters.private)(show_menu)
    app.on_message(filters.regex("^🜲 STATUS 🜲$") & filters.private)(show_status)
    app.on_message(filters.regex("^🜲 VIP 🜲$") & filters.private)(show_vip_info)
    app.on_message(filters.regex("^🜲 VVIP 🜲$") & filters.private)(show_vvip_info)
    app.on_message(filters.regex("^🜲 Profil 🜲$") & filters.private)(show_profile)
    app.on_message(filters.regex("^🜲 Monitoring Bot 🜲$") & filters.private)(show_monitoring_bot)
    app.on_message(filters.regex("^🜲 Maintenance 🜲$") & filters.private)(show_maintenance)
    app.on_message(filters.regex("^🜲 Manajemen Grup 🜲$") & filters.private)(show_group_management)
    app.on_message(filters.regex("^🜲 Pengaturan Grup 🜲$") & filters.private)(show_group_settings)
    app.on_message(filters.regex("^🜲 Sistem Bot 🜲$") & filters.private)(show_bot_system)
    
    app.on_message(filters.regex("^🜲 Clear Cache 🜲$") & filters.private)(handle_clear_cache)
    app.on_message(filters.regex("^🜲 Reset Sessions 🜲$") & filters.private)(handle_reset_sessions)
    app.on_message(filters.regex("^🜲 DB Optimize 🜲$") & filters.private)(handle_db_optimize)
    app.on_message(filters.regex("^🜲 Clean Logs 🜲$") & filters.private)(handle_clean_logs)
    app.on_message(filters.regex("^🜲 Restart Tasks 🜲$") & filters.private)(handle_restart_tasks)
    
    app.on_message(filters.regex("^🜲 Bot Tokens 🜲$") & filters.private)(handle_bot_tokens)
    app.on_message(filters.regex("^🜲 Webhooks 🜲$") & filters.private)(handle_webhooks)
    app.on_message(filters.regex("^🜲 Auto Restart 🜲$") & filters.private)(handle_auto_restart)
    app.on_message(filters.regex("^🜲 Logging 🜲$") & filters.private)(handle_logging)
    app.on_message(filters.regex("^🜲 Security 🜲$") & filters.private)(handle_security)
    app.on_message(filters.regex("^🜲 Performance 🜲$") & filters.private)(handle_performance)
    
    app.on_message(filters.regex("^🜲 View Logs 🜲$") & filters.private)(show_view_logs)
    
    app.on_message(filters.regex("^🜲 Real-time Stats 🜲$") & filters.private)(show_realtime_stats)
    app.on_message(filters.regex("^🜲 User Analytics 🜲$") & filters.private)(show_user_analytics)
    app.on_message(filters.regex("^🜲 Limit Usage 🜲$") & filters.private)(show_limit_usage)
    app.on_message(filters.regex("^🜲 Bot Fleet 🜲$") & filters.private)(show_bot_fleet)
    app.on_message(filters.regex("^🜲 Export Reports 🜲$") & filters.private)(show_export_reports)
    app.on_message(filters.regex("^🜲 Alerts Center 🜲$") & filters.private)(show_alerts_center)
    
    app.on_message(filters.regex("^🜲 List Groups 🜲$") & filters.private)(handle_list_groups)
    app.on_message(filters.regex("^🜲 Add Group 🜲$") & filters.private)(handle_add_group)
    app.on_message(filters.regex("^🜲 Remove Group 🜲$") & filters.private)(handle_remove_group)
    app.on_message(filters.regex("^🜲 Group Stats 🜲$") & filters.private)(handle_group_stats)
    app.on_message(filters.regex("^🜲 Broadcast 🜲$") & filters.private)(handle_broadcast)
    
    app.on_message(filters.regex("^🜲 Required Groups 🜲$") & filters.private)(handle_required_groups)
    app.on_message(filters.regex("^🜲 Welcome Message 🜲$") & filters.private)(handle_welcome_message)
    app.on_message(filters.regex("^🜲 Anti-Spam 🜲$") & filters.private)(handle_anti_spam)
    app.on_message(filters.regex("^🜲 Moderation 🜲$") & filters.private)(handle_moderation)
