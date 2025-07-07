#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查Elasticsearch中的实际文档数量
排除嵌套对象导致的计数问题
"""

import json
from elasticsearch import Elasticsearch


def check_document_counts():
    """检查实际文档数量与嵌套对象数量"""
    print("🔢 检查Elasticsearch中的实际文档数量")
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

    print("✅ Elasticsearch连接成功")

    # 获取索引统计信息
    try:
        stats = es.indices.stats(index="nku_webpages")
        total_doc_count = stats["indices"]["nku_webpages"]["total"]["docs"]["count"]
        print(f"📊 ES报告的总文档数: {total_doc_count}")
    except Exception as e:
        print(f"❌ 获取统计信息失败: {e}")
        return False

    # 获取顶级文档数量
    try:
        # 使用cardinality聚合来获取唯一URL数量
        response = es.search(
            index="nku_webpages",
            body={
                "size": 0,
                "aggs": {"unique_urls": {"cardinality": {"field": "url"}}},
            },
        )

        # 获取实际网页文档数量
        unique_urls = response["aggregations"]["unique_urls"]["value"]
        print(f"📄 实际网页文档数(URL唯一计数): {unique_urls}")

        # 获取网页列表
        print(f"\n📑 获取实际网页列表...")
        response = es.search(
            index="nku_webpages",
            body={
                "query": {"match_all": {}},
                "_source": ["url", "title", "domain"],
                "size": unique_urls,
            },
        )

        hits = response["hits"]["hits"]
        print(f"✅ 找到 {len(hits)} 个网页文档")

        # 显示每个网页信息
        print("\n📋 网页文档列表:")
        for i, hit in enumerate(hits, 1):
            source = hit["_source"]
            print(
                f"{i}. {source.get('title', 'N/A')[:50]}... [{source.get('domain', 'N/A')}]"
            )

        # 分析嵌套对象数量
        print("\n🔍 分析嵌套对象数量...")

        # 检查anchor_texts嵌套字段
        nested_query = {
            "size": 0,
            "aggs": {"nested_count": {"nested": {"path": "anchor_texts"}}},
        }

        response = es.search(index="nku_webpages", body=nested_query)

        anchor_texts_count = response["aggregations"]["nested_count"]["doc_count"]
        print(f"🔗 锚文本(anchor_texts)嵌套对象数量: {anchor_texts_count}")

        # 检查attachments嵌套字段
        nested_query["aggs"]["nested_count"]["nested"]["path"] = "attachments"
        response = es.search(index="nku_webpages", body=nested_query)

        attachments_count = response["aggregations"]["nested_count"]["doc_count"]
        print(f"📎 附件(attachments)嵌套对象数量: {attachments_count}")

        # 计算总数
        estimated_total = unique_urls + anchor_texts_count + attachments_count
        print(f"\n📊 文档数量分析:")
        print(f"  - 网页文档数: {unique_urls}")
        print(f"  - 锚文本嵌套对象数: {anchor_texts_count}")
        print(f"  - 附件嵌套对象数: {attachments_count}")
        print(f"  - 估计总数: {estimated_total}")
        print(f"  - ES报告总数: {total_doc_count}")
        print(f"  - 差异: {total_doc_count - estimated_total}")

    except Exception as e:
        print(f"❌ 分析文档数量失败: {e}")
        return False

    return True


if __name__ == "__main__":
    check_document_counts()
