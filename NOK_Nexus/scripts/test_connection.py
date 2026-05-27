#!/usr/bin/env python3
"""
数据库连接测试脚本
从 .env 文件读取配置

使用方式：
    python scripts/test_connection.py
"""
import sys
import os

# 添加项目路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from app.core.config import settings
from sqlalchemy import text

def test_database_connection():
    """测试数据库连接"""
    print("=" * 60)
    print("数据库连接测试")
    print("=" * 60)

    # 打印配置信息（隐藏密码）
    print(f"\n配置信息:")
    print(f"  DB_HOST: {settings.DB_HOST}")
    print(f"  DB_PORT: {settings.DB_PORT}")
    print(f"  DB_NAME: {settings.DB_NAME}")
    print(f"  DB_USER: {settings.DB_USER}")
    print(f"  DB_PASSWORD: {'*' * len(settings.DB_PASSWORD)}")

    # 测试网络连接
    print(f"\n网络连通性测试...")
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(10)
        result = s.connect_ex((settings.DB_HOST, settings.DB_PORT))
        if result == 0:
            print("  ✓ 网络连通!")
        else:
            print(f"  ✗ 无法连接，错误码：{result}")
            print("\n  可能原因:")
            print("  1. RDS 白名单未配置 (请添加你的公网 IP)")
            print("  2. RDS 只有内网地址 (需申请公网地址)")
            s.close()
            return False
        s.close()
    except Exception as e:
        print(f"  ✗ 网络测试失败：{e}")
        return False

    # 测试数据库连接
    print(f"\n数据库连接测试...")
    try:
        from app.core.database import engine

        with engine.connect() as conn:
            result = conn.execute(text('SELECT version();'))
            version = result.fetchone()[0]
            print("  ✅ RDS PostgreSQL 连接成功!")
            print(f"  PostgreSQL 版本：{version[:60]}...")

        # 检查表是否存在
        print("\n检查数据库表...")
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """))
            tables = [row[0] for row in result.fetchall()]

            if tables:
                print(f"  ✓ 找到 {len(tables)} 张表:")
                for table in tables[:10]:
                    print(f"    - {table}")
                if len(tables) > 10:
                    print(f"    ... 还有 {len(tables) - 10} 张表")
            else:
                print("  ⚠️  数据库为空，需要运行初始化脚本")

        return True

    except Exception as e:
        print(f"  ❌ 数据库连接失败:")
        print(f"  错误：{e}")
        return False


def test_redis_connection():
    """测试 Redis 连接"""
    print("\n" + "=" * 60)
    print("Redis 连接测试")
    print("=" * 60)

    print(f"\n配置信息:")
    print(f"  REDIS_HOST: {settings.REDIS_HOST}")
    print(f"  REDIS_PORT: {settings.REDIS_PORT}")

    try:
        from app.services.redis_service import redis_service

        # 测试连接
        redis_service.redis_client.ping()
        print("  ✅ Redis 连接成功!")

        # 测试读写
        test_key = "test:connection"
        redis_service.set(test_key, "hello", expire_seconds=60)
        value = redis_service.get(test_key)
        print(f"  ✓ 读写测试：set/get = {value}")

        return True

    except Exception as e:
        print(f"  ❌ Redis 连接失败:")
        print(f"  错误：{e}")
        print("\n  解决方案:")
        print("  1. 启动本地 Redis: docker run -d -p 6379:6379 redis:7-alpine")
        print("  2. 或配置阿里云 Redis 地址")
        return False


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("NOK AI Lab - 系统配置测试")
    print("=" * 60)

    db_ok = test_database_connection()
    redis_ok = test_redis_connection()

    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    print(f"  数据库：{'✅ 成功' if db_ok else '❌ 失败'}")
    print(f"  Redis：  {'✅ 成功' if redis_ok else '❌ 失败'}")

    if db_ok and redis_ok:
        print("\n🎉 所有测试通过！可以启动应用了")
        print("\n启动命令:")
        print("  cd backend && uvicorn app.main:app --reload")
        print("  cd frontend && npm run dev")
        sys.exit(0)
    else:
        print("\n⚠️  部分测试失败，请检查配置")
        sys.exit(1)
