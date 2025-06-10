#!/usr/bin/env python3
"""
NKU搜索引擎项目启动脚本
用于快速启动各个服务组件 - 支持统一虚拟环境
"""

import argparse
import subprocess
import sys
import os
import time
from pathlib import Path
from typing import Optional


def run_command(command: str, cwd: Optional[str] = None, background: bool = False):
    """运行命令"""
    print(f"正在执行: {command}")
    if cwd:
        print(f"工作目录: {cwd}")

    if background:
        # 后台运行
        process = subprocess.Popen(
            command, shell=True, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        return process
    else:
        # 前台运行
        result = subprocess.run(command, shell=True, cwd=cwd)
        return result.returncode == 0


def check_docker():
    """检查Docker是否可用"""
    try:
        result = subprocess.run(
            "docker --version", shell=True, capture_output=True, text=True
        )
        if result.returncode == 0:
            print(f"Docker版本: {result.stdout.strip()}")
            return True
        else:
            print("Docker未安装或不可用")
            return False
    except Exception as e:
        print(f"检查Docker时出错: {e}")
        return False


def check_virtual_env():
    """检查是否在虚拟环境中"""
    return hasattr(sys, "real_prefix") or (
        hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
    )


def start_docker_services():
    """启动Docker服务"""
    print("启动Docker服务...")
    project_root = Path(__file__).parent.parent
    return run_command("docker-compose up -d", cwd=str(project_root))


def stop_docker_services():
    """停止Docker服务"""
    print("停止Docker服务...")
    project_root = Path(__file__).parent.parent
    return run_command("docker-compose down", cwd=str(project_root))


def install_python_dependencies():
    """安装Python依赖"""
    print("安装Python依赖...")
    project_root = Path(__file__).parent.parent

    # 检查虚拟环境
    if not check_virtual_env():
        print("⚠️  建议在虚拟环境中运行:")
        print("   python -m venv venv")
        print("   venv\\Scripts\\activate  # Windows")
        print("   pip install -r requirements.txt")
        print("")
        print("继续在当前环境安装依赖...")
    else:
        print("✅ 检测到虚拟环境")

    # 安装依赖
    return run_command("pip install -r requirements.txt", cwd=str(project_root))


def start_crawler():
    """启动爬虫服务"""
    print("启动爬虫服务...")
    project_root = Path(__file__).parent.parent
    crawler_dir = project_root / "crawler"

    # 检查是否安装了依赖
    try:
        import scrapy

        print("✅ Scrapy已安装，启动爬虫...")
    except ImportError:
        print("❌ Scrapy未安装，请先运行: python scripts/start.py install")
        return False

    # 运行爬虫
    return run_command("scrapy crawl nku_main", cwd=str(crawler_dir))


def start_backend():
    """启动后端服务"""
    print("启动后端服务...")
    project_root = Path(__file__).parent.parent
    backend_dir = project_root / "backend"

    # 检查是否安装了依赖
    try:
        import fastapi

        print("✅ FastAPI已安装，启动后端...")
    except ImportError:
        print("❌ FastAPI未安装，请先运行: python scripts/start.py install")
        return False

    # 运行后端
    return run_command("python main.py", cwd=str(backend_dir), background=True)


def start_frontend():
    """启动前端服务"""
    print("启动前端服务...")
    project_root = Path(__file__).parent.parent
    frontend_dir = project_root / "frontend"

    # 检查是否安装了依赖
    if not (frontend_dir / "node_modules").exists():
        print("正在安装前端依赖...")
        install_success = run_command("npm install", cwd=str(frontend_dir))
        if not install_success:
            print("❌ 前端依赖安装失败")
            return False

    # 运行前端
    print("✅ 启动前端开发服务器...")
    return run_command("npm run dev", cwd=str(frontend_dir), background=True)


def main():
    parser = argparse.ArgumentParser(description="NKU搜索引擎项目启动脚本")
    parser.add_argument(
        "action",
        choices=[
            "start",
            "stop",
            "restart",
            "crawler",
            "backend",
            "frontend",
            "docker",
            "install",
        ],
        help="操作类型",
    )
    parser.add_argument("--all", action="store_true", help="操作所有服务")

    args = parser.parse_args()

    if args.action == "install":
        install_python_dependencies()

    elif args.action == "docker":
        if not check_docker():
            sys.exit(1)
        start_docker_services()

    elif args.action == "start":
        if args.all:
            print("🚀 启动所有服务...")

            # 1. 检查虚拟环境和依赖
            if not check_virtual_env():
                print("⚠️  建议在虚拟环境中运行")

            try:
                import fastapi, scrapy

                print("✅ Python依赖已安装")
            except ImportError:
                print(
                    "❌ Python依赖未完整安装，请先运行: python scripts/start.py install"
                )
                return

            # 2. 启动Docker服务
            if check_docker():
                start_docker_services()
                print("⏳ 等待Docker服务启动...")
                time.sleep(10)

            # 3. 启动后端
            print("🔧 启动后端服务...")
            start_backend()
            time.sleep(3)

            # 4. 启动前端
            print("🎨 启动前端服务...")
            start_frontend()

            print("\n🎉 所有服务启动完成!")
            print("📋 访问地址:")
            print("   - 前端界面: http://localhost:3000")
            print("   - 后端API: http://localhost:8000")
            print("   - API文档: http://localhost:8000/docs")
            print("   - Elasticsearch: http://localhost:9200")
            print("   - Kibana: http://localhost:5601")

        else:
            print("请指定要启动的服务或使用 --all 启动所有服务")

    elif args.action == "stop":
        if args.all:
            print("🛑 停止所有服务...")
            stop_docker_services()
            print("💡 注意: 前端和后端服务需要手动停止")
        else:
            stop_docker_services()

    elif args.action == "restart":
        if args.all:
            print("🔄 重启所有Docker服务...")
            stop_docker_services()
            time.sleep(5)
            start_docker_services()

    elif args.action == "crawler":
        start_crawler()

    elif args.action == "backend":
        start_backend()

    elif args.action == "frontend":
        start_frontend()


if __name__ == "__main__":
    main()
