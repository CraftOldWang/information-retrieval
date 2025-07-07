import json

issues = []
total_items = 0

with open("data/raw/crawled_data_2025-06-10.jsonl", "r", encoding="utf-8") as f:
    for i, line in enumerate(f, 1):
        total_items += 1
        data = json.loads(line.strip())

        item_issues = []

        # 检查各种可能的问题
        if not data.get("title") or data["title"].strip() == "":
            item_issues.append("标题为空")

        if not data.get("content") or data["content"].strip() == "":
            item_issues.append("内容为空")

        content_len = len(data.get("content", "").strip())
        if content_len < 50:
            item_issues.append(f"内容过短({content_len}字符)")

        if not data.get("url"):
            item_issues.append("URL为空")

        if data.get("html") and len(data["html"]) < 100:
            item_issues.append("HTML内容过少")

        if item_issues:
            title = data.get("title", "未知")
            if len(title) > 50:
                title = title[:50] + "..."

            issues.append(
                {
                    "index": i,
                    "url": data.get("url", "未知"),
                    "title": title,
                    "issues": item_issues,
                }
            )

print(f"总条目数: {total_items}")
print(f"有问题的条目数: {len(issues)}")

if issues:
    print("\n存在问题的条目:")
    for issue in issues:
        print(f'  第{issue["index"]}条: {issue["title"]}')
        print(f'    URL: {issue["url"]}')
        print(f'    问题: {",".join(issue["issues"])}')
        print()
else:
    print("\n所有条目都没有明显的数据质量问题")

# 也检查一下内容长度分布
print("\n内容长度分布:")
content_lengths = []
with open("data/raw/crawled_data_2025-06-10.jsonl", "r", encoding="utf-8") as f:
    for line in f:
        data = json.loads(line.strip())
        content_len = len(data.get("content", "").strip())
        content_lengths.append(content_len)

content_lengths.sort()
print(f"最短: {min(content_lengths)} 字符")
print(f"最长: {max(content_lengths)} 字符")
print(f"平均: {sum(content_lengths)/len(content_lengths):.0f} 字符")
print(f"中位数: {content_lengths[len(content_lengths)//2]} 字符")
