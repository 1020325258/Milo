#!/usr/bin/env python3
"""
数据库初始化脚本

用于创建 Milo 知识库系统所需的数据库表。

使用方法:
    python scripts/init_database.py

环境变量:
    DATABASE_URL: 数据库连接地址（默认 mysql+pymysql://root:root@localhost:3306/milo）
"""

import os
import sys

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import create_engine, text

from app.core.config import settings
from app.models.base import Base


def create_database() -> None:
    """创建数据库（如果不存在）"""
    # 从 DATABASE_URL 中提取数据库名
    db_url = str(settings.DATABASE_URL)
    db_name = db_url.split("/")[-1].split("?")[0]

    # 连接到 MySQL（不指定数据库）
    base_url = db_url.rsplit("/", 1)[0]
    engine = create_engine(base_url)

    with engine.connect() as conn:
        conn.execute(
            text(f"CREATE DATABASE IF NOT EXISTS {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        )
        print(f"✓ 数据库 {db_name} 已创建或已存在")

    engine.dispose()


def create_tables() -> None:
    """创建所有表"""
    engine = create_engine(settings.DATABASE_URL)

    # 导入所有模型以确保它们被注册
    from app.models import Document, KnowledgeBase, Message  # noqa: F401

    Base.metadata.create_all(engine)
    print("✓ 所有表已创建")

    engine.dispose()


def main() -> None:
    """主函数"""
    print(f"数据库连接: {settings.DATABASE_URL}")

    try:
        print("\n创建数据库...")
        create_database()

        print("\n创建表...")
        create_tables()

        print("\n✓ 数据库初始化完成")

    except Exception as e:
        print(f"\n✗ 初始化失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
