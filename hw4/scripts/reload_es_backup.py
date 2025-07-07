#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从备份文件重新加载Elasticsearch数据
"""

import json
from elasticsearch import Elasticsearch


def reload_backup():
    """从备份文件重新加载数据"""
    print("📥 从备份文件重新加载Elasticsearch数据")
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

    # 加载备份文件
    backup_file = "data/raw/es_backup.json"
    try:
        with open(backup_file, "r", encoding="utf-8") as f:
            docs = json.load(f)
        print(f"📄 成功加载备份文件，包含 {len(docs)} 个文档")
    except Exception as e:
        print(f"❌ 加载备份文件失败: {e}")
        return False

    # 重新导入数据
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
                    if (
                        isinstance(anchor, dict)
                        and "text" in anchor
                        and "href" in anchor
                    ):
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
                es.index(index="nku_webpages", id=doc_id, document=doc)
                success += 1
                if success % 5 == 0:  # 每导入5个文档显示一次进度
                    print(f"  📊 已成功导入 {success}/{len(docs)} 个文档...")
            except Exception as e:
                print(f"  ⚠️ 导入文档ID {doc_id} 失败: {str(e)[:100]}...")
                errors += 1

        print(f"  ✅ 导入完成: 成功 {success} 个, 失败 {errors} 个")

    # 刷新索引
    es.indices.refresh(index="nku_webpages")
    print(f"✅ 备份数据导入完成!")

    return True


def main():
    """主函数"""
    success = reload_backup()
    return 0 if success else 1


if __name__ == "__main__":
    import sys

    sys.exit(main())
