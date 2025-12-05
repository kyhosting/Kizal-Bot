import os
import time
import asyncio
import logging
import psutil
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from collections import defaultdict

logger = logging.getLogger("bot")


class BotMonitor:
    _instance = None
    _metrics = None
    _alerts = None
    _response_times = None
    _error_counts = None
    _start_time = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._metrics = defaultdict(list)
            cls._alerts = []
            cls._response_times = []
            cls._error_counts = defaultdict(int)
            cls._start_time = datetime.now()
        return cls._instance
    
    async def get_system_metrics(self) -> Dict[str, Any]:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        uptime = datetime.now() - self._start_time
        uptime_str = f"{uptime.days}d {uptime.seconds // 3600}h {(uptime.seconds % 3600) // 60}m"
        
        return {
            "cpu_percent": cpu_percent,
            "memory_used_mb": memory.used / (1024 * 1024),
            "memory_total_mb": memory.total / (1024 * 1024),
            "memory_percent": memory.percent,
            "disk_used_gb": disk.used / (1024 * 1024 * 1024),
            "disk_total_gb": disk.total / (1024 * 1024 * 1024),
            "disk_percent": disk.percent,
            "uptime": uptime_str,
            "uptime_seconds": uptime.total_seconds()
        }
    
    async def get_bot_statistics(self) -> Dict[str, Any]:
        from core.database import db
        
        stats = await db.get_statistics()
        
        conn = await db.connect()
        today = datetime.now().strftime("%Y-%m-%d")
        cursor = await conn.execute(
            "SELECT COUNT(DISTINCT user_id) as count FROM logs WHERE DATE(timestamp) = ?",
            (today,)
        )
        result = await cursor.fetchone()
        active_today = result['count'] if result else 0
        
        stats['active_today'] = active_today
        
        return stats
    
    def record_response_time(self, command: str, response_time_ms: float):
        self._response_times.append({
            "command": command,
            "time_ms": response_time_ms,
            "timestamp": datetime.now()
        })
        
        if len(self._response_times) > 1000:
            self._response_times = self._response_times[-500:]
    
    def record_error(self, error_type: str, details: str = ""):
        self._error_counts[error_type] += 1
        logger.error(f"Error recorded: {error_type} - {details}")
    
    def add_alert(self, level: str, message: str, source: str = "system"):
        alert = {
            "level": level,
            "message": message,
            "source": source,
            "timestamp": datetime.now(),
            "acknowledged": False
        }
        self._alerts.append(alert)
        
        if len(self._alerts) > 100:
            self._alerts = self._alerts[-50:]
        
        logger.warning(f"Alert [{level}]: {message}")
    
    def get_alerts(self, include_acknowledged: bool = False) -> List[Dict[str, Any]]:
        if include_acknowledged:
            return self._alerts
        return [a for a in self._alerts if not a.get("acknowledged")]
    
    def acknowledge_alert(self, index: int) -> bool:
        if 0 <= index < len(self._alerts):
            self._alerts[index]["acknowledged"] = True
            return True
        return False
    
    def get_average_response_time(self, minutes: int = 60) -> float:
        cutoff = datetime.now() - timedelta(minutes=minutes)
        recent = [r for r in self._response_times if r["timestamp"] > cutoff]
        
        if not recent:
            return 0.0
        
        return sum(r["time_ms"] for r in recent) / len(recent)
    
    def get_error_rate(self, minutes: int = 60) -> Dict[str, int]:
        return dict(self._error_counts)
    
    def get_response_time_stats(self) -> Dict[str, Any]:
        if not self._response_times:
            return {
                "avg_ms": 0,
                "min_ms": 0,
                "max_ms": 0,
                "count": 0
            }
        
        times = [r["time_ms"] for r in self._response_times]
        return {
            "avg_ms": sum(times) / len(times),
            "min_ms": min(times),
            "max_ms": max(times),
            "count": len(times)
        }
    
    async def check_health(self) -> Dict[str, Any]:
        health = {
            "status": "healthy",
            "checks": {}
        }
        
        metrics = await self.get_system_metrics()
        
        if metrics["cpu_percent"] > 90:
            health["checks"]["cpu"] = {"status": "warning", "value": metrics["cpu_percent"]}
            self.add_alert("warning", f"High CPU usage: {metrics['cpu_percent']}%")
        else:
            health["checks"]["cpu"] = {"status": "ok", "value": metrics["cpu_percent"]}
        
        if metrics["memory_percent"] > 85:
            health["checks"]["memory"] = {"status": "warning", "value": metrics["memory_percent"]}
            self.add_alert("warning", f"High memory usage: {metrics['memory_percent']}%")
        else:
            health["checks"]["memory"] = {"status": "ok", "value": metrics["memory_percent"]}
        
        if metrics["disk_percent"] > 90:
            health["checks"]["disk"] = {"status": "critical", "value": metrics["disk_percent"]}
            self.add_alert("critical", f"Critical disk usage: {metrics['disk_percent']}%")
            health["status"] = "unhealthy"
        else:
            health["checks"]["disk"] = {"status": "ok", "value": metrics["disk_percent"]}
        
        from core.database import db
        try:
            await db.connect()
            health["checks"]["database"] = {"status": "ok"}
        except Exception as e:
            health["checks"]["database"] = {"status": "critical", "error": str(e)}
            health["status"] = "unhealthy"
            self.add_alert("critical", f"Database connection failed: {str(e)}")
        
        avg_response = self.get_average_response_time(10)
        if avg_response > 5000:
            health["checks"]["response_time"] = {"status": "warning", "value": avg_response}
            self.add_alert("warning", f"High average response time: {avg_response:.0f}ms")
        else:
            health["checks"]["response_time"] = {"status": "ok", "value": avg_response}
        
        return health
    
    async def get_logs(self, limit: int = 50, level: str = None) -> List[Dict[str, Any]]:
        from core.database import db
        
        conn = await db.connect()
        
        if level:
            cursor = await conn.execute(
                """SELECT * FROM logs 
                   WHERE details LIKE ? 
                   ORDER BY timestamp DESC LIMIT ?""",
                (f'%"level": "{level}"%', limit)
            )
        else:
            cursor = await conn.execute(
                "SELECT * FROM logs ORDER BY timestamp DESC LIMIT ?",
                (limit,)
            )
        
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    
    def format_metrics_report(self, metrics: Dict[str, Any], stats: Dict[str, Any]) -> str:
        response_stats = self.get_response_time_stats()
        alerts = self.get_alerts()
        
        report = f"""```
📊 BOT METRICS REPORT
═══════════════════════════════════════

🖥️ SYSTEM RESOURCES
───────────────────────────────────────
CPU Usage      : {metrics['cpu_percent']:.1f}%
Memory Usage   : {metrics['memory_percent']:.1f}%
Disk Usage     : {metrics['disk_percent']:.1f}%
Uptime         : {metrics['uptime']}

───────────────────────────────────────
👥 USER STATISTICS
───────────────────────────────────────
Total Users    : {stats['total_users']}
VIP Members    : {stats['vip_count']}
VVIP Members   : {stats['vvip_count']}
Active Today   : {stats.get('active_today', 0)}
Total Ops      : {stats['total_operations']}

───────────────────────────────────────
⚡ PERFORMANCE
───────────────────────────────────────
Avg Response   : {response_stats['avg_ms']:.1f}ms
Min Response   : {response_stats['min_ms']:.1f}ms
Max Response   : {response_stats['max_ms']:.1f}ms
Total Requests : {response_stats['count']}

───────────────────────────────────────
🔔 ALERTS ({len(alerts)} active)
───────────────────────────────────────
"""
        
        if alerts:
            for i, alert in enumerate(alerts[:5]):
                report += f"[{alert['level'].upper()}] {alert['message']}\n"
        else:
            report += "No active alerts\n"
        
        report += "───────────────────────────────────────\n```"
        
        return report


