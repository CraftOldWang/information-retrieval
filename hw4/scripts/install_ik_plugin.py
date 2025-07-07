#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Elasticsearch IK 分词器插件安装脚本
用于NKU搜索引擎项目的中文分词支持
"""

import os
import sys
import requests
import subprocess
from pathlib import Path
import docker
import time


def check_docker_running():
    """检查Docker是否运行"""
    try:
        client = docker.from_env()
        client.ping()
        print("✅ Docker正在运行")
        return True
    except Exception as e:
        print(f"❌ Docker未运行或连接失败: {e}")
        return False


def get_elasticsearch_container():
    """获取Elasticsearch容器"""
    try:
        client = docker.from_env()
        containers = client.containers.list()

        for container in containers:
            if (
                "elasticsearch" in container.name.lower()
                or "elastic" in container.name.lower()
            ):
                print(f"✅ 找到Elasticsearch容器: {container.name}")
                return container

        print("❌ 未找到Elasticsearch容器")
        return None
    except Exception as e:
        print(f"❌ 获取容器列表失败: {e}")
        return None


def install_ik_plugin_method1(container):
    """方法1: 在容器内直接安装IK插件"""
    try:
        print("🔄 方法1: 在容器内安装IK插件...")

        # 在容器内执行安装命令
        result = container.exec_run(
            "elasticsearch-plugin install https://github.com/medcl/elasticsearch-analysis-ik/releases/download/v8.10.2/elasticsearch-analysis-ik-8.10.2.zip",
            privileged=True,
        )

        if result.exit_code == 0:
            print("✅ IK插件安装成功")
            return True
        else:
            print(f"❌ IK插件安装失败: {result.output.decode()}")
            return False

    except Exception as e:
        print(f"❌ 安装过程出错: {e}")
        return False


def install_ik_plugin_method2():
    """方法2: 下载插件文件并挂载到容器"""
    try:
        print("🔄 方法2: 下载IK插件文件...")

        # 创建插件目录
        plugin_dir = Path("../config/elasticsearch/plugins/ik")
        plugin_dir.mkdir(parents=True, exist_ok=True)

        # 下载IK插件
        plugin_url = "https://github.com/medcl/elasticsearch-analysis-ik/releases/download/v8.10.2/elasticsearch-analysis-ik-8.10.2.zip"
        plugin_file = plugin_dir / "elasticsearch-analysis-ik-8.10.2.zip"

        print(f"📥 正在下载: {plugin_url}")
        response = requests.get(plugin_url, stream=True)
        response.raise_for_status()

        with open(plugin_file, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        print(f"✅ 插件下载完成: {plugin_file}")

        # 解压插件
        import zipfile

        with zipfile.ZipFile(plugin_file, "r") as zip_ref:
            zip_ref.extractall(plugin_dir)

        print("✅ 插件解压完成")

        # 删除zip文件
        plugin_file.unlink()

        return True

    except Exception as e:
        print(f"❌ 下载安装失败: {e}")
        return False


def update_docker_compose():
    """更新docker-compose.yml以支持IK插件"""
    try:
        compose_file = Path("../docker-compose.yml")

        if not compose_file.exists():
            print("❌ docker-compose.yml文件不存在")
            return False

        # 读取现有配置
        with open(compose_file, "r", encoding="utf-8") as f:
            content = f.read()

        # 检查是否已经包含插件挂载配置
        if "plugins/" in content:
            print("✅ docker-compose.yml已包含插件配置")
            return True

        # 添加插件挂载配置
        # 在elasticsearch服务的volumes部分添加插件目录挂载
        lines = content.split("\n")
        new_lines = []
        in_elasticsearch_volumes = False

        for line in lines:
            new_lines.append(line)

            # 检测到elasticsearch的volumes部分
            if "elasticsearch:" in line:
                in_elasticsearch_volumes = False
            elif in_elasticsearch_volumes and "volumes:" in line:
                in_elasticsearch_volumes = True
            elif in_elasticsearch_volumes and line.strip().startswith("- "):
                # 在最后一个volume后添加插件挂载
                if "elasticsearch_logs" in line:
                    new_lines.append(
                        "      - ./config/elasticsearch/plugins:/usr/share/elasticsearch/plugins"
                    )
                    in_elasticsearch_volumes = False

        # 写回文件
        with open(compose_file, "w", encoding="utf-8") as f:
            f.write("\n".join(new_lines))

        print("✅ docker-compose.yml已更新")
        return True

    except Exception as e:
        print(f"❌ 更新docker-compose.yml失败: {e}")
        return False


def restart_elasticsearch():
    """重启Elasticsearch容器"""
    try:
        print("🔄 重启Elasticsearch容器...")

        # 使用docker-compose重启
        subprocess.run(
            ["docker-compose", "restart", "elasticsearch"], cwd="../", check=True
        )

        print("✅ Elasticsearch重启成功")

        # 等待服务启动
        print("⏳ 等待Elasticsearch启动...")
        time.sleep(30)

        return True

    except Exception as e:
        print(f"❌ 重启失败: {e}")
        return False


def verify_ik_installation():
    """验证IK插件是否安装成功"""
    try:
        print("🔍 验证IK插件安装...")

        # 检查插件是否可用
        response = requests.get("http://localhost:9200/_cat/plugins", timeout=10)

        if response.status_code == 200:
            plugins = response.text
            if "analysis-ik" in plugins:
                print("✅ IK插件安装验证成功")
                return True
            else:
                print("❌ IK插件未在插件列表中找到")
                print(f"已安装插件: {plugins}")
                return False
        else:
            print(f"❌ 无法获取插件列表: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ 验证过程出错: {e}")
        return False


def main():
    """主函数"""
    print("🚀 开始安装Elasticsearch IK分词器插件")
    print("=" * 50)

    # 1. 检查Docker是否运行
    if not check_docker_running():
        print("请先启动Docker服务")
        return False

    # 2. 获取Elasticsearch容器
    container = get_elasticsearch_container()

    # 3. 尝试安装插件
    success = False

    if container:
        # 方法1: 容器内安装
        success = install_ik_plugin_method1(container)

    if not success:
        # 方法2: 下载并挂载
        print("\n🔄 尝试方法2...")
        success = install_ik_plugin_method2()

        if success:
            # 更新docker-compose配置
            update_docker_compose()

            # 重启容器
            restart_elasticsearch()

    # 4. 验证安装
    if success:
        if verify_ik_installation():
            print("\n🎉 IK分词器插件安装完成！")
            print("现在可以重新运行爬虫测试中文分词功能")
            return True
        else:
            print("\n❌ 插件安装失败，请检查日志")
            return False
    else:
        print("\n❌ 所有安装方法都失败了")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
