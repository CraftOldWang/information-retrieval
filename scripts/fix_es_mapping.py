#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复Elasticsearch的索引映射
解决domain字段聚合操作的问题
"""

import json
import os
import hashlib
from urllib.parse import urlparse
from elasticsearch import Elasticsearch


def fix_es_mapping():
    """修复ES索引映射"""
    print("🔧 修复Elasticsearch索引映射")
    print("=" * 50)

    # 初始化docs变量，避免可能未定义的错误
    docs = []

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
        # 备份数据
        print(f"📦 备份现有数据...")
        try:
            response = es.search(
                index=index_name,
                query={"match_all": {}},
                size=1000,  # 假设不会超过1000个文档
            )

            for hit in response["hits"]["hits"]:
                doc = hit["_source"]
                doc["_id"] = hit["_id"]
                docs.append(doc)

            print(f"  ✅ 成功备份了 {len(docs)} 个文档")
            # 保存备份到文件
            backup_file = "data/raw/es_backup.json"
            with open(backup_file, "w", encoding="utf-8") as f:
                json.dump(docs, f, ensure_ascii=False, indent=2)
            print(f"  ✅ 备份已保存到 {backup_file}")

        except Exception as e:
            print(f"  ❌ 备份数据失败: {e}")
            return False

        # 删除旧索引
        print(f"🗑️ 删除旧索引...")
        try:
            es.indices.delete(index=index_name)
            print(f"  ✅ 索引 {index_name} 已删除")
        except Exception as e:
            print(f"  ❌ 删除索引失败: {e}")
            return False

    # 创建新索引，使用正确的映射
    print(f"📝 创建新索引...")

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
                    "type": "nested",  # 改为嵌套类型
                    "properties": {
                        "text": {"type": "text", "analyzer": "default"},
                        "href": {"type": "keyword"}
                    }
                },
                "domain": {"type": "keyword"},  # 确保是keyword类型
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

    try:
        es.indices.create(index=index_name, body=webpage_mapping)
        print(f"  ✅ 索引 {index_name} 已创建，使用正确的映射")
    except Exception as e:
        print(f"  ❌ 创建索引失败: {e}")
        return False

    # 导入备份数据
    
    if docs:
        print(f"📤 导入备份数据...")
        success = 0
        errors = 0

        for doc in docs:
            doc_id = doc.pop("_id", None)
            
            # 处理anchor_texts字段格式问题
            if "anchor_texts" in doc:
                # 检查当前格式并转换为正确的嵌套格式
                anchor_texts = doc["anchor_texts"]
                # 如果不是列表，先转为空列表
                if not isinstance(anchor_texts, list):
                    anchor_texts = []
                
                # 如果列表中的元素不是字典或缺少必要的字段，进行转换
                normalized_anchors = []
                for anchor in anchor_texts:
                    if isinstance(anchor, dict) and "text" in anchor and "href" in anchor:
                        # 已经是正确格式
                        normalized_anchors.append(anchor)
                    elif isinstance(anchor, str):
                        # 如果是字符串，将其转为字典格式
                        normalized_anchors.append({"text": anchor, "href": ""})
                    elif isinstance(anchor, dict):
                        # 如果是字典但缺少字段，补充
                        text = anchor.get("text", "")
                        href = anchor.get("href", "")
                        if not text and "anchor_text" in anchor:
                            text = anchor["anchor_text"]
                        normalized_anchors.append({"text": text, "href": href})
                
                # 更新文档中的anchor_texts字段
                doc["anchor_texts"] = normalized_anchors
            
            try:
                es.index(index=index_name, id=doc_id, document=doc)
                success += 1
            except Exception as e:
                print(f"  ⚠️ 导入文档ID {doc_id} 失败: {str(e)[:100]}...")
                errors += 1

        print(f"  ✅ 导入完成: 成功 {success} 个, 失败 {errors} 个")

    # 刷新索引
    es.indices.refresh(index=index_name)
    print(f"✅ 索引映射修复完成!")

    return True


def main():
    """主函数"""
    success = fix_es_mapping()
    return 0 if success else 1


if __name__ == "__main__":
    import sys

    sys.exit(main())
