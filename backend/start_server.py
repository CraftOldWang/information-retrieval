#!/usr/bin/env python3
"""
NKU搜索引擎后端启动脚本
"""
import os
import sys
import subprocess
from pathlib import Path

def main():
    """主函数"""
    # 确保在正确的目录
    backend_dir = Path(__file__).parent
    os.chdir(backend_dir)
    
    print("🚀 启动NKU搜索引擎后端服务...")
    print(f"📁 工作目录: {backend_dir}")
    
    # 检查Python版本
    if sys.version_info < (3, 8):
        print("❌ 需要Python 3.8或更高版本")
        sys.exit(1)
    
    # 检查是否安装了依赖
    try:
        import fastapi
        import uvicorn
        print("✅ 依赖检查通过")
    except ImportError as e:
        print(f"❌ 缺少依赖: {e}")
        print("请运行: pip install -r requirements.txt")
        sys.exit(1)
    
    # 创建必要的目录
    data_dirs = [
        "../data/sqlite",
        "../data/logs",
        "../data/uploads"
    ]
    
    for dir_path in data_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"📁 创建目录: {dir_path}")
    
    # 启动服务
    try:
        print("🌐 启动FastAPI服务器...")
        print("📖 API文档: http://127.0.0.1:8000/docs")
        print("🔍 搜索API: http://127.0.0.1:8000/api/v1/search")
        print("⏹️  按 Ctrl+C 停止服务")
        
        # 使用uvicorn启动
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "main:app",
            "--host", "127.0.0.1",
            "--port", "8000",
            "--reload",
            "--log-level", "info"
        ])
        
    except KeyboardInterrupt:
        print("\n👋 服务已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
