from elasticsearch import Elasticsearch, helpers
import os

def export_all_html_from_index(index_name, output_dir="exported_html"):
    es = Elasticsearch("http://localhost:9200")

    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)

    # 使用helpers.scan遍历所有文档，效率高，适合大数据量
    docs = helpers.scan(es, index=index_name, query={"query": {"match_all": {}}})

    count = 0
    for doc in docs:
        doc_id = doc["_id"]
        source = doc["_source"]

        html_content = source.get("html")
        if html_content:
            file_path = os.path.join(output_dir, f"{doc_id}.html")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            count += 1

    print(f"共导出 {count} 个html文件，保存在目录：{output_dir}")

if __name__ == "__main__":
    index_name = "nku_webpages"  # 替换成你的索引名
    export_all_html_from_index(index_name)
