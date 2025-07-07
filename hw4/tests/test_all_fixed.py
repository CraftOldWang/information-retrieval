#!/usr/bin/env python3
"""
NKU搜索引擎项目 - 修复版连接测试脚本
使用修复后的Elasticsearch连接配置测试所有组件
"""

import sys
import traceback
from datetime import datetime


def test_elasticsearch():
    """测试Elasticsearch连接 - 使用修复的配置"""
    print("🔍 测试Elasticsearch连接...")
    try:
        from elasticsearch import Elasticsearch

        # 使用修复后的连接配置
        es = Elasticsearch(
            ["http://localhost:9200"],
            verify_certs=False,
            ssl_show_warn=False,
            request_timeout=30,
        )

        # 测试ping
        if not es.ping():
            print("❌ Elasticsearch ping失败")
            return False

        print("✅ Elasticsearch连接成功!")

        # 检查集群健康状态
        health = es.cluster.health()
        print(f"   集群状态: {health['status']}")
        print(f"   节点数: {health['number_of_nodes']}")
        print(f"   数据节点: {health['number_of_data_nodes']}")

        # 测试索引操作
        index_name = "test-connection"
        test_doc = {
            "title": "测试文档",
            "content": "这是一个测试文档",
            "timestamp": datetime.now().isoformat(),
        }

        # 创建测试文档
        result = es.index(index=index_name, document=test_doc)
        print(f"   测试文档创建: {result['result']}")

        # 删除测试索引
        if es.indices.exists(index=index_name):
            es.indices.delete(index=index_name)
            print(f"   测试索引已清理")

        return True

    except Exception as e:
        print(f"❌ Elasticsearch连接失败: {e}")
        traceback.print_exc()
        return False


def test_redis():
    """测试Redis连接"""
    print("\n🔴 测试Redis连接...")
    try:
        import redis

        # 连接到Redis
        r = redis.Redis(host="localhost", port=6379, decode_responses=True)

        # 测试连接
        r.ping()
        print("✅ Redis连接成功!")

        # 测试基本操作
        test_key = "test:connection"
        test_value = f"连接测试 - {datetime.now().isoformat()}"

        r.set(test_key, test_value, ex=60)  # 设置60秒过期
        retrieved_value = r.get(test_key)

        if retrieved_value == test_value:
            print(f"   数据读写测试: ✅ 成功")
        else:
            print(f"   数据读写测试: ❌ 失败")

        # 清理测试数据
        r.delete(test_key)
        print(f"   测试数据已清理")

        return True

    except Exception as e:
        print(f"❌ Redis连接失败: {e}")
        traceback.print_exc()
        return False


def test_scrapy():
    """测试Scrapy环境"""
    print("\n🕷️ 测试Scrapy环境...")
    try:
        import scrapy
        from scrapy.utils.project import get_project_settings

        print(f"✅ Scrapy版本: {scrapy.__version__}")

        # 测试项目设置
        import os

        current_dir = os.getcwd()

        try:
            os.chdir("crawler")
            settings = get_project_settings()
            print(f"   项目名称: {settings.get('BOT_NAME', 'N/A')}")
        finally:
            os.chdir(current_dir)

        return True

    except Exception as e:
        print(f"❌ Scrapy环境测试失败: {e}")
        traceback.print_exc()
        return False


def test_fastapi():
    """测试FastAPI环境"""
    print("\n🚀 测试FastAPI环境...")
    try:
        import fastapi
        import uvicorn
        from pydantic import BaseModel

        print(f"✅ FastAPI版本: {fastapi.__version__}")
        print(f"   Uvicorn可用: ✅")
        print(f"   Pydantic可用: ✅")

        return True

    except Exception as e:
        print(f"❌ FastAPI环境测试失败: {e}")
        traceback.print_exc()
        return False


def test_ml_libraries():
    """测试机器学习库"""
    print("\n🤖 测试机器学习库...")
    try:
        import pandas as pd
        import numpy as np
        import sklearn
        import jieba

        print(f"✅ Pandas版本: {pd.__version__}")
        print(f"   Numpy版本: {np.__version__}")
        print(f"   Scikit-learn版本: {sklearn.__version__}")
        print(f"   Jieba分词: ✅")

        # 测试jieba分词
        test_text = "南开大学搜索引擎项目"
        words = jieba.lcut(test_text)
        print(f"   分词测试: '{test_text}' -> {words}")

        return True

    except Exception as e:
        print(f"❌ 机器学习库测试失败: {e}")
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("🧪 NKU搜索引擎项目 - 修复版环境连接测试")
    print("=" * 60)

    # 检查Python环境
    print(f"🐍 Python版本: {sys.version.split()[0]}")
    print(
        f"   虚拟环境: {'✅ 已激活' if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix) else '❌ 未激活'}"
    )
    print()

    tests = [
        ("Elasticsearch", test_elasticsearch),
        ("Redis", test_redis),
        ("Scrapy", test_scrapy),
        ("FastAPI", test_fastapi),
        ("机器学习库", test_ml_libraries),
    ]

    results = {}
    for name, test_func in tests:
        try:
            results[name] = test_func()
        except Exception as e:
            print(f"❌ {name} 测试异常: {e}")
            results[name] = False

    # 总结
    print("\n" + "=" * 60)
    print("📊 测试结果总结:")

    success_count = 0
    for name, success in results.items():
        status = "✅ 通过" if success else "❌ 失败"
        print(f"   {name}: {status}")
        if success:
            success_count += 1

    print(f"\n🎯 总体状态: {success_count}/{len(tests)} 项测试通过")

    if success_count == len(tests):
        print("🎉 所有测试通过！项目环境已就绪！")
        print("\n📋 下一步操作:")
        print("   1. 启动爬虫: python scripts/start.py crawler")
        print("   2. 启动后端: python scripts/start.py backend")
        print("   3. 启动前端: python scripts/start.py frontend")
        print("   4. 一键启动所有服务: python scripts/start.py start --all")
        return True
    else:
        print("⚠️  部分测试失败，请检查相关服务")
        return False


if __name__ == "__main__":
    main()
