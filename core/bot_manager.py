import os
import asyncio
import logging
import aiohttp
from typing import Dict, Any, List, Optional
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.handlers import MessageHandler

logger = logging.getLogger("bot")


class BotInstance:
    def __init__(self, bot_id: int, name: str, token: str):
        self.bot_id = bot_id
        self.name = name
        self.token = token
        self.client: Optional[Client] = None
        self.status = "offline"
        self.started_at: Optional[datetime] = None
        self.user_count = 0
        self.message_count = 0
        self.error_count = 0
        self.last_activity: Optional[datetime] = None
        self.bot_username: Optional[str] = None
        self.bot_telegram_id: Optional[int] = None
        self.is_running = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "bot_id": self.bot_id,
            "name": self.name,
            "status": self.status,
            "is_running": self.is_running,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "user_count": self.user_count,
            "message_count": self.message_count,
            "error_count": self.error_count,
            "last_activity": self.last_activity.isoformat() if self.last_activity else None,
            "bot_username": self.bot_username,
            "bot_telegram_id": self.bot_telegram_id
        }


class BotManager:
    _instance = None
    _bots: Dict[int, BotInstance] = {}
    _db = None
    _running_clients: Dict[int, Client] = {}
    _api_id: int = 0
    _api_hash: str = ""
    _main_bot = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._bots = {}
            cls._running_clients = {}
        return cls._instance
    
    async def initialize(self, api_id: int = None, api_hash: str = None, main_bot: Client = None):
        from core.database import db
        from config import API_ID, API_HASH
        
        self._db = db
        self._api_id = api_id or API_ID
        self._api_hash = api_hash or API_HASH
        self._main_bot = main_bot
        
        await self._load_bots_from_db()
        asyncio.create_task(self._auto_start_all_bots())
        logger.info("BotManager initialized")
    
    async def _load_bots_from_db(self):
        conn = await self._db.connect()
        cursor = await conn.execute("SELECT * FROM multi_bot")
        rows = await cursor.fetchall()
        
        for row in rows:
            bot_data = dict(row)
            instance = BotInstance(
                bot_id=bot_data['id'],
                name=bot_data.get('name', f"Bot-{bot_data['id']}"),
                token=bot_data['token']
            )
            instance.status = bot_data.get('status', 'offline')
            instance.bot_username = bot_data.get('bot_username')
            instance.bot_telegram_id = bot_data.get('bot_telegram_id')
            self._bots[bot_data['id']] = instance
        
        logger.info(f"Loaded {len(self._bots)} bots from database")
    
    async def _auto_start_all_bots(self):
        await asyncio.sleep(3)
        for bot_id in list(self._bots.keys()):
            try:
                result = await self.start_bot(bot_id)
                if result.get('success'):
                    logger.info(f"Auto-started bot ID {bot_id}")
                else:
                    logger.warning(f"Failed to auto-start bot ID {bot_id}: {result.get('message')}")
            except Exception as e:
                logger.error(f"Error auto-starting bot {bot_id}: {e}")
            await asyncio.sleep(1)
    
    async def _verify_token_online(self, token: str) -> tuple:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"https://api.telegram.org/bot{token}/getMe",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    data = await response.json()
                    
                    if data.get("ok"):
                        bot_info = data.get("result", {})
                        return True, bot_info
                    else:
                        return False, {"error": data.get("description", "Invalid token")}
        except asyncio.TimeoutError:
            return False, {"error": "Timeout"}
        except Exception as e:
            return False, {"error": str(e)}
    
    def _create_bot_handlers(self, instance: BotInstance):
        
        async def start_handler(client: Client, message: Message):
            instance.message_count += 1
            instance.last_activity = datetime.now()
            
            await message.reply_text(
                f"**Halo! Saya @{instance.bot_username}**\n\n"
                f"Bot ini dikelola oleh KIFZL DEV BOT System.\n"
                f"Created by: @KIFZLDEV\n\n"
                f"Status: **ONLINE** ✅"
            )
        
        async def message_handler(client: Client, message: Message):
            instance.message_count += 1
            instance.last_activity = datetime.now()
            
            await message.reply_text(
                f"Pesan diterima!\n"
                f"Bot: @{instance.bot_username}\n"
                f"Status: ONLINE ✅"
            )
        
        return start_handler, message_handler
    
    async def add_bot(self, name: str, token: str, created_by: int = None) -> Dict[str, Any]:
        if not self._validate_token_format(token):
            return {"success": False, "message": "Token format tidak valid"}
        
        is_valid, bot_info = await self._verify_token_online(token)
        if not is_valid:
            return {"success": False, "message": f"Token tidak valid: {bot_info.get('error', 'Unknown error')}"}
        
        try:
            conn = await self._db.connect()
            
            cursor = await conn.execute("SELECT id FROM multi_bot WHERE token = ?", (token,))
            existing = await cursor.fetchone()
            if existing:
                return {"success": False, "message": "Bot token sudah terdaftar"}
            
            cursor = await conn.execute("""
                INSERT INTO multi_bot (token, name, status, added_by, last_check, bot_username, bot_telegram_id)
                VALUES (?, ?, 'offline', ?, CURRENT_TIMESTAMP, ?, ?)
            """, (token, name, created_by, bot_info.get('username'), bot_info.get('id')))
            await conn.commit()
            
            bot_id = cursor.lastrowid
            
            instance = BotInstance(bot_id=bot_id, name=name, token=token)
            instance.bot_username = bot_info.get('username')
            instance.bot_telegram_id = bot_info.get('id')
            self._bots[bot_id] = instance
            
            start_result = await self.start_bot(bot_id)
            
            logger.info(f"Bot added: {name} (ID: {bot_id}) - @{bot_info.get('username')}")
            
            if start_result.get('success'):
                return {
                    "success": True,
                    "bot_id": bot_id,
                    "username": bot_info.get('username'),
                    "message": f"Bot '{name}' berhasil ditambahkan dan RUNNING! ✅\n@{bot_info.get('username')} sekarang ONLINE dan bisa menerima pesan."
                }
            else:
                return {
                    "success": True,
                    "bot_id": bot_id,
                    "username": bot_info.get('username'),
                    "message": f"Bot '{name}' berhasil ditambahkan tapi gagal start: {start_result.get('message')}"
                }
            
        except Exception as e:
            logger.error(f"Failed to add bot: {e}")
            return {"success": False, "message": f"Gagal menambahkan bot: {str(e)}"}
    
    def _validate_token_format(self, token: str) -> bool:
        if not token:
            return False
        parts = token.split(':')
        if len(parts) != 2:
            return False
        try:
            int(parts[0])
            return len(parts[1]) >= 30
        except ValueError:
            return False
    
    async def start_bot(self, bot_id: int) -> Dict[str, Any]:
        if bot_id not in self._bots:
            return {"success": False, "message": "Bot tidak ditemukan"}
        
        instance = self._bots[bot_id]
        
        if bot_id in self._running_clients and instance.is_running:
            return {
                "success": True,
                "status": "RUNNING",
                "message": f"Bot '{instance.name}' sudah berjalan"
            }
        
        is_valid, bot_info = await self._verify_token_online(instance.token)
        if not is_valid:
            instance.status = "offline"
            instance.is_running = False
            await self._update_bot_status(bot_id, "offline")
            return {
                "success": False,
                "status": "OFFLINE",
                "message": f"Token tidak valid: {bot_info.get('error', 'Unknown error')}"
            }
        
        try:
            if bot_id in self._running_clients:
                try:
                    await self._running_clients[bot_id].stop()
                except:
                    pass
                del self._running_clients[bot_id]
            
            client = Client(
                name=f"managed_bot_{bot_id}",
                api_id=self._api_id,
                api_hash=self._api_hash,
                bot_token=instance.token,
                in_memory=True,
                workdir="."
            )
            
            start_handler, message_handler = self._create_bot_handlers(instance)
            
            client.add_handler(MessageHandler(start_handler, filters.command("start") & filters.private))
            client.add_handler(MessageHandler(message_handler, filters.private & ~filters.command("start")))
            
            await client.start()
            
            me = await client.get_me()
            instance.bot_username = me.username
            instance.bot_telegram_id = me.id
            
            self._running_clients[bot_id] = client
            instance.client = client
            instance.status = "running"
            instance.is_running = True
            instance.started_at = datetime.now()
            
            await self._update_bot_status(bot_id, "running", {
                "username": me.username,
                "id": me.id
            })
            
            logger.info(f"Bot STARTED and RUNNING: {instance.name} (@{me.username})")
            
            return {
                "success": True,
                "status": "RUNNING",
                "username": me.username,
                "message": f"Bot '{instance.name}' berhasil dijalankan!\n@{me.username} sekarang ONLINE ✅"
            }
            
        except Exception as e:
            instance.status = "error"
            instance.is_running = False
            instance.error_count += 1
            logger.error(f"Failed to start bot {bot_id}: {e}")
            await self._update_bot_status(bot_id, "error")
            
            return {
                "success": False,
                "status": "ERROR",
                "message": f"Gagal menjalankan bot: {str(e)}"
            }
    
    async def stop_bot(self, bot_id: int) -> Dict[str, Any]:
        if bot_id not in self._bots:
            return {"success": False, "message": "Bot tidak ditemukan"}
        
        instance = self._bots[bot_id]
        
        try:
            if bot_id in self._running_clients:
                try:
                    await self._running_clients[bot_id].stop()
                except Exception as e:
                    logger.warning(f"Error stopping client: {e}")
                del self._running_clients[bot_id]
            
            instance.client = None
            instance.status = "stopped"
            instance.is_running = False
            
            await self._update_bot_status(bot_id, "stopped")
            
            logger.info(f"Bot stopped: {instance.name} (ID: {bot_id})")
            
            return {
                "success": True,
                "message": f"Bot '{instance.name}' (@{instance.bot_username}) berhasil dihentikan"
            }
            
        except Exception as e:
            logger.error(f"Failed to stop bot {bot_id}: {e}")
            return {"success": False, "message": f"Gagal menghentikan bot: {str(e)}"}
    
    async def restart_bot(self, bot_id: int) -> Dict[str, Any]:
        stop_result = await self.stop_bot(bot_id)
        if not stop_result.get('success') and "tidak ditemukan" in stop_result.get('message', ''):
            return stop_result
        
        await asyncio.sleep(1)
        
        return await self.start_bot(bot_id)
    
    async def delete_bot(self, bot_id: int) -> Dict[str, Any]:
        if bot_id not in self._bots:
            return {"success": False, "message": "Bot tidak ditemukan"}
        
        instance = self._bots[bot_id]
        
        await self.stop_bot(bot_id)
        
        try:
            conn = await self._db.connect()
            await conn.execute("DELETE FROM multi_bot WHERE id = ?", (bot_id,))
            await conn.commit()
            
            del self._bots[bot_id]
            
            logger.info(f"Bot deleted: {instance.name} (ID: {bot_id})")
            
            return {
                "success": True,
                "message": f"Bot '{instance.name}' (@{instance.bot_username}) berhasil dihapus"
            }
            
        except Exception as e:
            logger.error(f"Failed to delete bot {bot_id}: {e}")
            return {"success": False, "message": f"Gagal menghapus bot: {str(e)}"}
    
    async def _update_bot_status(self, bot_id: int, status: str, bot_info: dict = None):
        conn = await self._db.connect()
        
        if bot_info:
            await conn.execute("""
                UPDATE multi_bot 
                SET status = ?, last_check = CURRENT_TIMESTAMP, bot_username = ?, bot_telegram_id = ?
                WHERE id = ?
            """, (status, bot_info.get('username'), bot_info.get('id'), bot_id))
        else:
            await conn.execute("""
                UPDATE multi_bot SET status = ?, last_check = CURRENT_TIMESTAMP WHERE id = ?
            """, (status, bot_id))
        
        await conn.commit()
    
    async def check_all_bots_status(self) -> Dict[str, Any]:
        results = []
        for bot_id, instance in self._bots.items():
            is_running = bot_id in self._running_clients and instance.is_running
            
            if is_running:
                try:
                    client = self._running_clients[bot_id]
                    me = await client.get_me()
                    instance.status = "running"
                    instance.bot_username = me.username
                except:
                    instance.status = "error"
                    instance.is_running = False
            else:
                is_valid, bot_info = await self._verify_token_online(instance.token)
                if is_valid:
                    instance.status = "stopped"
                    instance.bot_username = bot_info.get('username')
                else:
                    instance.status = "offline"
            
            results.append({
                "bot_id": bot_id,
                "name": instance.name,
                "status": instance.status,
                "is_running": instance.is_running,
                "username": instance.bot_username
            })
        
        running_count = sum(1 for r in results if r['status'] == 'running')
        stopped_count = sum(1 for r in results if r['status'] == 'stopped')
        offline_count = sum(1 for r in results if r['status'] in ['offline', 'error'])
        
        return {
            "success": True,
            "bots": results,
            "total": len(results),
            "running": running_count,
            "stopped": stopped_count,
            "offline": offline_count
        }
    
    async def get_all_bots(self) -> List[Dict[str, Any]]:
        bots = []
        for bot_id, instance in self._bots.items():
            bot_dict = instance.to_dict()
            bot_dict['is_running'] = bot_id in self._running_clients and instance.is_running
            bots.append(bot_dict)
        return bots
    
    async def get_bot(self, bot_id: int) -> Optional[Dict[str, Any]]:
        if bot_id in self._bots:
            bot_dict = self._bots[bot_id].to_dict()
            bot_dict['is_running'] = bot_id in self._running_clients
            return bot_dict
        return None
    
    async def get_bot_stats(self, bot_id: int) -> Dict[str, Any]:
        if bot_id not in self._bots:
            return {"success": False, "message": "Bot tidak ditemukan"}
        
        instance = self._bots[bot_id]
        is_running = bot_id in self._running_clients and instance.is_running
        
        uptime = None
        if instance.started_at and is_running:
            uptime = (datetime.now() - instance.started_at).total_seconds()
        
        return {
            "success": True,
            "stats": {
                "name": instance.name,
                "status": instance.status,
                "is_running": is_running,
                "username": instance.bot_username,
                "telegram_id": instance.bot_telegram_id,
                "uptime_seconds": uptime,
                "user_count": instance.user_count,
                "message_count": instance.message_count,
                "error_count": instance.error_count,
                "started_at": instance.started_at.isoformat() if instance.started_at else None
            }
        }
    
    async def record_bot_activity(self, bot_id: int, activity_type: str = "message"):
        if bot_id in self._bots:
            instance = self._bots[bot_id]
            instance.last_activity = datetime.now()
            
            if activity_type == "message":
                instance.message_count += 1
            elif activity_type == "user":
                instance.user_count += 1
            elif activity_type == "error":
                instance.error_count += 1
    
    async def get_summary(self) -> Dict[str, Any]:
        running_count = 0
        stopped_count = 0
        error_count = 0
        
        for bot_id, instance in self._bots.items():
            is_running = bot_id in self._running_clients and instance.is_running
            if is_running:
                running_count += 1
            elif instance.status == "error":
                error_count += 1
            else:
                stopped_count += 1
        
        total_users = sum(b.user_count for b in self._bots.values())
        total_messages = sum(b.message_count for b in self._bots.values())
        
        return {
            "total_bots": len(self._bots),
            "running": running_count,
            "stopped": stopped_count,
            "error": error_count,
            "total_users": total_users,
            "total_messages": total_messages
        }
    
    async def shutdown_all(self):
        for bot_id in list(self._running_clients.keys()):
            try:
                await self.stop_bot(bot_id)
            except Exception as e:
                logger.error(f"Error stopping bot {bot_id} during shutdown: {e}")
        
        logger.info("All managed bots stopped")


bot_manager = BotManager()
