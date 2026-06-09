#!/bin/bash

# Milo 知识库系统初始化脚本

set -e

echo "=== Milo 知识库系统初始化 ==="
echo ""

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "✗ 未找到 Python 3，请先安装"
    exit 1
fi
echo "✓ Python 3 已安装"

# 检查 Node.js
if ! command -v node &> /dev/null; then
    echo "✗ 未找到 Node.js，请先安装"
    exit 1
fi
echo "✓ Node.js 已安装"

# 复制环境变量文件
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✓ 已创建 .env 文件，请编辑填入配置"
else
    echo "✓ .env 文件已存在"
fi

# 安装后端依赖
echo ""
echo "安装后端依赖..."
cd backend
pip install -e .
cd ..
echo "✓ 后端依赖已安装"

# 安装前端依赖
echo ""
echo "安装前端依赖..."
cd frontend
npm install
cd ..
echo "✓ 前端依赖已安装"

# 初始化数据库
echo ""
echo "初始化数据库..."
python3 scripts/init_database.py

# 初始化 Elasticsearch
echo ""
echo "初始化 Elasticsearch..."
python3 scripts/init_elasticsearch.py

echo ""
echo "=== 初始化完成 ==="
echo ""
echo "启动后端服务: cd backend && uvicorn app.main:app --reload"
echo "启动前端服务: cd frontend && npm run dev"
echo ""
