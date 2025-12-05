import os
import asyncio
import logging
import aiohttp
from typing import Dict, Any, List, Optional
from datetime import datetime
from pyrogram import Client

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
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "bot_id": self.bot_id,
            "name": self.name,
            "status": self.status,
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
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._bots = {}
            cls._running_clients = {}
        return cls._instance
    
    async def initialize(self):
        from core.database import db
        self._db = db
        await self._ensure_table()
        await self._load_bots_from_db()
        asyncio.create_task(self._auto_start_bots())
        logger.info("BotManager initialized")
    
    async def _ensure_table(self):
        pass
    
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
    
    async def _auto_start_bots(self):
        await asyncio.sleep(2)
        for bot_id, instance in self._bots.items():
            try:
                is_valid, bot_info = await self._verify_token_online(instance.token)
                if is_valid:
                    instance.status = "online"
                    instance.bot_username = bot_info.get('username')
                    instance.bot_telegram_id = bot_info.get('id')
                    await self._update_bot_status(bot_id, "online", bot_info)
                    logger.info(f"Bot {instance.name} is ONLINE (@{instance.bot_username})")
                else:
                    instance.status = "offline"
                    await self._update_bot_status(bot_id, "offline")
                    logger.warning(f"Bot {instance.name} is OFFLINE")
            except Exception as e:
                instance.status = "error"
                instance.error_count += 1
                logger.error(f"Error checking bot {instance.name}: {e}")
    
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
                VALUES (?, ?, 'online', ?, CURRENT_TIMESTAMP, ?, ?)
            """, (token, name, created_by, bot_info.get('username'), bot_info.get('id')))
            await conn.commit()
            
            bot_id = cursor.lastrowid
            
            instance = BotInstance(bot_id=bot_id, name=name, token=token)
            instance.status = "online"
            instance.bot_username = bot_info.get('username')
            instance.bot_telegram_id = bot_info.get('id')
            self._bots[bot_id] = instance
            
            logger.info(f"Bot added: {name} (ID: {bot_id}) - @{bot_info.get('username')}")
            
            return {
                "success": True,
                "bot_id": bot_id,
                "username": bot_info.get('username'),
                "message": f"Bot '{name}' berhasil ditambahkan dan ONLINE!"
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
        
        is_valid, bot_info = await self._verify_token_online(instance.token)
        
        if is_valid:
            instance.status = "online"
            instance.started_at = datetime.now()
            instance.bot_username = bot_info.get('username')
            instance.bot_telegram_id = bot_info.get('id')
            
            await self._update_bot_status(bot_id, "online", bot_info)
            
            logger.info(f"Bot started: {instance.name} (ID: {bot_id}) - ONLINE")
            
            return {
                "success": True,
                "status": "ONLINE",
                "username": bot_info.get('username'),
                "message": f"Bot '{instance.name}' berhasil dijalankan - Status: ONLINE"
            }
        else:
            instance.status = "offline"
            instance.error_count += 1
            await self._update_bot_status(bot_id, "offline")
            
            return {
                "success": False,
                "status": "OFFLINE",
                "message": f"Bot gagal dijalankan: {bot_info.get('error', 'Token tidak valid')}"
            }
    
    async def stop_bot(self, bot_id: int) -> Dict[str, Any]:
        if bot_id not in self._bots:
            return {"success": False, "message": "Bot tidak ditemukan"}
        
        instance = self._bots[bot_id]
        
        try:
            if bot_id in self._running_clients:
                await self._running_clients[bot_id].stop()
                del self._running_clients[bot_id]
            
            instance.status = "offline"
            
            await self._update_bot_status(bot_id, "offline")
            
            logger.info(f"Bot stopped: {instance.name} (ID: {bot_id})")
            
            return {
                "success": True,
                "message": f"Bot '{instance.name}' berhasil dihentikan"
            }
            
        except Exception as e:
            logger.error(f"Failed to stop bot {bot_id}: {e}")
            return {"success": False, "message": f"Gagal menghentikan bot: {str(e)}"}
    
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
                "message": f"Bot '{instance.name}' berhasil dihapus"
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
            is_valid, bot_info = await self._verify_token_online(instance.token)
            
            if is_valid:
                instance.status = "online"
                instance.bot_username = bot_info.get('username')
                instance.bot_telegram_id = bot_info.get('id')
                await self._update_bot_status(bot_id, "online", bot_info)
            else:
                instance.status = "offline"
                await self._update_bot_status(bot_id, "offline")
            
            results.append({
                "bot_id": bot_id,
                "name": instance.name,
                "status": instance.status,
                "username": instance.bot_username
            })
        
        return {
            "success": True,
            "bots": results,
            "total": len(results),
            "online": sum(1 for r in results if r['status'] == 'online'),
            "offline": sum(1 for r in results if r['status'] == 'offline')
        }
    
    async def get_all_bots(self) -> List[Dict[str, Any]]:
        return [instance.to_dict() for instance in self._bots.values()]
    
    async def get_bot(self, bot_id: int) -> Optional[Dict[str, Any]]:
        if bot_id in self._bots:
            return self._bots[bot_id].to_dict()
        return None
    
    async def get_bot_stats(self, bot_id: int) -> Dict[str, Any]:
        if bot_id not in self._bots:
            return {"success": False, "message": "Bot tidak ditemukan"}
        
        instance = self._bots[bot_id]
        
        is_valid, bot_info = await self._verify_token_online(instance.token)
        if is_valid:
            instance.status = "online"
            instance.bot_username = bot_info.get('username')
            instance.bot_telegram_id = bot_info.get('id')
        else:
            instance.status = "offline"
        
        uptime = None
        if instance.started_at and instance.status == "online":
            uptime = (datetime.now() - instance.started_at).total_seconds()
        
        return {
            "success": True,
            "stats": {
                "name": instance.name,
                "status": instance.status,
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
        online_count = 0
        offline_count = 0
        error_count = 0
        
        for instance in self._bots.values():
            if instance.status == "online":
                online_count += 1
            elif instance.status == "error":
                error_count += 1
            else:
                offline_count += 1
        
        total_users = sum(b.user_count for b in self._bots.values())
        total_messages = sum(b.message_count for b in self._bots.values())
        
        return {
            "total_bots": len(self._bots),
            "running": online_count,
            "stopped": offline_count,
            "error": error_count,
            "total_users": total_users,
            "total_messages": total_messages
        }


bot_manager = BotManager()
