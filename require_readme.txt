# NKU搜索引擎项目 - 统一依赖管理
# 包含爬虫模块和后端模块的所有Python依赖

# =================================
# 爬虫模块依赖 (Scrapy)
# =================================
scrapy>=2.11.0
scrapy-redis>=0.7.3
jieba>=0.42.1
beautifulsoup4>=4.12.0
lxml>=4.9.0

# =================================
# 后端模块依赖 (FastAPI)
# =================================
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.0.0
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
python-multipart>=0.0.6
httpx>=0.25.0
aiofiles>=23.0.0

# =================================
# 数据处理和分析
# =================================
pandas>=2.0.0
numpy>=1.24.0
scikit-learn>=1.3.0

# =================================
# 数据库和存储
# =================================
elasticsearch>=8.10.0
redis>=4.5.0

# =================================
# HTTP和网络
# =================================
requests>=2.31.0
urllib3>=2.0.0

# =================================
# 配置和日志
# =================================
python-dotenv>=1.0.0
python-dateutil>=2.8.0

# =================================
# 开发工具
# =================================
pytest>=7.0.0
pytest-asyncio>=0.21.0
black>=23.0.0
flake8>=6.0.0
mypy>=1.6.0

# =================================
# 安装说明
# =================================
# 1. 创建虚拟环境：python -m venv venv
# 2. 激活虚拟环境：venv\Scripts\activate (Windows) 或 source venv/bin/activate (Linux/Mac)
# 3. 安装依赖：pip install -r requirements.txt
# 4. 启动Docker服务：docker-compose up -d
