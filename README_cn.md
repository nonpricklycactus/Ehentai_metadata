
<img src="/image/telegram.png" width="200" height="200" alt="插件开发"/>


[![Telegram](/image/TelegramBots.svg)](https://t.me/+TAT5NFNLhI83MTc1)

这个插件可以从[E站](https://e-hentai.org/)上下载本子的元数据。

**主要特点**

- 这个插件可以下载题名、作者、评分、tags、封面。
- 如果你输入了你在`exhentai.org`的cookies，这个插件可以从[ExHentai.org](https://exhentai.org/)上下载元数据。
- 可将标签自动翻译为中文（从 GitHub 自动拉取最新翻译数据，无需手动配置数据库）。
- 支持通过自定义元数据服务器扩展元数据来源。

**一些需要注意的事**

- 由于E-Hentai并没有独立的作者字段，插件所提供的题名与作者是通过正则表达式识别出来的。
- 由于E站的特殊性，大陆地区需要使用梯子，插件才能正常运行
- 适用于calibre中python3的所有版本

**安装方法**

1. 打开calibre客户端，选择界面中的首选项
2. 进入之后我们选择，从文件中加载插件选项
3. 选择我们下载好的插件zip安装包，选择插件路径
4. 然后就会提示我们是否安装插件我们选择是
5. 选择完之后，插件安装完成
6. 若有其它警告一律选是，重启客户端后看是否安装成功

**数据库配置**

> ⚠️ v3.0.0 起不再需要手动配置本地数据库。插件会自动从 GitHub EhTagTranslation 仓库拉取最新翻译数据，并缓存 24 小时。
>
> 只需在插件设置中勾选"Translate tags to Chinese"即可。


**特别感谢**

该插件由wuyingren的[doujinshi_metadata_plugins](https://github.com/yingziwu/doujinshi_metadata_plugins)思路改写。

该数据库来自EhTagTranslation的[Database](https://github.com/EhTagTranslation/Database)数据改造而来

## 🎯 最新更新 (2026年3月23日)

### 主要改进

#### 1. HTTP 400 错误修复
**问题**: 配置自定义元数据服务器时，插件返回 "HTTP Error 400: BAD REQUEST" 错误。

**根本原因**:
- Flask服务器要求 `Content-Type: application/json` 头部，但插件未正确发送
- 代理设置干扰了本地服务器的连接
- 请求参数验证不充分

**解决方案**:
- 在 `protocol.py` 中确保正确发送 `Content-Type: application/json` 头部
- 当未启用代理时，清除浏览器的代理设置
- 添加客户端参数验证和URL格式检查
- 使用更可靠的 `urllib.request` 方法发送请求

#### 2. 配置界面优化
**问题**: 自定义服务器配置选项分散在配置界面中，逻辑不清晰。

**解决方案**:
- 重新排序 `__init__.py` 中的选项定义
- 将自定义元数据服务器选项 (`use_custom_metadata`, `custom_metadata_url`, `custom_metadata_token`) 移到 `accurate_label` 选项之后
- 形成逻辑分组：精确模式 → 自定义服务器扩展

#### 3. 调试能力增强
**问题**: 出现错误时难以诊断问题原因。

**解决方案**:
- **插件端增强日志**: 在 `protocol.py` 中添加详细的请求/响应日志
- **服务器端增强日志**: 在 `custom_metadata_server_example.py` 中添加详细的验证日志
- **错误信息丰富化**: HTTP错误现在包含状态码、响应体等详细信息

## ⚙️ 完整配置指南

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

## 📚 版本历史

**Version 3.0.0** - 2026-03-22

- **针对 Calibre 9.5.0 的完整重构**
- 模块化架构：拆分为 6 个文件（net、proxy、translation、protocol、ui、__init__）
- 请求限速：API 请求之间自动等待 5 秒，防止被封 IP
- 标签翻译：从 GitHub EhTagTranslation 自动拉取最新数据（24 小时缓存），无需手动配置数据库
- 自定义元数据服务器：JSON 协议 v1.0，支持第三方集成
- 代理配置优化：支持 username:password@host:port 格式，自动生成认证请求头
- Accurate Label 界面优化：URL 格式校验，修复布局问题
- Qt 兼容性：使用 qt.core 导入，适配 Calibre 9.x
- 最低支持版本：Calibre 9.0.0
- 根本性变更：不再需要本地 SQLite 数据库文件

**Version 2.3.2** - 2022-11-22

- 优化插件搜索能力
- 去除Chinese Tags复选框


**Version 2.3.1** - 2022-11-07

- 修复e站改版数据搜索不到问题


**Version 2.3.0** - 2022-8-21

- 去除上传者标签
- 解决存在多个画师和社团时只会添加一个问题


**Version 2.2.7** - 2022-8-20

- 解决在Calibre 6版本Accurate_Label闪退问题


**Version 2.2.6** - 2022-5-4

- 解决在本子语言是英语或未定义的情况下把 tag 转为单词首字母大写
- 在语言未定义的情况下, 可以根据是否具有日文标题来设定漫画的语言为日语
- 修复一些小问题


**Version 2.2.5** - 2022-4-21

- 增加自定义代理的选项


**Version 2.2.4** - 2022-4-17

- 修改从标题中获取作者等信息的正则表达式
- 增加了解析到的元信息的种类
- 正确处理漫画具有多语言的情况


**Version 2.2.3** - 2022-4-5

- 将accurate_url的输入改为弹出框输入
- 选择Accurate_Label后插件将会从输入的e站accurate_url：https://exhentai.org/g/21843\*\*/175ff141\*\*/来获取标签数据



**Version 2.2.2** - 2022-4-3

- 增加复选框Accurate_Label
- 选择Accurate_Label后插件将会从输入的e站accurate_url：https://exhentai.org/g/21843\*\*/175ff141\*\*/来获取标签数据


**Version 2.2.1** - 2022-4-2

- 增加复选框Chinese Tags
- 选择Chinese Tags后插件将只搜索中文本子来获取标签数据，降低获取时间


**Version 2.2.0** - 2022-3-31

- 增加是否翻译功能
- 更改翻译数据库方式，需要手动添加数据源


**Version 2.1.1** - 2022-3-30

- 解决无法进入里站问题
- cookie填写项增加igneous值


**Version 2.1.0** - 2021-8-25

- 将标签变得更简洁
- 将部分标签改为中文



**Version 1.1.0** - 2021-4-5

- Initial release

