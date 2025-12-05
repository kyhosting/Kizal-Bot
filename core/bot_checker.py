import re
import aiohttp
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from core.database import db


class BotChecker:
    _instance = None
    _cache = {}
    _cache_timeout = 300
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        self.api_base = "https://api.telegram.org"
    
    def validate_token_format(self, token: str) -> Tuple[bool, str]:
        if not token:
            return False, "Token tidak boleh kosong"
        
        pattern = r'^[0-9]{8,10}:[a-zA-Z0-9_-]{35}$'
        if not re.match(pattern, token):
            return False, "Format token tidak valid. Format: XXXXXXXXXX:XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
        
        return True, "Format token valid"
    
    async def check_by_token(self, token: str) -> Dict[str, Any]:
        is_valid, message = self.validate_token_format(token)
        if not is_valid:
            return {
                "success": False,
                "error": message
            }
        
        cache_key = f"token_{token[:15]}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_base}/bot{token}/getMe",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    data = await response.json()
                    
                    if not data.get("ok"):
                        return {
                            "success": False,
                            "error": data.get("description", "Token tidak valid atau bot tidak ditemukan")
                        }
                    
                    bot_info = data.get("result", {})
                    
                    result = {
                        "success": True,
                        "bot_id": bot_info.get("id"),
                        "username": bot_info.get("username"),
                        "first_name": bot_info.get("first_name"),
                        "can_join_groups": bot_info.get("can_join_groups", False),
                        "can_read_all_group_messages": bot_info.get("can_read_all_group_messages", False),
                        "supports_inline_queries": bot_info.get("supports_inline_queries", False),
                        "is_bot": bot_info.get("is_bot", True),
                        "link": f"t.me/{bot_info.get('username')}" if bot_info.get('username') else None,
                        "checked_at": datetime.now().isoformat()
                    }
                    
                    webhook_info = await self._check_webhook(token)
                    result["webhook"] = webhook_info
                    
                    self._set_cache(cache_key, result)
                    
                    return result
                    
        except asyncio.TimeoutError:
            return {
                "success": False,
                "error": "Timeout: Server tidak merespons"
            }
        except aiohttp.ClientError as e:
            return {
                "success": False,
                "error": f"Network error: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error: {str(e)}"
            }
    
    async def check_by_username(self, username: str) -> Dict[str, Any]:
        username = username.lstrip('@').lower()
        
        if not username:
            return {
                "success": False,
                "error": "Username tidak boleh kosong"
            }
        
        if not username.endswith('bot'):
            return {
                "success": False,
                "error": "Username bot harus diakhiri dengan 'bot'"
            }
        
        cache_key = f"username_{username}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        result = {
            "success": True,
            "username": f"@{username}",
            "link": f"t.me/{username}",
            "note": "Untuk info lengkap (ID, capabilities), gunakan token bot",
            "checked_at": datetime.now().isoformat()
        }
        
        self._set_cache(cache_key, result)
        
        return result
    
    async def _check_webhook(self, token: str) -> Dict[str, Any]:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_base}/bot{token}/getWebhookInfo",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    data = await response.json()
                    
                    if data.get("ok"):
                        webhook_info = data.get("result", {})
                        return {
                            "set": bool(webhook_info.get("url")),
                            "url": webhook_info.get("url", ""),
                            "pending_update_count": webhook_info.get("pending_update_count", 0),
                            "has_custom_certificate": webhook_info.get("has_custom_certificate", False)
                        }
        except:
            pass
        
        return {"set": False, "error": "Could not check webhook"}
    
    async def save_checked_bot(self, user_id: int, bot_info: Dict[str, Any]) -> bool:
        try:
            conn = await db.connect()
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS checked_bots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    bot_id INTEGER,
                    username TEXT,
                    first_name TEXT,
                    capabilities TEXT,
                    checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, bot_id)
                )
            """)
            
            import json
            capabilities = json.dumps({
                "can_join_groups": bot_info.get("can_join_groups", False),
                "can_read_all_group_messages": bot_info.get("can_read_all_group_messages", False),
                "supports_inline_queries": bot_info.get("supports_inline_queries", False)
            })
            
            await conn.execute("""
                INSERT OR REPLACE INTO checked_bots 
                (user_id, bot_id, username, first_name, capabilities, checked_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                user_id,
                bot_info.get("bot_id"),
                bot_info.get("username"),
                bot_info.get("first_name"),
                capabilities
            ))
            
            await conn.commit()
            return True
            
        except Exception as e:
            return False
    
    async def get_check_history(self, user_id: int, limit: int = 10) -> list:
        try:
            conn = await db.connect()
            
            cursor = await conn.execute("""
                SELECT * FROM checked_bots 
                WHERE user_id = ? 
                ORDER BY checked_at DESC 
                LIMIT ?
            """, (user_id, limit))
            
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
            
        except:
            return []
    
    def _get_cached(self, key: str) -> Optional[Dict[str, Any]]:
        if key in self._cache:
            cached_data, cached_time = self._cache[key]
            if (datetime.now() - cached_time).total_seconds() < self._cache_timeout:
                cached_data["from_cache"] = True
                return cached_data
            else:
                del self._cache[key]
        return None
    
    def _set_cache(self, key: str, data: Dict[str, Any]):
        self._cache[key] = (data.copy(), datetime.now())
        
        if len(self._cache) > 100:
            oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k][1])
            del self._cache[oldest_key]
    
    def format_bot_info(self, bot_info: Dict[str, Any]) -> str:
        if not bot_info.get("success"):
            return f"""```
❌ ERROR
───────────────────────────────────────
{bot_info.get('error', 'Unknown error')}
───────────────────────────────────────
```"""
        
        webhook_status = "❌ Not Set"
        if bot_info.get("webhook", {}).get("set"):
            webhook_status = "✅ Set"
        
        can_join = "✅ Yes" if bot_info.get("can_join_groups") else "❌ No"
        can_read = "✅ Yes" if bot_info.get("can_read_all_group_messages") else "❌ No"
        inline = "✅ Yes" if bot_info.get("supports_inline_queries") else "❌ No"
        
        from_cache = " (cached)" if bot_info.get("from_cache") else ""
        
        return f"""```
✅ BOT INFORMATION{from_cache}
───────────────────────────────────────

🆔 Bot ID     : {bot_info.get('bot_id', 'N/A')}
👤 Username   : @{bot_info.get('username', 'N/A')}
📛 Name       : {bot_info.get('first_name', 'N/A')}
🔗 Link       : {bot_info.get('link', 'N/A')}

───────────────────────────────────────
📊 CAPABILITIES
───────────────────────────────────────
• Can Join Groups    : {can_join}
• Can Read Messages  : {can_read}
• Inline Queries     : {inline}
• Webhook            : {webhook_status}

───────────────────────────────────────
⏰ Checked: {bot_info.get('checked_at', 'Just now')}
───────────────────────────────────────
```"""


bot_checker = BotChecker()
