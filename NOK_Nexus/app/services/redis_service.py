"""
Redis 服务
用于验证码、Token 黑名单、缓存等
"""
import redis
import json
from typing import Optional, Any, Dict
from datetime import timedelta, datetime
from app.core.config import settings
from loguru import logger


# 开发环境：使用内存存储替代 Redis
class MemoryStorage:
    """内存存储（开发环境使用）"""

    def __init__(self):
        self._data: Dict[str, Dict[str, Any]] = {}

    def setex(self, key: str, expire: timedelta, value: Any):
        expire_at = datetime.utcnow() + expire
        self._data[key] = {"value": value, "expire_at": expire_at}

    def get(self, key: str) -> Optional[Any]:
        if key not in self._data:
            return None
        item = self._data[key]
        if datetime.utcnow() > item["expire_at"]:
            del self._data[key]
            return None
        return item["value"]

    def delete(self, key: str):
        if key in self._data:
            del self._data[key]

    def exists(self, key: str) -> bool:
        if key not in self._data:
            return False
        if datetime.utcnow() > self._data[key]["expire_at"]:
            del self._data[key]
            return False
        return True

    def incr(self, key: str) -> int:
        if key not in self._data:
            self._data[key] = {"value": 1, "expire_at": datetime.utcnow() + timedelta(minutes=15)}
            return 1
        self._data[key]["value"] += 1
        return self._data[key]["value"]


class RedisService:
    """Redis 服务类"""

    def __init__(self):
        # 尝试连接 Redis，失败则使用内存存储
        try:
            self.redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD,
                decode_responses=True,
            )
            # 测试连接
            self.redis_client.ping()
            logger.info("Redis 连接成功")
            self._use_memory = False
        except Exception as e:
            logger.warning(f"Redis 连接失败，使用内存存储：{e}")
            self.redis_client = MemoryStorage()
            self._use_memory = True

    def _get_key(self, key: str) -> str:
        """获取带前缀的 key"""
        return f"nok_ailab:{key}"

    # ==================== 验证码相关 ====================

    def set_verify_code(
        self, type: str, identifier: str, code: str, expire_minutes: int = 10
    ):
        """
        设置验证码
        :param type: verify(验证)/login(登录)/reset(重置密码)
        :param identifier: email 或 phone
        :param code: 验证码
        :param expire_minutes: 过期时间 (分钟)
        """
        key = self._get_key(f"verify_code:{type}:{identifier}")
        self.redis_client.setex(key, timedelta(minutes=expire_minutes), code)
        logger.info(f"验证码已设置：{type}:{identifier} -> {code}")

    def get_verify_code(self, type: str, identifier: str) -> Optional[str]:
        """获取验证码"""
        key = self._get_key(f"verify_code:{type}:{identifier}")
        return self.redis_client.get(key)

    def delete_verify_code(self, type: str, identifier: str):
        """删除验证码"""
        key = self._get_key(f"verify_code:{type}:{identifier}")
        self.redis_client.delete(key)

    # ==================== Token 黑名单相关 ====================

    async def blacklist_token(self, token: str, expire_hours: int = 24):
        """将 Token 加入黑名单 (用户登出时使用)"""
        key = self._get_key(f"token_blacklist:{token}")
        self.redis_client.setex(key, timedelta(hours=expire_hours), "1")

    async def is_token_blacklisted(self, token: str) -> bool:
        """检查 Token 是否在黑名单中"""
        key = self._get_key(f"token_blacklist:{token}")
        return self.redis_client.exists(key) > 0

    # ==================== 通用 KV 操作 ====================

    def set(self, key: str, value: Any, expire_seconds: Optional[int] = None):
        """设置键值对"""
        full_key = self._get_key(key)
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        if expire_seconds:
            self.redis_client.setex(full_key, timedelta(seconds=expire_seconds), value)
        else:
            self.redis_client.set(full_key, value)

    def get(self, key: str, as_json: bool = False) -> Optional[Any]:
        """获取值"""
        full_key = self._get_key(key)
        value = self.redis_client.get(full_key)
        if value is None:
            return None
        if as_json:
            return json.loads(value)
        return value

    def delete(self, key: str):
        """删除键"""
        full_key = self._get_key(key)
        self.redis_client.delete(full_key)

    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        full_key = self._get_key(key)
        return self.redis_client.exists(full_key) > 0

    # ==================== 限流相关 ====================

    def is_rate_limited(
        self, key: str, max_attempts: int = 5, window_minutes: int = 15
    ) -> bool:
        """
        检查是否触发限流
        :param key: 限流 key(如 IP 或用户 ID)
        :param max_attempts: 最大尝试次数
        :param window_minutes: 时间窗口 (分钟)
        :return: 是否被限流
        """
        full_key = self._get_key(f"rate_limit:{key}")
        current = self.redis_client.get(full_key)

        if current is None:
            self.redis_client.setex(full_key, timedelta(minutes=window_minutes), 1)
            return False

        if int(current) >= max_attempts:
            return True

        self.redis_client.incr(full_key)
        return False


# 单例
redis_service = RedisService()
