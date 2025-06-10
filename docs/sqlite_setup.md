# SQLite数据库本地配置说明

## 为什么使用本地SQLite？

为了便于开发和调试，我们将SQLite数据库配置为在本地文件系统中运行，而不是在Docker容器内。这样做的好处包括：

1. **易于调试**: 可以直接使用SQLite工具查看和修改数据库
2. **数据持久性**: 数据不会因为容器重启而丢失
3. **性能**: 避免Docker网络层的开销
4. **开发便利**: 可以使用各种SQLite GUI工具

## 数据库文件位置

数据库文件存储在项目根目录下：
```
./data/sqlite/nku_search.db
```

## 推荐的SQLite工具

### 1. DB Browser for SQLite (免费)
- 下载地址: https://sqlitebrowser.org/
- 跨平台GUI工具，支持Windows/Mac/Linux
- 功能完整，包括数据查看、编辑、SQL查询等

### 2. SQLiteStudio (免费)
- 下载地址: https://sqlitestudio.pl/
- 功能强大的SQLite管理工具
- 支持插件扩展

### 3. VS Code扩展
```bash
# 安装SQLite Viewer扩展
# 在VS Code中搜索 "SQLite Viewer" 或 "SQLite"
```

### 4. 命令行工具
```bash
# Windows上可以下载SQLite命令行工具
# 下载地址: https://www.sqlite.org/download.html

# 使用命令行连接数据库
sqlite3 ./data/sqlite/nku_search.db

# 查看所有表
.tables

# 查看表结构
.schema users

# 执行SQL查询
SELECT * FROM users;

# 退出
.quit
```

## 数据库表结构

### users表 - 用户信息
```sql
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    college TEXT,
    major TEXT,
    grade TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### search_history表 - 搜索历史
```sql
CREATE TABLE IF NOT EXISTS search_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    query TEXT NOT NULL,
    search_type TEXT DEFAULT 'normal',
    results_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);
```

### user_preferences表 - 用户偏好
```sql
CREATE TABLE IF NOT EXISTS user_preferences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE,
    domain_preferences TEXT,  -- JSON格式存储域名偏好
    topic_preferences TEXT,   -- JSON格式存储主题偏好
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);
```

### click_logs表 - 点击记录
```sql
CREATE TABLE IF NOT EXISTS click_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    query TEXT,
    clicked_url TEXT,
    position INTEGER,  -- 结果在列表中的位置
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);
```

## 常用SQL查询示例

### 查看用户统计
```sql
-- 查看注册用户数
SELECT COUNT(*) as total_users FROM users;

-- 查看最近注册的用户
SELECT username, email, created_at 
FROM users 
ORDER BY created_at DESC 
LIMIT 10;
```

### 查看搜索统计
```sql
-- 查看最热门的搜索词
SELECT query, COUNT(*) as search_count 
FROM search_history 
GROUP BY query 
ORDER BY search_count DESC 
LIMIT 20;

-- 查看用户搜索活跃度
SELECT u.username, COUNT(sh.id) as search_count
FROM users u
LEFT JOIN search_history sh ON u.id = sh.user_id
GROUP BY u.id
ORDER BY search_count DESC;
```

### 查看点击统计
```sql
-- 查看最受欢迎的页面
SELECT clicked_url, COUNT(*) as click_count
FROM click_logs
GROUP BY clicked_url
ORDER BY click_count DESC
LIMIT 20;
```

## 数据备份

建议定期备份数据库文件：

```bash
# Windows PowerShell
Copy-Item "./data/sqlite/nku_search.db" "./data/sqlite/backup/nku_search_$(Get-Date -Format 'yyyyMMdd_HHmmss').db"

# Linux/Mac
cp ./data/sqlite/nku_search.db ./data/sqlite/backup/nku_search_$(date +%Y%m%d_%H%M%S).db
```

## 开发环境设置

1. 确保项目根目录下存在 `./data/sqlite/` 目录
2. 运行后端应用时，数据库会自动初始化
3. 使用上述工具连接数据库进行查看和调试

## 生产环境注意事项

在生产环境中，考虑：
1. 使用更强大的数据库系统（如PostgreSQL）
2. 设置数据库访问权限
3. 配置自动备份策略
4. 监控数据库性能和存储空间
