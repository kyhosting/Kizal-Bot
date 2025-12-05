import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
from core.database import db
from config import is_owner

ROLE_LIMITS = {
    "reguler": 15,
    "vip": 30,
    "vvip": 99999,
    "owner": 99999
}


class LimitManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._reset_task = None
        self._initialized = True
    
    def get_limit_for_role(self, role: str) -> int:
        return ROLE_LIMITS.get(role.lower(), 15)
    
    async def check_limit(self, user_id: int) -> Tuple[bool, Dict[str, Any]]:
        if is_owner(user_id):
            return True, {
                "can_proceed": True,
                "remaining": 99999,
                "used": 0,
                "limit": 99999,
                "role": "owner",
                "message": None,
                "warning_level": None
            }
        
        user = await db.get_user(user_id)
        if not user:
            user = await db.create_or_update_user(user_id)
        
        role = user.get("role", "reguler").lower()
        
        if role in ["vip", "vvip", "owner"]:
            return True, {
                "can_proceed": True,
                "remaining": 99999,
                "used": user.get("daily_used", 0),
                "limit": 99999,
                "role": role,
                "message": None,
                "warning_level": None
            }
        
        today = datetime.now().strftime("%Y-%m-%d")
        daily_used = user.get("daily_used", 0)
        daily_limit = self.get_limit_for_role(role)
        
        if user.get("last_reset_date") != today:
            daily_used = 0
            await self._reset_user_limit(user_id, today)
        
        remaining = max(0, daily_limit - daily_used)
        
        result = {
            "can_proceed": remaining > 0,
            "remaining": remaining,
            "used": daily_used,
            "limit": daily_limit,
            "role": role,
            "message": None,
            "warning_level": None
        }
        
        if remaining == 0:
            reset_time = self._get_time_until_reset()
            result["message"] = self._get_limit_exhausted_message(reset_time)
            result["warning_level"] = "exhausted"
        elif remaining <= 3:
            reset_time = self._get_time_until_reset()
            result["message"] = self._get_low_limit_warning(remaining, reset_time)
            result["warning_level"] = "low"
        elif remaining <= 7:
            result["message"] = self._get_usage_tip_message(daily_used, daily_limit)
            result["warning_level"] = "moderate"
        
        return result["can_proceed"], result
    
    async def use_operation(self, user_id: int, operation_name: str = None) -> Tuple[bool, Dict[str, Any]]:
        can_proceed, status = await self.check_limit(user_id)
        
        if not can_proceed:
            return False, status
        
        if status["role"] not in ["vip", "vvip", "owner"]:
            await db.increment_operation(user_id)
            status["remaining"] -= 1
            status["used"] += 1
            
            if operation_name:
                await self._log_operation(user_id, operation_name)
        else:
            await db.increment_operation(user_id)
            if operation_name:
                await self._log_operation(user_id, operation_name)
        
        if status["remaining"] <= 3 and status["remaining"] > 0:
            reset_time = self._get_time_until_reset()
            status["message"] = self._get_low_limit_warning(status["remaining"], reset_time)
            status["warning_level"] = "low"
        elif status["remaining"] == 0:
            reset_time = self._get_time_until_reset()
            status["message"] = self._get_limit_exhausted_message(reset_time)
            status["warning_level"] = "exhausted"
        
        return True, status
    
    async def _reset_user_limit(self, user_id: int, today: str):
        conn = await db.connect()
        await conn.execute("""
            UPDATE users SET daily_used = 0, last_reset_date = ?
            WHERE telegram_id = ?
        """, (today, user_id))
        await conn.commit()
    
    async def reset_all_daily_limits(self):
        today = datetime.now().strftime("%Y-%m-%d")
        conn = await db.connect()
        await conn.execute("""
            UPDATE users SET daily_used = 0, last_reset_date = ?
            WHERE last_reset_date != ? OR last_reset_date IS NULL
        """, (today, today))
        await conn.commit()
    
    async def _log_operation(self, user_id: int, operation_name: str):
        await db.log_action(user_id, f"operation_{operation_name}", {
            "timestamp": datetime.now().isoformat(),
            "operation": operation_name
        })
    
    def _get_time_until_reset(self) -> str:
        now = datetime.now()
        tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        diff = tomorrow - now
        
        hours = int(diff.total_seconds() // 3600)
        minutes = int((diff.total_seconds() % 3600) // 60)
        
        if hours > 0:
            return f"{hours} jam {minutes} menit"
        return f"{minutes} menit"
    
    def _get_limit_exhausted_message(self, reset_time: str) -> str:
        return f"""```
⏰ LIMIT HARIAN TELAH HABIS ⏰
───────────────────────────────────────

Kamu sudah menggunakan 15 operasi hari ini.

🔄 Limit akan reset otomatis dalam {reset_time}.

───────────────────────────────────────
🚀 AKSES UNLIMITED SEKARANG!
───────────────────────────────────────

Upgrade ke VVIP untuk:
• No limits - gunakan sepuasnya
• Priority support
• Semua fitur terbuka

👉 Gunakan "🎁 Redeem Code" atau hubungi admin!
───────────────────────────────────────
```"""
    
    def _get_low_limit_warning(self, remaining: int, reset_time: str) -> str:
        return f"""```
✨ Perhatian! ✨
───────────────────────────────────────

Kamu punya {remaining} operasi tersisa hari ini.

Jangan khawatir! Limit akan reset otomatis 
dalam {reset_time}.

───────────────────────────────────────
💡 Ingin akses tanpa limit?
───────────────────────────────────────

Upgrade ke VVIP untuk:
• Unlimited operations 24/7
• Priority processing
• Semua fitur premium

Ketik "🎁 Redeem Code" untuk upgrade!
───────────────────────────────────────
```"""
    
    def _get_usage_tip_message(self, used: int, limit: int) -> str:
        return f"""```
💡 Tips untuk kamu! 💡
───────────────────────────────────────

Kamu sudah menggunakan {used}/{limit} operasi hari ini.

⚡ Level up pengalamanmu!
───────────────────────────────────────

Upgrade ke VVIP dapatkan:
• Unlimited operations
• Faster processing
• All premium features

🎁 Gunakan "Redeem Code" untuk upgrade mudah!
───────────────────────────────────────
```"""
    
    def get_limit_reset_notification(self) -> str:
        return """```
🔄 LIMIT TELAH DIRESET! 🔄
───────────────────────────────────────

Selamat! Limit harian kamu sudah direset.

🎯 15 operasi tersedia untuk digunakan hari ini.

───────────────────────────────────────
💎 Ingat: Upgrade ke VVIP untuk akses tanpa batas!
───────────────────────────────────────
```"""
    
    def get_progress_bar(self, used: int, limit: int) -> str:
        if limit >= 99999:
            return "████████████████████ ∞"
        
        percentage = min(100, (used / limit) * 100)
        filled = int(percentage / 5)
        empty = 20 - filled
        
        bar = "█" * filled + "░" * empty
        return f"{bar} {used}/{limit}"
    
    async def get_user_limit_status(self, user_id: int) -> str:
        _, status = await self.check_limit(user_id)
        
        role = status["role"].upper()
        
        if role in ["VIP", "VVIP", "OWNER"]:
            return f"""```
📊 LIMIT STATUS
───────────────────────────────────────
Role      : {role}
Status    : UNLIMITED ∞
───────────────────────────────────────
```"""
        
        progress_bar = self.get_progress_bar(status["used"], status["limit"])
        
        return f"""```
📊 LIMIT STATUS
───────────────────────────────────────
Role      : {role}
Terpakai  : {status["used"]}/{status["limit"]}
Sisa      : {status["remaining"]}
Progress  : {progress_bar}
───────────────────────────────────────
```"""
    
    async def start_auto_reset_task(self):
        if self._reset_task is not None:
            return
        
        self._reset_task = asyncio.create_task(self._auto_reset_loop())
    
    async def _auto_reset_loop(self):
        while True:
            now = datetime.now()
            tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            sleep_seconds = (tomorrow - now).total_seconds()
            
            await asyncio.sleep(sleep_seconds)
            await self.reset_all_daily_limits()
    
    async def stop_auto_reset_task(self):
        if self._reset_task:
            self._reset_task.cancel()
            self._reset_task = None


limit_manager = LimitManager()
