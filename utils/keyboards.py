from pyrogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from config import is_owner, REQUIRED_GROUPS


def get_main_keyboard(user_id: int, is_private: bool = True) -> ReplyKeyboardMarkup:
    if is_owner(user_id):
        keyboard = [
            [KeyboardButton("🜲 Menu Utama 🜲")],
            [KeyboardButton("🜲 Monitoring Bot 🜲"), KeyboardButton("🜲 Maintenance 🜲")],
            [KeyboardButton("🜲 Manajemen Grup 🜲"), KeyboardButton("🜲 Owner Panel 🜲")],
            [KeyboardButton("🜲 Pengaturan Grup 🜲"), KeyboardButton("🜲 Sistem Bot 🜲")]
        ]
    else:
        if is_private:
            keyboard = [
                [KeyboardButton("🜲 Menu Utama 🜲")],
                [KeyboardButton("🜲 VIP 🜲"), KeyboardButton("🜲 VVIP 🜲")],
                [KeyboardButton("🎁 Redeem Code"), KeyboardButton("🜲 Profil 🜲")]
            ]
        else:
            keyboard = [
                [KeyboardButton("🜲 Menu Utama 🜲")],
                [KeyboardButton("🜲 VIP 🜲"), KeyboardButton("🜲 VVIP 🜲")],
                [KeyboardButton("🎁 Redeem Code")]
            ]

    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_menu_keyboard(user_id: int) -> ReplyKeyboardMarkup:
    if is_owner(user_id):
        keyboard = [
            [KeyboardButton("🜲 MSG TO TXT 🜲"), KeyboardButton("🜲 TXT TO VCF 🜲")],
            [KeyboardButton("🜲 VCF TO TXT 🜲"), KeyboardButton("🜲 XLS TO VCF 🜲")],
            [KeyboardButton("🜲 RAPIKAN TXT 🜲"), KeyboardButton("🜲 GABUNG FILE 🜲")],
            [KeyboardButton("🜲 HITUNG KONTAK 🜲"), KeyboardButton("🜲 CEK NAMA 🜲")],
            [KeyboardButton("🜲 SPLIT FILE 🜲"), KeyboardButton("🜲 CREATE ADM/NAVY 🜲")],
            [KeyboardButton("🜲 STATUS 🜲")],
            [KeyboardButton("🔙 KEMBALI 🔙")]
        ]
    else:
        keyboard = [
            [KeyboardButton("🜲 MSG TO TXT 🜲"), KeyboardButton("🜲 TXT TO VCF 🜲")],
            [KeyboardButton("🜲 VCF TO TXT 🜲"), KeyboardButton("🜲 XLS TO VCF 🜲")],
            [KeyboardButton("🜲 RAPIKAN TXT 🜲"), KeyboardButton("🜲 GABUNG FILE 🜲")],
            [KeyboardButton("🜲 HITUNG KONTAK 🜲"), KeyboardButton("🜲 CEK NAMA 🜲")],
            [KeyboardButton("🜲 SPLIT FILE 🜲"), KeyboardButton("🜲 CREATE ADM/NAVY 🜲")],
            [KeyboardButton("🜲 STATUS 🜲"), KeyboardButton("🎁 Redeem Code")],
            [KeyboardButton("🔙 KEMBALI 🔙")]
        ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [[KeyboardButton("❌ BATAL ❌")]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_done_batal_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton("✅ Done"), KeyboardButton("❌ Batal")],
        [KeyboardButton("⏭️ Lanjut")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_mode_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton("🜲 MODE A - GUIDED 🜲")],
        [KeyboardButton("🜲 MODE B - AUTO PARSE 🜲")],
        [KeyboardButton("🜲 MODE C - MINIMAL 🜲")],
        [KeyboardButton("❌ BATAL ❌")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_split_mode_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton("🜲 PER KONTAK 🜲"), KeyboardButton("🜲 PER BAGIAN 🜲")],
        [KeyboardButton("❌ BATAL ❌")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_merge_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton("✅ SELESAI ✅")],
        [KeyboardButton("❌ BATAL ❌")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_verification_keyboard() -> InlineKeyboardMarkup:
    buttons = []
    
    if len(REQUIRED_GROUPS) >= 1 and REQUIRED_GROUPS[0].get("link"):
        buttons.append([InlineKeyboardButton("🜲 Join Grup 1 🜲", url=REQUIRED_GROUPS[0]["link"])])
    
    if len(REQUIRED_GROUPS) >= 2 and REQUIRED_GROUPS[1].get("link"):
        buttons.append([InlineKeyboardButton("🜲 Join Grup 2 🜲", url=REQUIRED_GROUPS[1]["link"])])
    
    buttons.append([InlineKeyboardButton("🜲 Verifikasi Ulang 🜲", callback_data="verify_recheck")])
    
    return InlineKeyboardMarkup(buttons)


def get_owner_panel_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton("🜲 Statistik 🜲"), KeyboardButton("🜲 Lihat Users 🜲")],
        [KeyboardButton("🜲 Tambah VIP 🜲"), KeyboardButton("🜲 Tambah VVIP 🜲")],
        [KeyboardButton("🜲 Buat Redeem 🜲"), KeyboardButton("🜲 Lihat Redeem 🜲")],
        [KeyboardButton("🜲 Ban User 🜲"), KeyboardButton("🜲 Unban User 🜲")],
        [KeyboardButton("🤖 Manage Bots"), KeyboardButton("📊 Dashboard")],
        [KeyboardButton("🔍 Check Bot"), KeyboardButton("🜲 Metrics 🜲")],
        [KeyboardButton("📢 Broadcast")],
        [KeyboardButton("🔙 KEMBALI 🔙")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_redeem_type_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton("🎲 RANDOM CODE")],
        [KeyboardButton("✍️ CUSTOM CODE")],
        [KeyboardButton("❌ BATAL ❌")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_maintenance_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton("🜲 Clear Cache 🜲"), KeyboardButton("🜲 Reset Sessions 🜲")],
        [KeyboardButton("🜲 DB Optimize 🜲"), KeyboardButton("🜲 Clean Logs 🜲")],
        [KeyboardButton("🜲 Restart Tasks 🜲")],
        [KeyboardButton("🔙 KEMBALI 🔙")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_bot_system_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton("🜲 Bot Tokens 🜲"), KeyboardButton("🜲 Webhooks 🜲")],
        [KeyboardButton("🜲 Auto Restart 🜲"), KeyboardButton("🜲 Logging 🜲")],
        [KeyboardButton("🜲 Security 🜲"), KeyboardButton("🜲 Performance 🜲")],
        [KeyboardButton("🔙 KEMBALI 🔙")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_bot_management_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton("🜲 Add New Bot 🜲"), KeyboardButton("🜲 List Bots 🜲")],
        [KeyboardButton("🜲 Start Bot 🜲"), KeyboardButton("🜲 Stop Bot 🜲")],
        [KeyboardButton("🜲 Bot Stats 🜲"), KeyboardButton("🜲 Restart Bot 🜲")],
        [KeyboardButton("🜲 Delete Bot 🜲")],
        [KeyboardButton("🔙 KEMBALI 🔙")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_monitoring_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton("🜲 System Metrics 🜲"), KeyboardButton("🜲 Bot Stats 🜲")],
        [KeyboardButton("🜲 View Alerts 🜲"), KeyboardButton("🜲 View Logs 🜲")],
        [KeyboardButton("🜲 Response Times 🜲"), KeyboardButton("🜲 Error Rates 🜲")],
        [KeyboardButton("🔙 KEMBALI 🔙")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_role_duration_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton("🜲 1 Hari 🜲"), KeyboardButton("🜲 7 Hari 🜲")],
        [KeyboardButton("🜲 30 Hari 🜲"), KeyboardButton("🜲 90 Hari 🜲")],
        [KeyboardButton("❌ BATAL ❌")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_confirm_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton("✅ KONFIRMASI"), KeyboardButton("❌ BATAL ❌")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_bot_checker_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton("🜲 Cek dengan Token 🜲")],
        [KeyboardButton("🜲 Cek dengan Username 🜲")],
        [KeyboardButton("🜲 History Checks 🜲")],
        [KeyboardButton("🔙 KEMBALI 🔙")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_bot_action_keyboard(bot_id: int = None) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton("💾 Save to My Bots", callback_data=f"save_bot_{bot_id}" if bot_id else "save_bot"),
            InlineKeyboardButton("🔄 Check Another", callback_data="check_another")
        ]
    ]
    return InlineKeyboardMarkup(buttons)


