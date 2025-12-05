# KIFZL DEV BOT - Pyrogram v2

## Overview

Bot Telegram premium berbasis Pyrogram v2 dengan SQLite database lokal. Bot ini adalah clone dari bot lama dengan enhanced infrastructure menggunakan Pyrogram async framework.

## Project Structure

```
/
├── bot.py                      # Main entry point
├── config.py                   # Configuration
├── requirements.txt            # Python dependencies
├── db/                         # SQLite database directory
│   └── data.db                 # SQLite database file
├── core/                       # Core modules
│   ├── database.py             # SQLite connection & models
│   ├── security.py             # AES-256 encryption
│   ├── logger.py               # Logging system with rotation
│   ├── error_handler.py        # Error handling
│   ├── bot_manager.py          # Multi-bot management system
│   ├── monitoring.py           # Metrics, alerts, dashboard
│   └── background_tasks.py     # Auto tasks & health checks
├── handlers/                   # Command handlers
│   ├── start.py                # /start command
│   ├── menu.py                 # Menu system (13 buttons)
│   ├── verify.py               # Group verification
│   ├── owner.py                # Owner panel + bot management
│   ├── redeem.py               # Redeem system
│   └── file_commands/          # File processing features
│       ├── buat_admin_navy.py  # 3 Mode (A, B, C)
│       ├── split_file.py       # 6 Steps
│       ├── gabung_file.py      # Auto detection TXT/VCF
│       ├── msg_to_txt.py       # Converter
│       ├── txt_to_vcf.py       # Converter
│       ├── vcf_to_txt.py       # Converter
│       ├── xlsx_to_vcf.py      # Converter
│       ├── rapikan_txt.py      # Text cleaning
│       ├── hitung_kontak.py    # Count contacts
│       └── cek_nama_kontak.py  # Check names
├── utils/                      # Utilities
│   ├── keyboards.py            # Reply keyboard layouts
│   ├── messages.py             # Template messages
│   ├── file_utils.py           # File processing utilities
│   ├── vcf_utils.py            # VCF processing
│   └── session_manager.py      # Session management
├── tmp/                        # Temporary files (auto delete)
└── logs/                       # Log files with rotation
```

## Features

### Role System
- **REGULER**: Limited access (10 daily operations)
- **VIP**: Full access (50 daily operations)
- **VVIP**: Premium access (100 daily operations)
- **OWNER**: Unlimited access + management

### 13 Menu Buttons (All Functional)
1. **Menu Utama** - Main menu with all file tools
2. **STATUS** - View account status
3. **VIP** - VIP membership info
4. **VVIP** - VVIP membership info
5. **Profil** - Detailed user profile
6. **Redeem** - Redeem VIP/VVIP codes
7. **Monitoring Bot** - System metrics (owner only)
8. **Maintenance** - Cache/session cleanup (owner only)
9. **Manajemen Grup** - Group management (owner only)
10. **Pengaturan Grup** - Group settings (owner only)
11. **Sistem Bot** - Bot system settings (owner only)
12. **Owner Panel** - User & bot management (owner only)
13. **KEMBALI** - Back to start

### File Processing Tools
1. **MSG → TXT**: Convert messages to text file
2. **TXT → VCF**: Convert text to VCF contacts
3. **VCF → TXT**: Extract numbers from VCF
4. **XLS → VCF**: Convert Excel to VCF
5. **RAPIKAN TXT**: Clean and format text files
6. **GABUNG FILE**: Merge multiple files
7. **SPLIT FILE**: Split files (6-step process)
8. **HITUNG KONTAK**: Count contacts
9. **CEK NAMA**: Check contact names
10. **CREATE ADMIN/NAVY**: Create admin & navy contacts (3 modes)

### Multi-Bot Management (Owner Panel)
- Add new bots with encrypted token storage
- Start/Stop/Restart managed bots
- View bot statistics and status
- Delete bots from management

### Monitoring Dashboard (Owner)
- System metrics (CPU, Memory, Disk)
- Response time tracking
- Error rate monitoring
- Active alerts with notifications
- Bot statistics

### Systems
- **Redeem System**: VIP/VVIP code redemption
- **Owner Panel**: User management, statistics, code generation
- **Group Verification**: Required group membership
- **Background Tasks**: Auto expiry check, temp cleanup, health checks
- **Alert System**: Critical event notifications to owner

## Environment Variables

Required:
- `TELEGRAM_BOT_TOKEN`: Bot token from @BotFather
- `API_ID`: Telegram API ID from my.telegram.org
- `API_HASH`: Telegram API Hash from my.telegram.org

Optional:
- `OWNER_ID`: Owner's Telegram user ID (default: 8317563450)
- `ENCRYPTION_KEY`: Key for persistent AES-256 encryption of multi-bot tokens (if not set, uses auto-generated key that won't persist across restarts)

## Tech Stack
- Python 3.11+
- Pyrogram v2 (async Telegram MTProto)
- SQLite + aiosqlite (local database)
- cryptography (AES-256-GCM encryption)
- openpyxl (Excel processing)
- vobject (VCF processing)
- psutil (System monitoring)

## Running the Bot

```bash
python bot.py
```

## Recent Changes (December 2025)
- Added comprehensive monitoring system (CPU/Memory/Disk metrics)
- Implemented multi-bot management with encrypted token storage
- Created alert system with Telegram notifications
- Enhanced logging with rotation support
- Added response time and error rate tracking
- Implemented all 13 menu button handlers
- Added background health checks and maintenance tasks
- Session cleanup and expired user handling

### Bug Fixes (December 5, 2025)
- Fixed all keyboard button handlers - every button now has a working handler
- Fixed owner /start menu - owner now sees owner keyboard directly
- Fixed Menu Utama for owner - removed Redeem Code (owner doesn't need it)
- Multi-Bot system now uses SQLite (multi_bot table) - real ONLINE status checking via Telegram API
- Added KEMBALI (Back) button to all keyboards for proper navigation
- Fixed all Sistem Bot menu handlers (Bot Tokens, Webhooks, Auto Restart, Logging, Security, Performance)
- Fixed all Maintenance menu handlers (Clear Cache, Reset Sessions, DB Optimize, Clean Logs, Restart Tasks)
- Fixed all Monitoring menu handlers (System Metrics, View Alerts, View Logs, Response Times, Error Rates)
- Fixed all Dashboard menu handlers (Real-time Stats, User Analytics, Limit Usage, Bot Fleet, Export Reports, Alerts Center)
- Fixed all Group Management menu handlers (List Groups, Add Group, Remove Group, Group Stats, Broadcast)
- Fixed all Group Settings menu handlers (Required Groups, Welcome Message, Anti-Spam, Moderation)

### Multi-Bot System (December 5, 2025) - REAL RUNNING BOTS
- Multi-bot system now ACTUALLY RUNS managed bots using Pyrogram Client
- Each managed bot is started as a real Pyrogram client (not just token verification)
- Bots can receive and respond to /start and messages
- Auto-start all bots on main bot startup (3 second delay)
- Status: "running" means bot is ACTUALLY receiving messages
- Status: "stopped" means bot token valid but not started
- Status: "error" means failed to start
- Each managed bot responds with "Bot ONLINE" confirmation
- Uses same API_ID and API_HASH as main bot

## User Preferences
- All interactions via keyboard buttons
- Markdown formatting for messages
- Auto-cleanup temporary files
- Session tracking for multi-step processes
- Response time target: < 2 seconds

## Anti-Theft Protection
Bot creator credit: @KIFZLDEV (must not be changed)

## Credits
Created by: @KIFZLDEV
