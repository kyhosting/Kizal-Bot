import aiosqlite
import json
import os
from datetime import datetime
from typing import Optional, Dict, Any, List

DATABASE_PATH = "db/data.db"


class Database:
    _instance = None
    _connection = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def connect(self):
        if self._connection is None:
            os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
            self._connection = await aiosqlite.connect(DATABASE_PATH)
            self._connection.row_factory = aiosqlite.Row
            await self._create_tables()
        return self._connection

    async def _create_tables(self):
        await self._connection.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                role TEXT DEFAULT 'reguler' CHECK (role IN ('reguler', 'vip', 'vvip', 'owner')),
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expired_at TIMESTAMP NULL,
                joined_group INTEGER DEFAULT 0 CHECK (joined_group IN (0, 1)),
                status TEXT DEFAULT 'active' CHECK (status IN ('active', 'banned', 'pending')),
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                operation_count INTEGER DEFAULT 0,
                daily_limit INTEGER DEFAULT 15,
                daily_used INTEGER DEFAULT 0,
                last_reset_date TEXT
            );
            
            CREATE TABLE IF NOT EXISTS user_operations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                operation_type TEXT,
                operation_name TEXT,
                success INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                details TEXT,
                FOREIGN KEY (user_id) REFERENCES users(telegram_id)
            );
            
            CREATE INDEX IF NOT EXISTS idx_user_operations_user ON user_operations(user_id);
            CREATE INDEX IF NOT EXISTS idx_user_operations_date ON user_operations(created_at);

            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT,
                details TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS redeem_codes (
                code TEXT PRIMARY KEY,
                role TEXT CHECK (role IN ('vip', 'vvip')),
                days INTEGER,
                max_use INTEGER DEFAULT 1,
                used_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expire_at TIMESTAMP,
                created_by INTEGER
            );

            CREATE TABLE IF NOT EXISTS user_sessions (
                user_id INTEGER PRIMARY KEY,
                mode TEXT,
                step INTEGER DEFAULT 0,
                data TEXT,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS config (
                key TEXT PRIMARY KEY,
                value TEXT
            );

            CREATE TABLE IF NOT EXISTS multi_bot (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                token TEXT UNIQUE NOT NULL,
                name TEXT,
                status TEXT DEFAULT 'offline',
                added_by INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_check DATETIME,
                bot_username TEXT,
                bot_telegram_id INTEGER
            );

            CREATE TABLE IF NOT EXISTS user_verifications (
                user_id INTEGER PRIMARY KEY,
                joined_group1 INTEGER DEFAULT 0,
                joined_group2 INTEGER DEFAULT 0,
                status TEXT DEFAULT 'pending',
                verified_at TIMESTAMP,
                last_check TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        await self._connection.commit()

    async def close(self):
        if self._connection:
            await self._connection.close()
            self._connection = None

    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        conn = await self.connect()
        cursor = await conn.execute(
            "SELECT * FROM users WHERE telegram_id = ?", (user_id,)
        )
        row = await cursor.fetchone()
        if row:
            return dict(row)
        return None

    async def create_or_update_user(
        self,
        user_id: int,
        username: str = None,
        first_name: str = None,
        last_name: str = None
    ) -> Dict[str, Any]:
        conn = await self.connect()
        existing = await self.get_user(user_id)
        
        if existing:
            await conn.execute("""
                UPDATE users SET 
                    username = COALESCE(?, username),
                    first_name = COALESCE(?, first_name),
                    last_name = COALESCE(?, last_name),
                    last_activity = CURRENT_TIMESTAMP
                WHERE telegram_id = ?
            """, (username, first_name, last_name, user_id))
        else:
            await conn.execute("""
                INSERT INTO users (telegram_id, username, first_name, last_name, daily_limit)
                VALUES (?, ?, ?, ?, 15)
            """, (user_id, username, first_name, last_name))
        
        await conn.commit()
        return await self.get_user(user_id)

    async def update_user_role(
        self,
        user_id: int,
        role: str,
        expired_at: datetime = None
    ):
        conn = await self.connect()
        daily_limit = 15
        if role == 'vip':
            daily_limit = 30
        elif role == 'vvip':
            daily_limit = 99999
        elif role == 'owner':
            daily_limit = 99999
        
        await conn.execute("""
            UPDATE users SET role = ?, expired_at = ?, daily_limit = ?
            WHERE telegram_id = ?
        """, (role, expired_at, daily_limit, user_id))
        await conn.commit()

    async def increment_operation(self, user_id: int):
        conn = await self.connect()
        today = datetime.now().strftime("%Y-%m-%d")
        
        user = await self.get_user(user_id)
        if user:
            if user.get('last_reset_date') != today:
                await conn.execute("""
                    UPDATE users SET daily_used = 1, last_reset_date = ?, operation_count = operation_count + 1
                    WHERE telegram_id = ?
                """, (today, user_id))
            else:
                await conn.execute("""
                    UPDATE users SET daily_used = daily_used + 1, operation_count = operation_count + 1
                    WHERE telegram_id = ?
                """, (user_id,))
            await conn.commit()

    async def check_daily_limit(self, user_id: int) -> tuple:
        user = await self.get_user(user_id)
        if not user:
            return False, "User tidak ditemukan"
        
        today = datetime.now().strftime("%Y-%m-%d")
        daily_used = user.get('daily_used', 0)
        daily_limit = user.get('daily_limit', 10)
        
        if user.get('last_reset_date') != today:
            daily_used = 0
        
        if daily_used >= daily_limit:
            return False, f"Limit harian tercapai ({daily_used}/{daily_limit})"
        
        return True, f"Sisa limit: {daily_limit - daily_used}"

    async def log_action(self, user_id: int, action: str, details: dict = None):
        conn = await self.connect()
        await conn.execute("""
            INSERT INTO logs (user_id, action, details)
            VALUES (?, ?, ?)
        """, (user_id, action, json.dumps(details) if details else None))
        await conn.commit()

    async def save_session(self, user_id: int, mode: str, step: int = 0, data: dict = None):
        conn = await self.connect()
        await conn.execute("""
            INSERT OR REPLACE INTO user_sessions (user_id, mode, step, data, last_activity)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (user_id, mode, step, json.dumps(data) if data else None))
        await conn.commit()

    async def get_session(self, user_id: int) -> Optional[Dict[str, Any]]:
        conn = await self.connect()
        cursor = await conn.execute(
            "SELECT * FROM user_sessions WHERE user_id = ?", (user_id,)
        )
        row = await cursor.fetchone()
        if row:
            result = dict(row)
            if result.get('data'):
                result['data'] = json.loads(result['data'])
            return result
        return None

    async def clear_session(self, user_id: int):
        conn = await self.connect()
        await conn.execute("DELETE FROM user_sessions WHERE user_id = ?", (user_id,))
        await conn.commit()

    async def create_redeem_code(
        self,
        code: str,
        role: str,
        days: int,
        max_use: int = 1,
        expire_at: datetime = None,
        created_by: int = None
    ):
        conn = await self.connect()
        await conn.execute("""
            INSERT INTO redeem_codes (code, role, days, max_use, expire_at, created_by)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (code.upper(), role, days, max_use, expire_at, created_by))
        await conn.commit()

    async def redeem_code(self, code: str, user_id: int) -> Dict[str, Any]:
        conn = await self.connect()
        cursor = await conn.execute(
            "SELECT * FROM redeem_codes WHERE code = ?", (code.upper(),)
        )
        row = await cursor.fetchone()
        
        if not row:
            return {"success": False, "message": "Kode tidak ditemukan"}
        
        redeem = dict(row)
        
        if redeem['used_count'] >= redeem['max_use']:
            return {"success": False, "message": "Kode sudah digunakan"}
        
        if redeem['expire_at']:
            expire_at = datetime.fromisoformat(redeem['expire_at'])
            if datetime.now() > expire_at:
                return {"success": False, "message": "Kode sudah expired"}
        
        from datetime import timedelta
        new_expired = datetime.now() + timedelta(days=redeem['days'])
        
        await self.update_user_role(user_id, redeem['role'], new_expired)
        
        await conn.execute("""
            UPDATE redeem_codes SET used_count = used_count + 1 WHERE code = ?
        """, (code.upper(),))
        await conn.commit()
        
        return {
            "success": True,
            "type": redeem['role'],
            "duration": redeem['days'],
            "message": "Berhasil redeem!"
        }

    async def get_all_users(self) -> List[Dict[str, Any]]:
        conn = await self.connect()
        cursor = await conn.execute("SELECT * FROM users ORDER BY joined_at DESC")
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def get_user_verification(self, user_id: int) -> Optional[Dict[str, Any]]:
        conn = await self.connect()
        cursor = await conn.execute(
            "SELECT * FROM user_verifications WHERE user_id = ?", (user_id,)
        )
        row = await cursor.fetchone()
        if row:
            return dict(row)
        return None

    async def update_verification(
        self,
        user_id: int,
        joined_group1: bool = False,
        joined_group2: bool = False
    ):
        conn = await self.connect()
        status = 'verified' if (joined_group1 and joined_group2) else 'pending'
        verified_at = datetime.now() if status == 'verified' else None
        
        await conn.execute("""
            INSERT OR REPLACE INTO user_verifications 
            (user_id, joined_group1, joined_group2, status, verified_at, last_check)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (user_id, int(joined_group1), int(joined_group2), status, verified_at))
        await conn.commit()

    async def get_expired_users(self) -> List[Dict[str, Any]]:
        conn = await self.connect()
        cursor = await conn.execute("""
            SELECT * FROM users 
            WHERE expired_at IS NOT NULL AND expired_at < CURRENT_TIMESTAMP
            AND role IN ('vip', 'vvip')
        """)
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def reset_expired_users(self):
        conn = await self.connect()
        await conn.execute("""
            UPDATE users SET role = 'reguler', expired_at = NULL, daily_limit = 15
            WHERE expired_at IS NOT NULL AND expired_at < CURRENT_TIMESTAMP
            AND role IN ('vip', 'vvip')
        """)
        await conn.commit()
    
    async def log_operation(self, user_id: int, operation_type: str, operation_name: str, success: bool = True, details: dict = None):
        conn = await self.connect()
        import json
        await conn.execute("""
            INSERT INTO user_operations (user_id, operation_type, operation_name, success, details)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, operation_type, operation_name, 1 if success else 0, json.dumps(details) if details else None))
        await conn.commit()
    
    async def get_user_operations_today(self, user_id: int) -> int:
        conn = await self.connect()
        today = datetime.now().strftime("%Y-%m-%d")
        cursor = await conn.execute("""
            SELECT COUNT(*) as count FROM user_operations 
            WHERE user_id = ? AND DATE(created_at) = ?
        """, (user_id, today))
        result = await cursor.fetchone()
        return result['count'] if result else 0
    
    async def get_limit_stats(self) -> Dict[str, Any]:
        conn = await self.connect()
        today = datetime.now().strftime("%Y-%m-%d")
        
        cursor = await conn.execute("""
            SELECT AVG(daily_used) as avg_usage FROM users WHERE role = 'reguler'
        """)
        avg_result = await cursor.fetchone()
        
        cursor = await conn.execute("""
            SELECT COUNT(*) as count FROM users 
            WHERE role = 'reguler' AND daily_used >= daily_limit AND last_reset_date = ?
        """, (today,))
        exceeded_result = await cursor.fetchone()
        
        return {
            "avg_usage_reguler": avg_result['avg_usage'] or 0,
            "limit_exceeded_count": exceeded_result['count'] if exceeded_result else 0
        }

    async def get_statistics(self) -> Dict[str, Any]:
        conn = await self.connect()
        
        cursor = await conn.execute("SELECT COUNT(*) as count FROM users")
        total_users = (await cursor.fetchone())['count']
        
        cursor = await conn.execute("SELECT COUNT(*) as count FROM users WHERE role = 'vip'")
        vip_count = (await cursor.fetchone())['count']
        
        cursor = await conn.execute("SELECT COUNT(*) as count FROM users WHERE role = 'vvip'")
        vvip_count = (await cursor.fetchone())['count']
        
        cursor = await conn.execute("SELECT SUM(operation_count) as total FROM users")
        total_ops = (await cursor.fetchone())['total'] or 0
        
        return {
            "total_users": total_users,
            "vip_count": vip_count,
            "vvip_count": vvip_count,
            "total_operations": total_ops
        }


db = Database()
