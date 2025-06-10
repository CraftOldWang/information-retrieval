#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查Elasticsearch状态和数据的脚本
用于验证爬取的数据是否正确存储在ES中
"""

import json
import sys
from datetime import datetime
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import ConnectionError, NotFoundError


def check_es_connection():
    """检查Elasticsearch连接"""
    try:
        es = Elasticsearch(
            ["http://localhost:9200"],
            verify_certs=False,
            ssl_show_warn=False,
            request_timeout=30,
        )

        if es.ping():
            print("✅ Elasticsearch连接成功")

            # 获取集群信息
            cluster_info = es.info()
            print(f"📊 ES版本: {cluster_info['version']['number']}")
            print(f"📊 集群名称: {cluster_info['cluster_name']}")
            return es
        else:
            print("❌ Elasticsearch连接失败")
            return None

    except ConnectionError as e:
        print(f"❌ 无法连接到Elasticsearch: {e}")
        return None
    except Exception as e:
        print(f"❌ Elasticsearch连接异常: {e}")
        return None


def check_indices(es):
    """检查索引状态"""
    try:  # 获取所有索引
        indices = es.indices.get_alias(index="*")
        print(f"\n📁 当前索引列表:")

        target_index = "nku_webpages"
        index_exists = False

        for index_name in indices:
            print(f"  - {index_name}")
            if index_name == target_index:
                index_exists = True

        if index_exists:
            print(f"\n✅ 目标索引 '{target_index}' 存在")
            # 获取索引统计信息
            stats = es.indices.stats(index=target_index)
            doc_count = stats["indices"][target_index]["total"]["docs"]["count"]
            store_size = stats["indices"][target_index]["total"]["store"][
                "size_in_bytes"
            ]

            print(f"📊 文档数量: {doc_count}")
            print(f"📊 存储大小: {store_size / 1024 / 1024:.2f} MB")

            # 获取索引映射
            mapping = es.indices.get_mapping(index=target_index)
            properties = mapping[target_index]["mappings"].get("properties", {})
            print(f"📊 字段数量: {len(properties)}")
            print(f"📊 字段列表: {list(properties.keys())}")

            return target_index, doc_count
        else:
            print(f"\n❌ 目标索引 '{target_index}' 不存在")
            return None, 0

    except Exception as e:
        print(f"❌ 检查索引时出错: {e}")
        return None, 0


def check_data_samples(es, index_name, doc_count):
    """检查数据样本"""
    if not index_name or doc_count == 0:
        print("\n⚠️ 没有数据可以检查")
        return

    try:
        print(f"\n🔍 检查数据样本...")
        # 获取前5个文档
        response = es.search(
            index=index_name,
            query={"match_all": {}},
            size=5,
            source=["url", "title", "domain", "crawl_time"],
        )

        hits = response["hits"]["hits"]
        print(f"📄 前{len(hits)}个文档样本:")

        for i, hit in enumerate(hits, 1):
            source = hit["_source"]
            print(f"\n  {i}. 文档ID: {hit['_id']}")
            print(f"     URL: {source.get('url', 'N/A')}")
            print(f"     标题: {source.get('title', 'N/A')[:50]}...")
            print(f"     域名: {source.get('domain', 'N/A')}")
            print(f"     爬取时间: {source.get('crawl_time', 'N/A')}")
        # 检查域名分布
        print(f"\n🌐 域名分布:")
        domain_agg = es.search(
            index=index_name,
            query={"match_all": {}},
            size=0,
            aggs={"domains": {"terms": {"field": "domain", "size": 10}}},
        )

        domain_buckets = domain_agg["aggregations"]["domains"]["buckets"]
        for bucket in domain_buckets:
            print(f"  - {bucket['key']}: {bucket['doc_count']} 个文档")

        # 检查数据完整性
        print(f"\n🔍 数据完整性检查:")
        # 检查必填字段
        required_fields = ["url", "title", "content"]
        for field in required_fields:
            missing_query = {"bool": {"must_not": {"exists": {"field": field}}}}

            missing_count = es.count(index=index_name, query=missing_query)["count"]
            if missing_count == 0:
                print(f"  ✅ {field}: 所有文档都有此字段")
            else:
                print(f"  ⚠️ {field}: {missing_count} 个文档缺少此字段")
        # 检查内容长度分布
        print(f"\n📏 内容长度检查:")
        content_stats = es.search(
            index=index_name,
            query={"match_all": {}},
            size=0,
            aggs={
                "content_length": {
                    "stats": {
                        "script": {
                            "source": "doc['content.keyword'].size() > 0 ? doc['content.keyword'].value.length() : 0"
                        }
                    }
                }
            },
        )

        if "aggregations" in content_stats:
            stats = content_stats["aggregations"]["content_length"]
            print(f"  📊 平均长度: {stats['avg']:.0f} 字符")
            print(f"  📊 最短: {stats['min']:.0f} 字符")
            print(f"  📊 最长: {stats['max']:.0f} 字符")

    except Exception as e:
        print(f"❌ 检查数据样本时出错: {e}")


def compare_with_jsonl():
    """与JSONL文件进行对比"""
    try:
        print(f"\n📋 与JSONL文件对比:")

        jsonl_file = "../data/raw/crawled_data_2025-06-10.jsonl"
        with open(jsonl_file, "r", encoding="utf-8") as f:
            jsonl_count = sum(1 for line in f)

        print(f"  📄 JSONL文件中的条目数: {jsonl_count}")

        # 读取URL列表进行对比
        urls_in_jsonl = []
        with open(jsonl_file, "r", encoding="utf-8") as f:
            for line in f:
                data = json.loads(line.strip())
                urls_in_jsonl.append(data["url"])

        return jsonl_count, urls_in_jsonl

    except FileNotFoundError:
        print(f"  ⚠️ 未找到JSONL文件")
        return 0, []
    except Exception as e:
        print(f"  ❌ 读取JSONL文件时出错: {e}")
        return 0, []


def check_url_consistency(es, index_name, urls_in_jsonl):
    """检查URL一致性"""
    if not index_name or not urls_in_jsonl:
        return

    try:
        print(f"\n🔗 URL一致性检查:")
        # 获取ES中的所有URL
        response = es.search(
            index=index_name,
            query={"match_all": {}},
            size=1000,  # 假设不会超过1000个文档
            source=["url"],
        )

        urls_in_es = [hit["_source"]["url"] for hit in response["hits"]["hits"]]

        print(f"  📄 JSONL中的URL数量: {len(urls_in_jsonl)}")
        print(f"  📄 ES中的URL数量: {len(urls_in_es)}")

        # 找出差异
        urls_only_in_jsonl = set(urls_in_jsonl) - set(urls_in_es)
        urls_only_in_es = set(urls_in_es) - set(urls_in_jsonl)

        if urls_only_in_jsonl:
            print(f"  ⚠️ 只在JSONL中存在的URL: {len(urls_only_in_jsonl)}")
            for url in list(urls_only_in_jsonl)[:3]:  # 显示前3个
                print(f"    - {url}")

        if urls_only_in_es:
            print(f"  ⚠️ 只在ES中存在的URL: {len(urls_only_in_es)}")
            for url in list(urls_only_in_es)[:3]:  # 显示前3个
                print(f"    - {url}")

        if not urls_only_in_jsonl and not urls_only_in_es:
            print(f"  ✅ JSONL和ES中的URL完全一致")

    except Exception as e:
        print(f"❌ 检查URL一致性时出错: {e}")


def main():
    """主函数"""
    print("🔍 Elasticsearch数据检查工具")
    print("=" * 50)

    # 1. 检查连接
    es = check_es_connection()
    if not es:
        print("\n❌ 无法连接到Elasticsearch，请检查服务是否启动")
        return False

    # 2. 检查索引
    index_name, doc_count = check_indices(es)

    # 3. 检查数据样本
    check_data_samples(es, index_name, doc_count)

    # 4. 与JSONL文件对比
    jsonl_count, urls_in_jsonl = compare_with_jsonl()

    # 5. 检查URL一致性
    check_url_consistency(es, index_name, urls_in_jsonl)

    # 6. 总结
    print(f"\n📊 总结:")
    print(f"  - Elasticsearch中有 {doc_count} 个文档")
    print(f"  - JSONL文件中有 {jsonl_count} 个条目")

    if doc_count > 0 and jsonl_count > 0:
        if doc_count == jsonl_count:
            print(f"  ✅ 数据量一致，看起来爬虫工作正常")
            print(f"  🚀 可以开始大规模爬取了！")
        else:
            print(f"  ⚠️ 数据量不一致，可能需要检查爬虫配置")
    elif doc_count == 0:
        print(f"  ❌ ES中没有数据，可能存储过程有问题")

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