def get_dashboard_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton("🜲 Real-time Stats 🜲"), KeyboardButton("🜲 User Analytics 🜲")],
        [KeyboardButton("🜲 Limit Usage 🜲"), KeyboardButton("🜲 Bot Fleet 🜲")],
        [KeyboardButton("🜲 Export Reports 🜲"), KeyboardButton("🜲 Alerts Center 🜲")],
        [KeyboardButton("🔙 KEMBALI 🔙")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_limit_upgrade_inline() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton("🎁 Gunakan Redeem Code", callback_data="use_redeem")],
        [InlineKeyboardButton("💎 Upgrade ke VVIP", callback_data="upgrade_vvip")],
        [InlineKeyboardButton("📞 Hubungi Admin", url="https://t.me/KIFZLDEV")]
    ]
    return InlineKeyboardMarkup(buttons)


def get_group_management_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton("🜲 List Groups 🜲"), KeyboardButton("🜲 Add Group 🜲")],
        [KeyboardButton("🜲 Remove Group 🜲"), KeyboardButton("🜲 Group Stats 🜲")],
        [KeyboardButton("🜲 Broadcast 🜲")],
        [KeyboardButton("🔙 KEMBALI 🔙")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_group_settings_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton("🜲 Required Groups 🜲"), KeyboardButton("🜲 Welcome Message 🜲")],
        [KeyboardButton("🜲 Anti-Spam 🜲"), KeyboardButton("🜲 Moderation 🜲")],
        [KeyboardButton("🔙 KEMBALI 🔙")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_broadcast_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton("❌ BATAL ❌")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