class MetricsCollector:
    def __init__(self, monitor: BotMonitor):
        self.monitor = monitor
        self.running = False
    
    async def start(self):
        self.running = True
        asyncio.create_task(self._collect_loop())
        logger.info("Metrics collector started")
    
    async def stop(self):
        self.running = False
    
    async def _collect_loop(self):
        while self.running:
            try:
                await self.monitor.check_health()
            except Exception as e:
                logger.error(f"Error in metrics collection: {e}")
            
            await asyncio.sleep(60)


class AlertManager:
    def __init__(self, monitor: BotMonitor, client=None):
        self.monitor = monitor
        self.client = client
        self.owner_id = None
        self.running = False
    
    def set_owner(self, owner_id: int):
        self.owner_id = owner_id
    
    def set_client(self, client):
        self.client = client
    
    async def start(self):
        self.running = True
        asyncio.create_task(self._alert_loop())
        logger.info("Alert manager started")
    
    async def stop(self):
        self.running = False
    
    async def _alert_loop(self):
        last_alert_count = 0
        
        while self.running:
            try:
                alerts = self.monitor.get_alerts()
                
                if len(alerts) > last_alert_count and self.client and self.owner_id:
                    new_alerts = alerts[last_alert_count:]
                    for alert in new_alerts:
                        if alert["level"] in ["critical", "error"]:
                            await self._send_alert_notification(alert)
                
                last_alert_count = len(alerts)
                
            except Exception as e:
                logger.error(f"Error in alert loop: {e}")
            
            await asyncio.sleep(30)
    
    async def _send_alert_notification(self, alert: Dict[str, Any]):
        if not self.client or not self.owner_id:
            return
        
        try:
            text = f"""```
🚨 ALERT NOTIFICATION
───────────────────────────────────────
Level   : {alert['level'].upper()}
Source  : {alert['source']}
Time    : {alert['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}

Message:
{alert['message']}
───────────────────────────────────────
```"""
            await self.client.send_message(self.owner_id, text)
        except Exception as e:
            logger.error(f"Failed to send alert notification: {e}")


bot_monitor = BotMonitor()
