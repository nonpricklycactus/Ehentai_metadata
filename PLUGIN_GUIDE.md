# Ehentai Metadata Plugin - 完整使用指南

## 📖 概述

Ehentai Metadata Plugin 是一个 Calibre 插件，用于从 E-Hentai 和 ExHentai 图库下载元数据。本指南提供插件的完整安装、配置和使用说明。

---

## 🚀 快速开始

### 1. 安装插件
1. 下载插件 ZIP 文件
2. 打开 Calibre → 首选项 → 插件
3. 点击"从文件加载插件"
4. 选择下载的 ZIP 文件
5. 重启 Calibre

### 2. 基本配置
1. 打开 Calibre → 首选项 → 元数据 → 元数据来源
2. 选择"E-hentai Galleries" → 配置
3. 根据需要配置选项（见下文详细说明）

### 3. 使用插件
1. 在 Calibre 书库中选择书籍
2. 右键点击 → 下载元数据 → 下载元数据和封面
3. 选择"E-hentai Galleries"作为元数据来源

---

## ⚙️ 配置选项详解

### 搜索模式选项

#### 1. Use ExHentai
- **功能**: 使用 ExHentai 而不是 E-Hentai 进行搜索
- **要求**: 需要有效的 ExHentai cookies
- **默认值**: 关闭

#### 2. Translate tags to Chinese
- **功能**: 自动将标签翻译为中文
- **原理**: 从 GitHub EhTagTranslation 仓库获取最新翻译
- **缓存**: 24小时自动更新
- **默认值**: 关闭

#### 3. Accurate label mode
- **功能**: 精确模式，提示输入准确的图库URL
- **使用场景**: 知道具体图库URL时使用
- **工作流程**: 启用后，下载元数据时会弹出URL输入对话框
- **默认值**: 关闭

### 自定义元数据服务器选项

#### 4. Enable custom metadata server
- **功能**: 启用第三方元数据服务器
- **用途**: 扩展元数据来源，集成其他数据源
- **要求**: 需要配置服务器URL
- **默认值**: 关闭

#### 5. Custom metadata server URL
- **格式**: `http://host:port/path` 或 `https://host:port/path`
- **示例**: `http://localhost:5000/metadata`
- **协议**: 必须支持 Custom Metadata Server Protocol v1.0

#### 6. Custom metadata auth token
- **格式**: `Bearer <token>` 或 `Basic <base64>`
- **示例**: `Bearer my-secret-token-123`
- **可选**: 如果服务器不需要认证，可留空

### 网络选项

#### 7. Use proxy
- **功能**: 启用代理服务器
- **使用场景**: 需要代理访问 E-Hentai/ExHentai 时
- **默认值**: 关闭

#### 8. Proxy URL
- **格式**: `[user:pass@]host:port` 或 `http://host:port`
- **示例**: `127.0.0.1:1080` 或 `user:pass@proxy.example.com:8080`
- **要求**: 启用"Use proxy"时必须配置

### ExHentai Cookie 选项

#### 9-11. ExHentai cookies (ipb_member_id, ipb_pass_hash, igneous)
- **获取方法**:
  1. 登录 ExHentai 网站
  2. 打开浏览器开发者工具 (F12)
  3. 转到 Application/Storage → Cookies
  4. 查找并复制三个cookie值
- **要求**: 启用"Use ExHentai"时必须配置
- **安全提示**: 这些是敏感信息，请妥善保管

---

## 🔧 高级功能

### 自定义元数据服务器

#### 服务器协议
插件支持自定义元数据服务器协议 v1.0：

**请求格式**:
```json
{
  "schema_version": "1.0",
  "search_type": "identify",
  "title": "Gallery Title",
  "authors": ["Artist Name"],
  "identifiers": {"ehentai": "12345_abc_0"}
}
```

**响应格式**:
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

#### 示例服务器
项目包含完整的示例服务器实现：
```bash
cd custom_metadata_server
python custom_metadata_server_example.py
```

### 标签翻译系统

#### 工作原理
1. **自动获取**: 从 GitHub EhTagTranslation/Database 获取最新翻译
2. **智能缓存**: 24小时缓存，减少网络请求
3. **实时更新**: 每次启动插件时检查更新

#### 支持的语言
- 中文 (简体)
- 英文 (原标签)
- 日语 (部分标签)

### 精确模式 (Accurate Label Mode)

#### 使用场景
- 知道具体的 E-Hentai/ExHentai 图库URL
- 搜索无结果或结果不准确时
- 需要获取特定图库的元数据

#### 操作步骤
1. 启用"Accurate label mode"
2. 下载元数据时，会弹出URL输入对话框
3. 粘贴完整的图库URL，如: `https://e-hentai.org/g/1234567/abcdef123456/`
4. 插件直接获取该图库的元数据

---

## 🐛 故障排除

### 常见问题

#### 1. "No results found"
**可能原因**:
- 网络连接问题
- 标题/作者不匹配
- E-Hentai 访问限制

**解决方案**:
- 检查网络连接
- 尝试不同的搜索关键词
- 使用"Accurate label mode"直接指定URL

#### 2. "HTTP Error" 或连接失败
**可能原因**:
- 代理配置错误
- 防火墙阻止
- 服务器不可用

**解决方案**:
- 检查代理设置
- 暂时禁用防火墙测试
- 确认 E-Hentai 可正常访问

