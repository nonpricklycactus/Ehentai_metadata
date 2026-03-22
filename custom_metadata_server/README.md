# 自定义元数据服务器参考实现

## 概述

此目录包含Ehentai_metadata Calibre插件的自定义元数据服务器参考实现。该实现遵循插件定义的Custom Metadata Server Protocol v1.0规范。

## 文件结构

```
custom_metadata_server/
├── custom_metadata_server_example.py  # Flask服务器主程序
├── test_custom_server.py              # 综合测试脚本
├── CUSTOM_METADATA_SERVER_GUIDE.md    # 详细使用指南
├── start_server.bat                   # Windows启动脚本
├── start_server.sh                    # Linux/macOS启动脚本
└── README.md                          # 本文件
```

## 快速开始

### 1. 启动服务器

**Windows:**
```cmd
cd custom_metadata_server
start_server.bat
```

**Linux/macOS:**
```bash
cd custom_metadata_server
chmod +x start_server.sh
./start_server.sh
```

### 2. 测试服务器

```bash
cd custom_metadata_server
python test_custom_server.py
```

### 3. 配置Calibre插件

1. 打开Calibre → 首选项 → 元数据 → 元数据来源
2. 选择"E-hentai Galleries" → 配置
3. 设置：
   - **自定义元数据服务器URL**: `http://localhost:5000/metadata`
   - **自定义元数据验证令牌**: `Bearer test-token-123`

## 协议规范

### 请求格式 (插件 → 服务器)
```json
POST /metadata
{
  "schema_version": "1.0",
  "search_type": "identify",
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
  "results": [{
    "title": "Gallery Title",
    "authors": ["Artist Name"],
    "publisher": "Circle Name",
    "tags": ["female:glasses", "category:doujinshi"],
    "rating": 4.5,
    "cover_url": "https://example.com/cover.jpg",
    "identifiers": {"ehentai": "12345_abc_0"}
  }],
  "error": null
}
```

## 示例数据

服务器包含以下示例数据用于测试：

| 标题 | 作者 | E-Hentai ID | 标签示例 |
|------|------|-------------|----------|
| 拘束する部活動 | すもも堂 | 3852762_f65294d2bb_0 | category:doujinshi, parody:fate, character:saber |
| イブキとい～っぱいシようねっ♡ | 比宮じょーず | 1234567_abcdef_0 | category:doujinshi, parody:blue-archive, character:ibuki |
| Example Manga | Sample Artist | 9999999_xyz_0 | category:manga, female:catgirl |

## 开发自定义服务器

### 基于此示例开发

1. **修改配置**: 编辑`custom_metadata_server_example.py`中的`CONFIG`部分
2. **替换数据源**: 将`SAMPLE_METADATA`替换为真实数据库查询
3. **扩展功能**: 添加新的搜索逻辑或外部API集成
4. **生产部署**: 使用Gunicorn等WSGI服务器部署

### 协议兼容性要求

- 必须支持POST `/metadata`端点
- 必须遵循v1.0协议格式
- 必须返回有效的JSON响应
- 建议支持Bearer token认证

## 故障排除

### 常见问题

1. **端口占用**: 修改`CONFIG['port']`为其他端口（如8080）
2. **认证失败**: 确认插件和服务器使用相同的Bearer token
3. **无结果返回**: 检查请求格式和示例数据匹配
4. **连接失败**: 确认服务器正在运行且防火墙允许连接

### 调试方法

1. 查看服务器控制台输出
2. 使用测试脚本验证功能
3. 检查Calibre错误日志
4. 使用curl手动测试端点

## 扩展建议

### 功能扩展
- 数据库集成（SQLite/MySQL/PostgreSQL）
- 外部API集成（AniList、MyAnimeList等）
- 缓存机制提高性能
- 用户管理界面

### 部署优化
- Docker容器化
- 负载均衡
- HTTPS支持
- 监控和日志聚合

## 相关文件

- `../protocol.py` - 插件端的协议客户端实现
- `../AGENTS.md` - 插件开发文档
- `../README.md` - 插件主文档

## 许可证

此参考实现遵循与主插件相同的GPL v3许可证。