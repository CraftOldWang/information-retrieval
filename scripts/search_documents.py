#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
搜索文档工具
可用于搜索网页和文档（PDF、DOC等）
"""

import json
import argparse
from elasticsearch import Elasticsearch
from urllib.parse import urlparse


def search_documents(query, file_type=None, max_results=10):
    """搜索文档"""
    print(f"🔍 搜索: '{query}'")
    print("=" * 50)

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

    # 构建查询
    if file_type:
        # 搜索特定类型的附件
        search_query = {
            "query": {
                "nested": {
                    "path": "attachments",
                    "query": {
                        "bool": {
                            "must": [
                                {"match": {"attachments.type": file_type.lower()}}
                            ],
                            "should": [
                                {"match": {"attachments.metadata.title": query}},
                                {
                                    "wildcard": {
                                        "attachments.filename.keyword": f"*{query}*"
                                    }
                                },
                            ],
                            "minimum_should_match": 1,
                        }
                    },
                    "inner_hits": {},  # 返回匹配的内部文档
                }
            },
            "size": max_results,
        }
    else:
        # 搜索全文
        search_query = {
            "query": {
                "bool": {
                    "should": [
                        {"match": {"title": {"query": query, "boost": 3}}},
                        {"match": {"content": {"query": query, "boost": 2}}},
                        # 使用嵌套查询搜索锚文本
                        {
                            "nested": {
                                "path": "anchor_texts",
                                "query": {
                                    "match": {
                                        "anchor_texts.text": {
                                            "query": query,
                                            "boost": 1
                                        }
                                    }
                                }
                            }
                        },
                        # 也在附件中搜索
                        {
                            "nested": {
                                "path": "attachments",
                                "query": {
                                    "bool": {
                                        "should": [
                                            {
                                                "match": {
                                                    "attachments.metadata.title": query
                                                }
                                            },
                                            {
                                                "wildcard": {
                                                    "attachments.filename.keyword": f"*{query}*"
                                                }
                                            },
                                        ]
                                    }
                                },
                                "inner_hits": {},
                            }
                        },
                    ]
                }
            },
            "size": max_results,
        }

    # 执行搜索
    print(f"⏳ 正在搜索...")
    try:
        response = es.search(index="nku_webpages", body=search_query)
    except Exception as e:
        print(f"❌ 搜索失败: {e}")
        return False

    # 处理结果
    hits = response["hits"]["hits"]
    print(f"✅ 找到 {len(hits)} 个结果")

    # 如果没有结果
    if len(hits) == 0:
        print("😕 未找到匹配结果")
        return True

    # 显示结果
    print("\n📋 搜索结果:")

    for i, hit in enumerate(hits, 1):
        source = hit["_source"]
        score = hit["_score"]

        print(f"\n{i}. 得分: {score:.2f}")

        if file_type:
            # 如果是搜索附件，显示匹配的附件
            if "inner_hits" in hit and "attachments" in hit["inner_hits"]:
                attachment_hits = hit["inner_hits"]["attachments"]["hits"]["hits"]

                for j, att_hit in enumerate(attachment_hits, 1):
                    att_source = att_hit["_source"]
                    print(f"   📄 附件: {att_source.get('filename', 'Unknown')}")
                    print(f"   🔗 URL: {att_source.get('url', 'N/A')}")
                    print(f"   📝 类型: {att_source.get('type', 'unknown').upper()}")
                    print(
                        f"   📌 标题: {att_source.get('metadata', {}).get('title', 'N/A')}"
                    )
                    print(f"   📂 所属页面: {source.get('url', 'N/A')}")
                    print(f"   🏢 所属站点: {source.get('domain', 'N/A')}")
        else:
            # 普通网页搜索结果
            print(f"   🔗 URL: {source.get('url', 'N/A')}")
            print(f"   📌 标题: {source.get('title', 'N/A')[:80]}...")
            print(f"   🏢 域名: {source.get('domain', 'N/A')}")

            # 检查是否有匹配的附件
            if "inner_hits" in hit and "attachments" in hit["inner_hits"]:
                attachment_hits = hit["inner_hits"]["attachments"]["hits"]["hits"]
                if attachment_hits:
                    print(f"   📎 匹配的附件 ({len(attachment_hits)}):")
                    for j, att_hit in enumerate(attachment_hits[:3], 1):  # 只显示前3个
                        att_source = att_hit["_source"]
                        print(
                            f"      - {att_source.get('filename', 'Unknown')} ({att_source.get('type', 'unknown').upper()})"
                        )

    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="搜索网页和文档")
    parser.add_argument("query", help="搜索关键词")
    parser.add_argument("-t", "--type", help="文档类型 (如 pdf, doc, ppt 等)")
    parser.add_argument("-n", "--num", type=int, default=10, help="结果数量")

    args = parser.parse_args()
    success = search_documents(args.query, args.type, args.num)
