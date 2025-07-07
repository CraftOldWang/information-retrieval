#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
临时修复Elasticsearch索引映射配置
在IK分词器插件安装之前使用标准分析器
"""

import sys
from pathlib import Path
import json


def create_temp_mapping():
    """创建不依赖IK分词器的临时映射配置"""
    temp_mapping = {
        "mappings": {
            "properties": {
                "url": {"type": "keyword"},
                "title": {
                    "type": "text",
                    "analyzer": "standard",  # 使用标准分析器替代ik_max_word
                    "fields": {"keyword": {"type": "keyword"}},
                },
                "content": {"type": "text", "analyzer": "standard"},  # 使用标准分析器
                "anchor_texts": {
                    "type": "text",
                    "analyzer": "standard",
                },  # 使用标准分析器
                "domain": {"type": "keyword"},
                "crawl_time": {"type": "date"},
                "last_modified": {"type": "date"},
                "content_type": {"type": "keyword"},
                "file_size": {"type": "integer"},
                "links_count": {"type": "integer"},
                "depth": {"type": "integer"},
            }
        },
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 0,
            # 暂时不使用IK分词器相关设置
            "analysis": {"analyzer": {"default": {"type": "standard"}}},
        },
    }
    return temp_mapping


def update_pipelines_temp():
    """临时更新pipelines.py，移除IK分词器依赖"""
    pipelines_file = Path("../crawler/nku_spider/pipelines.py")

    if not pipelines_file.exists():
        print("❌ pipelines.py 文件不存在")
        return False

    try:
        # 读取现有文件
        with open(pipelines_file, "r", encoding="utf-8") as f:
            content = f.read()

        # 替换IK分词器相关配置
        content = content.replace('"analyzer": "ik_max_word"', '"analyzer": "standard"')
        content = content.replace(
            '"analyzer": "ik_smart_pinyin"', '"analyzer": "standard"'
        )
        content = content.replace(
            '"search_analyzer": "ik_smart"', '"search_analyzer": "standard"'
        )

        # 备份原文件
        backup_file = pipelines_file.with_suffix(".py.backup")
        with open(backup_file, "w", encoding="utf-8") as f:
            f.write(content)

        # 写入临时修复版本
        with open(pipelines_file, "w", encoding="utf-8") as f:
            f.write(content)

        print("✅ pipelines.py 已临时修复，移除了IK分词器依赖")
        print(f"📁 原文件备份为: {backup_file}")
        return True

    except Exception as e:
        print(f"❌ 更新pipelines.py失败: {e}")
        return False


def main():
    """主函数"""
    print("🔧 临时修复Elasticsearch配置...")
    print("=" * 40)

    # 创建临时映射配置
    temp_mapping = create_temp_mapping()

    # 保存映射配置到文件
    config_dir = Path("../config/elasticsearch")
    config_dir.mkdir(parents=True, exist_ok=True)

    mapping_file = config_dir / "temp_mapping.json"
    with open(mapping_file, "w", encoding="utf-8") as f:
        json.dump(temp_mapping, f, indent=2, ensure_ascii=False)

    print(f"✅ 临时映射配置已保存: {mapping_file}")

    # 更新pipelines.py
    if update_pipelines_temp():
        print("\n🎉 临时修复完成！")
        print("📝 说明:")
        print("  - 已移除对IK分词器的依赖")
        print("  - 使用标准分析器替代")
        print("  - 中文分词效果可能不如IK，但不会报错")
        print("  - 安装IK插件后请恢复原配置")
        print("\n🚀 现在可以重新运行爬虫测试:")
        print("  cd crawler && scrapy crawl nku_main")
        return True
    else:
        print("\n❌ 临时修复失败")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