#### 3. ExHentai 访问失败
**可能原因**:
- Cookie 过期或无效
- Cookie 格式错误
- ExHentai 服务器问题

**解决方案**:
- 重新获取有效的 cookies
- 检查三个cookie值是否完整
- 确认 ExHentai 账号状态正常

#### 4. 自定义服务器连接失败
**可能原因**:
- 服务器未运行
- URL格式错误
- 认证失败
- 协议不兼容

**解决方案**:
1. 确认服务器正在运行
2. 检查URL格式
3. 验证认证令牌
4. 查看服务器日志

### 调试步骤

#### 查看日志
1. 打开 Calibre → 首选项 → 杂项 → 打开Calibre配置目录
2. 进入 `logs` 文件夹
3. 查看最新的日志文件
4. 搜索 "E-hentai Galleries" 或 "CustomMetadataClient"

#### 测试连接
```bash
# 测试 E-Hentai 访问
curl https://e-hentai.org

# 测试自定义服务器
curl -X POST http://localhost:5000/metadata \
  -H "Content-Type: application/json" \
  -d '{"schema_version":"1.0","search_type":"identify","title":"test","authors":[],"identifiers":{}}'
```

#### 验证配置
1. 确认所有必填选项已配置
2. 检查选项之间的依赖关系
3. 测试每个功能单独使用

---

## 📊 性能优化

### 网络优化
- **速率限制**: 5秒间隔，避免IP封禁
- **连接复用**: 重用浏览器实例
- **超时设置**: 默认30秒，可配置

### 缓存策略
- **翻译缓存**: 24小时本地缓存
- **封面缓存**: 临时文件缓存
- **结果缓存**: Calibre内置缓存

### 内存管理
- **模块化设计**: 按需加载模块
- **资源清理**: 及时释放资源
- **错误恢复**: 优雅的错误处理

---

## 🔒 安全注意事项

### 敏感信息
1. **ExHentai Cookies**: 相当于密码，请勿分享
2. **代理凭证**: 包含用户名和密码
3. **认证令牌**: 自定义服务器的访问令牌

### 安全建议
1. **定期更新**: 定期更换敏感信息
2. **本地存储**: 配置信息本地加密存储
3. **最小权限**: 使用最小必要权限的账号

### 隐私保护
1. **搜索记录**: 不在插件中记录搜索历史
2. **个人信息**: 不收集用户个人信息
3. **数据传输**: 使用HTTPS加密传输敏感数据

---

## 🔄 更新与维护

### 检查更新
1. 关注项目 GitHub 页面
2. 查看 Calibre 插件更新
3. 阅读 `UPDATE_NOTES.md` 了解最新更改

### 备份配置
1. 导出插件配置
2. 备份 Calibre 配置目录
3. 记录重要的配置信息

### 问题报告
遇到问题时，请提供:
1. Calibre 版本
2. 插件版本
3. 错误日志
4. 复现步骤
5. 相关配置信息

---

## 📚 相关资源

### 官方文档
- [Calibre 插件开发指南](https://manual.calibre-ebook.com/plugins.html)
- [E-Hentai API 文档](https://ehwiki.org/wiki/API)
- [EhTagTranslation 项目](https://github.com/EhTagTranslation/Database)

### 社区支持
- [GitHub Issues](https://github.com/nonpricklycactus/Ehentai_metadata/issues)
- [Calibre 论坛](https://www.mobileread.com/forums/forumdisplay.php?f=240)
- [相关 Telegram 群组](https://t.me/+TAT5NFNLhI83MTc1)

### 示例代码
- `custom_metadata_server/` - 自定义服务器完整示例
- `test_custom_server.py` - 服务器测试脚本
- `AGENTS.md` - AI开发指南（本地文件）

---

## 📝 版本历史

### v3.0.0 (2026-03-22)
- 模块化架构重构
- 自动标签翻译系统
- 自定义元数据服务器支持
- 速率限制和代理改进

### 当前更新 (2026-03-23)
- 修复 HTTP 400 错误
- 优化配置界面
- 增强调试日志
- 改进错误处理

### 未来计划
- 更多元数据字段支持
- 批量处理优化
- 用户界面改进
- 性能增强

---

## ❓ 常见问题解答

### Q: 插件支持哪些 Calibre 版本？
**A**: 支持 Calibre 9.0.0 及以上版本。

### Q: 需要 VPN 吗？
**A**: 在中国大陆需要 VPN 访问 E-Hentai/ExHentai。

### Q: 标签翻译准确吗？
**A**: 基于社区维护的 EhTagTranslation 数据库，准确率较高。

### Q: 可以自定义标签吗？
**A**: 可以通过自定义元数据服务器扩展标签系统。

### Q: 插件安全吗？
**A**: 开源代码，不收集用户数据，所有配置本地存储。

### Q: 遇到问题如何获取帮助？
**A**: 查看故障排除章节，或通过 GitHub Issues 提交问题。

---

## 📞 联系与支持

- **项目主页**: [GitHub](https://github.com/nonpricklycactus/Ehentai_metadata)
- **问题反馈**: [GitHub Issues](https://github.com/nonpricklycactus/Ehentai_metadata/issues)
- **更新通知**: 关注 GitHub 项目更新
- **社区讨论**: 相关论坛和群组

---

**最后更新**: 2026年3月23日  
**文档版本**: 1.0  
**插件版本**: v3.0.0+