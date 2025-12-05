import asyncio
import logging
import os
import glob
from datetime import datetime, timedelta

logger = logging.getLogger("bot")


class BackgroundTasks:
    def __init__(self, client):
        self.client = client
        self.running = False

    async def start(self):
        self.running = True
        asyncio.create_task(self._expired_checker())
        asyncio.create_task(self._temp_cleanup())
        asyncio.create_task(self._session_cleanup())
        asyncio.create_task(self._health_check())
        asyncio.create_task(self._daily_reset())
        logger.info("Background tasks started")

    async def stop(self):
        self.running = False

    async def _expired_checker(self):
        from core.database import db
        
        while self.running:
            try:
                expired_users = await db.get_expired_users()
                
                if expired_users:
                    for user in expired_users:
                        try:
                            await self.client.send_message(
                                user['telegram_id'],
                                "```\n⚠️ NOTIFIKASI\n───────────────────────────────────────\n\nMasa aktif VIP/VVIP Anda telah berakhir.\n\nGunakan kode redeem atau hubungi admin\nuntuk memperpanjang akses.\n\n───────────────────────────────────────\n```"
                            )
                        except Exception as e:
                            logger.debug(f"Could not notify user {user['telegram_id']}: {e}")
                
                await db.reset_expired_users()
                logger.debug("Checked and reset expired users")
            except Exception as e:
                logger.error(f"Error in expired checker: {e}")
            
            await asyncio.sleep(3600)

    async def _temp_cleanup(self):
        while self.running:
            try:
                temp_files = glob.glob("tmp/*") + glob.glob("temp_*")
                now = datetime.now()
                deleted_count = 0
                
                for filepath in temp_files:
                    try:
                        if os.path.isfile(filepath):
                            mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
                            if now - mtime > timedelta(hours=1):
                                os.remove(filepath)
                                deleted_count += 1
                                logger.debug(f"Removed old temp file: {filepath}")
                    except Exception as e:
                        logger.error(f"Error removing temp file {filepath}: {e}")
                
                if deleted_count > 0:
                    logger.info(f"Cleaned up {deleted_count} temp files")
                
            except Exception as e:
                logger.error(f"Error in temp cleanup: {e}")
            
            await asyncio.sleep(1800)

    async def _session_cleanup(self):
        from core.database import db
        
        while self.running:
            try:
                conn = await db.connect()
                cutoff = datetime.now() - timedelta(hours=24)
                result = await conn.execute(
                    "DELETE FROM user_sessions WHERE last_activity < ?",
                    (cutoff,)
                )
                await conn.commit()
                logger.debug("Cleaned up old sessions")
            except Exception as e:
                logger.error(f"Error in session cleanup: {e}")
            
            await asyncio.sleep(3600)

    async def _health_check(self):
        from core.monitoring import bot_monitor
        
        while self.running:
            try:
                health = await bot_monitor.check_health()
                
                if health["status"] != "healthy":
                    logger.warning(f"Health check failed: {health}")
                
            except Exception as e:
                logger.error(f"Error in health check: {e}")
            
            await asyncio.sleep(300)

    async def _daily_reset(self):
        from core.database import db
        
        while self.running:
            try:
                now = datetime.now()
                
                if now.hour == 0 and now.minute < 5:
                    conn = await db.connect()
                    await conn.execute(
                        "UPDATE users SET daily_used = 0 WHERE daily_used > 0"
                    )
                    await conn.commit()
                    logger.info("Daily limit reset completed")
                    
                    await asyncio.sleep(300)
                
            except Exception as e:
                logger.error(f"Error in daily reset: {e}")
            
            await asyncio.sleep(60)

    async def restart(self):
        await self.stop()
        await asyncio.sleep(1)
        await self.start()
        logger.info("Background tasks restarted")
