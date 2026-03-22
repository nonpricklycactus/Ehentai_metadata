# 自定义元数据服务器使用指南

## 概述

Ehentai_metadata Calibre插件支持自定义元数据服务器功能，允许用户从自己的服务器获取元数据。本文档提供：
1. 协议规范说明
2. 示例服务器使用指南
3. 插件配置步骤
4. 开发自定义服务器的参考

## 协议规范 (v1.0)

### 请求格式 (插件 → 服务器)

```json
POST /metadata
Content-Type: application/json
Authorization: Bearer <token> (可选)

{
  "schema_version": "1.0",
  "search_type": "identify" | "cover",
  "title": "Gallery Title",
  "authors": ["Artist Name"],
  "identifiers": {"ehentai": "12345_abc_0"}
}
```

### 响应格式 (服务器 → 插件)

```json
{
  "schema_version": "1.0",
  "source": "My Metadata Server",
  "results": [
    {
      "title": "Gallery Title",
      "authors": ["Artist Name"],
      "publisher": "Circle Name",
      "tags": ["female:glasses", "category:doujinshi"],
      "rating": 4.5,
      "cover_url": "https://example.com/cover.jpg",
      "identifiers": {"ehentai": "12345_abc_0"}
    }
  ],
  "error": null
}
```

## 快速开始

### 1. 启动示例服务器

```bash
# 安装依赖
pip install flask

# 启动服务器
python custom_metadata_server_example.py
```

服务器启动后，访问以下端点：
- `http://localhost:5000/health` - 健康检查
- `http://localhost:5000/example-request` - 示例请求格式
- `http://localhost:5000/metadata` - 主元数据端点 (POST)

### 2. 测试服务器

```bash
# 运行测试脚本
python test_custom_server.py
```

### 3. 配置Calibre插件

1. 打开Calibre，进入 **首选项 → 元数据 → 元数据来源**
2. 选择 **"E-hentai Galleries"**，点击 **配置**
3. 设置以下选项：
   - **自定义元数据服务器URL**: `http://localhost:5000/metadata`
   - **自定义元数据验证令牌**: `Bearer test-token-123`
4. 点击 **确定**，重启Calibre（如果需要）

## 示例服务器功能

### 内置示例数据

服务器包含以下示例数据，可用于测试：

| 标题 | 作者 | 出版社 | 标签示例 | E-Hentai ID |
|------|------|--------|----------|-------------|
| 拘束する部活動 | すもも堂 | みらくるバーン | category:doujinshi, parody:fate, character:saber | 3852762_f65294d2bb_0 |
| イブキとい～っぱいシようねっ♡ | 比宮じょーず | みらくるバーン | category:doujinshi, parody:blue-archive, character:ibuki | 1234567_abcdef_0 |
| Example Manga | Sample Artist | Sample Circle | category:manga, female:catgirl | 9999999_xyz_0 |

### 搜索逻辑

1. **优先匹配**: 首先尝试匹配 `identifiers.ehentai` 字段
2. **标题匹配**: 如果无标识符匹配，尝试标题模糊匹配
3. **作者匹配**: 检查作者名称是否匹配

### 认证支持

- **启用认证**: 设置 `require_auth = True` 和 `auth_token`
- **Bearer令牌**: 使用 `Authorization: Bearer <token>` 头
- **测试令牌**: 示例服务器使用 `test-token-123`

## 开发自定义服务器

### 基本要求

1. **协议兼容**: 必须遵循 v1.0 协议规范
2. **JSON响应**: 必须返回有效的JSON响应
3. **错误处理**: 正确处理错误并返回 `error` 字段

### 扩展建议

1. **数据库集成**: 将示例数据替换为真实数据库
2. **外部API**: 集成其他元数据源（如AniList、MyAnimeList）
3. **缓存机制**: 添加缓存提高性能
4. **日志记录**: 记录请求和响应用于调试
5. **配置管理**: 使用配置文件或环境变量

### 示例扩展 - 连接数据库

```python
import sqlite3
from flask import Flask, request, jsonify

app = Flask(__name__)

def query_database(title, authors):
    """查询数据库获取元数据"""
    conn = sqlite3.connect('metadata.db')
    cursor = conn.cursor()
    
    # 简单的模糊查询示例
    query = """
    SELECT title, authors, publisher, tags, rating, cover_url, identifiers
    FROM metadata
    WHERE title LIKE ? OR ? LIKE '%' || title || '%'
    """
    
    cursor.execute(query, (f'%{title}%', title))
    results = []
    
    for row in cursor.fetchall():
        results.append({
            'title': row[0],
            'authors': json.loads(row[1]),
            'publisher': row[2],
            'tags': json.loads(row[3]),
            'rating': row[4],
            'cover_url': row[5],
            'identifiers': json.loads(row[6])
        })
    
    conn.close()
    return results
```

## 故障排除

### 常见问题

1. **服务器无法启动**
   - 检查端口是否被占用：`netstat -an | findstr :5000`
   - 确保已安装Flask：`pip install flask`

2. **插件无法连接**
   - 检查服务器URL是否正确
   - 验证防火墙设置
   - 确认服务器正在运行：访问 `http://localhost:5000/health`

3. **认证失败**
   - 检查令牌格式：`Bearer <token>`
   - 确认服务器和插件使用相同的令牌

4. **无结果返回**
   - 检查请求格式是否符合协议
   - 查看服务器日志了解错误信息

### 调试方法

1. **查看服务器日志**: 服务器运行时显示所有请求和响应
2. **使用测试脚本**: `python test_custom_server.py` 验证功能
3. **手动测试**: 使用curl或Postman发送测试请求
4. **检查Calibre日志**: Calibre错误日志可能包含插件错误信息

## 高级配置

### 修改服务器配置

编辑 `custom_metadata_server_example.py` 中的 `CONFIG` 部分：

```python
CONFIG = {
    'host': '0.0.0.0',  # 监听所有接口
    'port': 8080,       # 修改端口
    'debug': False,     # 生产环境设为False
    'auth_token': 'your-secret-token',  # 自定义令牌
    'require_auth': True,  # 启用认证
}
```

### 生产环境部署

1. **使用生产WSGI服务器**:
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 custom_metadata_server_example:app
   ```

2. **配置反向代理** (Nginx示例):
   ```nginx
   server {
       listen 80;
       server_name metadata.example.com;
       
       location / {
           proxy_pass http://127.0.0.1:5000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

3. **环境变量配置**:
   ```bash
   export METADATA_SERVER_TOKEN="your-token"
   export METADATA_SERVER_PORT="5000"
   ```

## 协议扩展建议

如需扩展协议，建议：

1. **保持向后兼容**: 新字段应为可选
2. **版本控制**: 使用 `schema_version` 字段
3. **文档更新**: 更新协议文档说明新功能

示例扩展字段:
```json
{
  "schema_version": "1.1",
  "search_type": "identify",
  "title": "...",
  "authors": ["..."],
  "identifiers": {...},
  "extended_fields": {  // 新增可选字段
    "publication_date": "2023-01-01",
    "page_count": 42,
    "color": true
  }
}
```

## 支持与反馈

如有问题或建议：

1. **查看项目文档**: 参考 `README.md` 和 `AGENTS.md`
2. **检查协议实现**: 查看 `protocol.py` 源码
3. **测试示例**: 运行提供的测试脚本
4. **报告问题**: 在项目仓库创建Issue

---

**注意**: 此示例服务器仅用于演示和测试目的。生产环境需要适当的安全措施、错误处理和性能优化。