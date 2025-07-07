#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完全重置爬虫环境
删除Elasticsearch索引、清空Redis数据、备份JSONL文件
"""

import os
import shutil
import json
from datetime import datetime
from elasticsearch import Elasticsearch
import redis
import sys


def reset_elasticsearch():
    """重置Elasticsearch，删除索引"""
    print("🔄 重置Elasticsearch...")
    print("-" * 50)

    try:
        # 连接Elasticsearch
        es = Elasticsearch(
            ["http://localhost:9200"],
            verify_certs=False,
            ssl_show_warn=False,
            request_timeout=30,
        )

        if not es.ping():
            print("❌ Elasticsearch连接失败")
            return False

        print("✅ Elasticsearch连接成功")

        # 检查索引是否存在
        index_name = "nku_webpages"
        if es.indices.exists(index=index_name):
            # 删除索引
            es.indices.delete(index=index_name)
            print(f"🗑️ 索引 '{index_name}' 已删除")
        else:
            print(f"ℹ️ 索引 '{index_name}' 不存在，无需删除")

        return True
    except Exception as e:
        print(f"❌ Elasticsearch重置失败: {e}")
        return False


def reset_redis():
    """重置Redis，清空爬虫使用的数据"""
    print("\n🔄 重置Redis...")
    print("-" * 50)

    try:
        # 连接Redis
        r = redis.Redis(
            host="localhost",
            port=6379,
            db=0,
            decode_responses=True,
            socket_connect_timeout=5,
        )

        if not r.ping():
            print("❌ Redis连接失败")
            return False

        print("✅ Redis连接成功")

        # 查找并删除爬虫相关的键
        # 主要是 'crawled_urls' 集合
        keys = ["crawled_urls"]

        for key in keys:
            if r.exists(key):
                r.delete(key)
                print(f"🗑️ Redis键 '{key}' 已删除")
            else:
                print(f"ℹ️ Redis键 '{key}' 不存在，无需删除")

        # 或者彻底清空当前数据库（慎用）
        # r.flushdb()
        # print("🗑️ Redis数据库已清空")

        return True
    except Exception as e:
        print(f"❌ Redis重置失败: {e}")
        return False


def backup_jsonl_files():
    """备份现有的JSONL文件"""
    print("\n🔄 备份JSONL文件...")
    print("-" * 50)

    try:
        # 数据目录
        data_dir = "data/raw"
        backup_dir = "data/backups"

        # 创建备份目录
        os.makedirs(backup_dir, exist_ok=True)

        # 当前时间戳，用于备份文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 查找所有JSONL文件
        jsonl_files = [f for f in os.listdir(data_dir) if f.endswith(".jsonl")]

        if not jsonl_files:
            print("ℹ️ 没有找到JSONL文件，无需备份")
            return True

        for file_name in jsonl_files:
            src_path = os.path.join(data_dir, file_name)
            # 添加时间戳到备份文件名
            backup_name = f"{os.path.splitext(file_name)[0]}_{timestamp}.jsonl"
            dst_path = os.path.join(backup_dir, backup_name)

            # 复制文件
            shutil.copy2(src_path, dst_path)
            print(f"📑 已备份: {src_path} → {dst_path}")

            # 可选：删除原文件
            os.remove(src_path)
            print(f"🗑️ 删除原始文件: {src_path}")

        return True
    except Exception as e:
        print(f"❌ JSONL文件备份失败: {e}")
        return False


def create_elasticsearch_index():
    """创建新的Elasticsearch索引，使用正确的映射"""
    print("\n🔄 创建新的Elasticsearch索引...")
    print("-" * 50)

    try:
        # 连接Elasticsearch
        es = Elasticsearch(
            ["http://localhost:9200"],
            verify_certs=False,
            ssl_show_warn=False,
            request_timeout=30,
        )

        if not es.ping():
            print("❌ Elasticsearch连接失败")
            return False

        # 网页索引配置
        webpage_mapping = {
            "mappings": {
                "properties": {
                    "url": {"type": "keyword"},
                    "title": {
                        "type": "text",
                        "analyzer": "default",
                        "fields": {"keyword": {"type": "keyword"}},
                    },
                    "content": {"type": "text", "analyzer": "default"},
                    "html": {"type": "text", "store": True},  # 存储HTML
                    "anchor_texts": {
                        "type": "nested",  # 嵌套类型
                        "properties": {
                            "text": {"type": "text", "analyzer": "default"},
                            "href": {"type": "keyword"},
                        },
                    },
                    "domain": {"type": "keyword"},  # keyword类型
                    "metadata": {
                        "properties": {
                            "crawl_time": {"type": "date"},
                            "last_modified": {"type": "date"},
                            "content_type": {"type": "keyword"},
                        }
                    },
                    "attachments": {
                        "type": "nested",
                        "properties": {
                            "url": {"type": "keyword"},
                            "filename": {
                                "type": "text",
                                "fields": {"keyword": {"type": "keyword"}},
                            },
                            "type": {"type": "keyword"},
                            "metadata": {
                                "properties": {
                                    "title": {"type": "text", "analyzer": "default"},
                                    "author": {"type": "text"},
                                    "upload_date": {"type": "date"},
                                    "file_size": {"type": "long"},
                                }
                            },
                        },
                    },
                }
            },
            "settings": {
                "number_of_shards": 3,
                "number_of_replicas": 1,
                "analysis": {
                    "analyzer": {"default": {"type": "custom", "tokenizer": "ik_smart"}}
                },
            },
        }

        # 创建索引
        index_name = "nku_webpages"
        es.indices.create(index=index_name, body=webpage_mapping)
        print(f"✅ 索引 '{index_name}' 已创建，使用正确的映射")

        return True
    except Exception as e:
        print(f"❌ 创建Elasticsearch索引失败: {e}")
        return False


def main():
    """主函数"""
    print("🔁 完全重置爬虫环境")
    print("=" * 50)

    # 确认操作
    confirm = input("⚠️ 此操作将删除所有爬虫数据。确定要继续吗？(y/n): ")
    if confirm.lower() != "y":
        print("❌ 操作已取消")
        return 1

    # 重置Elasticsearch
    es_result = reset_elasticsearch()

    # 重置Redis
    redis_result = reset_redis()

    # 备份JSONL文件
    jsonl_result = backup_jsonl_files()

    # 创建新的ES索引
    index_result = create_elasticsearch_index()

    # 总结
    print("\n📋 重置结果:")
    print(f"Elasticsearch: {'✅ 成功' if es_result else '❌ 失败'}")
    print(f"Redis: {'✅ 成功' if redis_result else '❌ 失败'}")
    print(f"JSONL备份: {'✅ 成功' if jsonl_result else '❌ 失败'}")
    print(f"ES索引创建: {'✅ 成功' if index_result else '❌ 失败'}")

    if es_result and redis_result and jsonl_result and index_result:
        print("\n✅ 环境重置完成！系统已准备好重新爬取。")
        print("\n运行以下命令开始爬取:")
        print("cd crawler && scrapy crawl nku_main")
        return 0
    else:
        print("\n⚠️ 环境重置过程中出现错误，请查看上面的日志。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
