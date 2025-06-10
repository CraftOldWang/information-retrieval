# 文本索引模块

## 概述

文本索引模块负责对爬取的网页内容进行处理和索引，建立高效的搜索索引，为查询服务提供基础。本模块将使用 Elasticsearch 作为核心索引引擎，实现多域索引和高效检索。

## 技术选择

### Elasticsearch

选择 Elasticsearch 作为索引引擎的理由：

1. **高性能全文检索**: 基于 Lucene 的高性能全文搜索引擎
2. **分布式架构**: 支持横向扩展，能处理大规模数据
3. **丰富的查询语言**: 支持多种复杂查询方式，包括模糊查询、短语查询等
4. **中文分词支持**: 通过 IK 分词器等插件提供良好的中文支持
5. **高级功能**: 支持同义词、高亮显示、结果聚合等功能

## 索引设计

### 索引结构

将创建以下索引：

1. **网页索引**: 存储网页内容及元数据
2. **文档索引**: 存储 PDF、Word 等文档的元数据（不包含文档内容）
3. **锚文本索引**: 存储网页间的锚文本关系
4. **PageRank 索引**: 存储预计算的 PageRank 值

### 索引字段

网页索引的字段设计：

```json
{
    "url": {
        "type": "keyword"
    },
    "title": {
        "type": "text",
        "analyzer": "ik_max_word",
        "fields": {
            "keyword": {
                "type": "keyword"
            }
        }
    },
    "content": {
        "type": "text",
        "analyzer": "ik_max_word"
    },
    "anchor_texts": {
        "type": "text",
        "analyzer": "ik_max_word"
    },
    "domain": {
        "type": "keyword"
    },
    "last_updated": {
        "type": "date"
    },
    "crawl_time": {
        "type": "date"
    },
    "page_rank": {
        "type": "float"
    },
    "attachments": {
        "type": "nested",
        "properties": {
            "url": { "type": "keyword" },
            "type": { "type": "keyword" },
            "filename": { "type": "text" },
            "metadata": {
                "properties": {
                    "title": { "type": "text", "analyzer": "ik_max_word" },
                    "author": { "type": "text" },
                    "upload_date": { "type": "date" },
                    "file_size": { "type": "long" }
                }
            }
        }
    },
    "snapshot": {
        "type": "keyword"
    }
}
```

## 中文分词

将使用 IK 分词器对中文文本进行分词处理：

1. **IK 分词器**: 优秀的中文分词器，支持细粒度和粗粒度分词
2. **自定义词典**: 添加南开特有词汇，如学院名称、人名等
3. **停用词**: 配置停用词表，过滤无意义词汇

## 索引优化

1. **字段权重**: 为不同字段设置不同权重，如标题权重高于正文
2. **同义词处理**: 配置同义词字典，如"南开大学"="南开"="NKU"
3. **拼音支持**: 添加拼音分析器，支持拼音搜索
4. **分片和复制**: 合理设置索引分片数量，确保性能和可靠性

## 链接分析

实现基于 PageRank 的链接分析算法：

1. 构建网页间链接关系图
2. 计算每个页面的 PageRank 值
3. 将 PageRank 值存入索引，作为排序因素之一

## 数据导入流程

1. 从爬虫模块获取原始数据
2. 进行文本清洗和预处理
3. 使用 bulk API 批量导入 Elasticsearch
4. 定期更新索引以反映网页变化

## 索引维护

1. **索引更新**: 定期对索引进行增量更新
2. **索引优化**: 定期执行索引优化操作
3. **冷热分离**: 根据数据访问频率实现冷热数据分离
4. **索引备份**: 定期备份索引数据，确保数据安全

## 实现计划

1. 设置 Elasticsearch 环境
2. 配置 IK 分词器和自定义词典
3. 创建索引结构和映射
4. 开发数据处理和导入脚本
5. 实现链接分析和 PageRank 计算
6. 开发索引维护和更新机制

## 性能考量

1. 合理设置内存分配，避免频繁 GC
2. 优化索引结构，减少不必要的字段
3. 使用批量操作减少网络开销
4. 监控索引性能，及时调整参数
