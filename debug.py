# 比较两个文件， 每一行是否一样

with open("./debug_retrieve/1.out", "r") as file1, open("./dev_output/1.out","r") as file2:
    for i in range(10000):
        content1 = file1.readline()
        if content1[1] == "\\":
            content1 = content1[:1] + "/" + content1[2:]
            # print("已替换")
        content2 = file2.readline()
        if content1 != content2:
            print(content1)
            print(content2)
            break