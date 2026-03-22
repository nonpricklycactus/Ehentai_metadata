# Ehentai Metadata Plugin - 更新说明

## 版本更新: 2026年3月23日

### 主要改进

本次更新主要解决了自定义元数据服务器集成中的关键问题，并改进了插件的配置界面和调试能力。

---

## 🎯 解决的问题

### 1. HTTP 400 错误修复
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

### 2. 配置界面优化
**问题**: 自定义服务器配置选项分散在配置界面中，逻辑不清晰。

**解决方案**:
- 重新排序 `__init__.py` 中的选项定义
- 将自定义元数据服务器选项 (`use_custom_metadata`, `custom_metadata_url`, `custom_metadata_token`) 移到 `accurate_label` 选项之后
- 形成逻辑分组：精确模式 → 自定义服务器扩展

### 3. 调试能力增强
**问题**: 出现错误时难以诊断问题原因。

**解决方案**:
- **插件端增强日志**: 在 `protocol.py` 中添加详细的请求/响应日志
- **服务器端增强日志**: 在 `custom_metadata_server_example.py` 中添加详细的验证日志
- **错误信息丰富化**: HTTP错误现在包含状态码、响应体等详细信息

---

## 🔧 技术细节

### 文件更改

#### 1. `__init__.py`
- **选项重新排序**: 第352-386行，将自定义服务器选项移到 `accurate_label` 之后
- **逻辑分组**:
  ```
  1. use_exhentai
  2. translate_tags
  3. accurate_label                    ← 精确模式
  4. use_custom_metadata               } 自定义服务器
  5. custom_metadata_url               } (精确模式扩展)
  6. custom_metadata_token             }
  7. use_proxy
  8. proxy_url
  9-11. ExHentai cookies
  ```

#### 2. `protocol.py` (CustomMetadataClient)
- **代理清理**: 添加 `br.set_proxies({})` 清除代理设置
- **头部处理**: 确保 `Content-Type: application/json` 正确发送
- **请求方法**: 优先使用 `urllib.request`，回退到浏览器方法
- **增强日志**: 添加请求头、代理状态、方法选择等调试信息
- **参数验证**: 添加输入参数类型检查和URL格式验证

#### 3. `custom_metadata_server_example.py`
- **验证日志**: 每个验证失败都记录详细原因
- **请求日志**: 记录客户端IP、请求头、原始请求体
- **调试信息**: 添加更多调试级别的日志输出

#### 4. `.gitignore`
- 新增文件，忽略开发环境文件
- 忽略 `.cache/`, `.sisyphus/`, `AGENTS.md` 等本地文件
- 忽略Python缓存文件和IDE配置文件

---

## 📋 使用说明

### 配置自定义元数据服务器

#### 1. 启动自定义服务器
```bash
cd custom_metadata_server
python custom_metadata_server_example.py
```
服务器默认运行在: `http://localhost:5000`

#### 2. 配置Calibre插件
1. 打开Calibre → 首选项 → 元数据 → 元数据来源
2. 选择"E-hentai Galleries" → 配置
3. 设置以下选项:
   - **Accurate label mode**: 可选启用
   - **Enable custom metadata server**: ✓ 勾选
   - **Custom metadata server URL**: `http://localhost:5000/metadata`
   - **Custom metadata auth token**: `Bearer test-token-123` (示例令牌)

#### 3. 测试配置
使用Calibre的"下载元数据"功能测试配置。查看Calibre日志确认连接成功。

### 故障排除

#### 常见问题

| 问题 | 可能原因 | 解决方案 |
|------|----------|----------|
| HTTP 400错误 | 1. Content-Type头部不正确<br>2. 代理干扰<br>3. 服务器URL格式错误 | 1. 检查插件日志<br>2. 禁用代理设置<br>3. 验证URL格式 |
| 连接被拒绝 | 1. 服务器未运行<br>2. 防火墙阻止<br>3. 端口被占用 | 1. 启动服务器<br>2. 检查防火墙设置<br>3. 更改服务器端口 |
| 无结果返回 | 1. 认证失败<br>2. 请求格式错误<br>3. 服务器无匹配数据 | 1. 检查认证令牌<br>2. 查看服务器日志<br>3. 测试简单请求 |

#### 调试步骤
1. **检查插件日志**: 查看Calibre日志中的 `CustomMetadataClient:` 消息
2. **检查服务器日志**: 查看服务器控制台输出
3. **测试连接**: 使用 `curl` 或浏览器测试服务器端点
4. **验证配置**: 确认所有配置选项正确设置

### 日志示例

#### 成功请求
```
CustomMetadataClient: sending request to http://localhost:5000/metadata
CustomMetadataClient: cleared proxy settings
CustomMetadataClient: request headers: {'Content-Type': 'application/json', 'Accept': 'application/json'}
CustomMetadataClient: trying direct urllib.request approach
CustomMetadataClient: direct urllib.request succeeded
CustomMetadataClient: got 2 results from Ehentai Metadata Example Server
```

#### 错误请求
```
CustomMetadataClient: request failed: HTTP Error 400: BAD REQUEST
CustomMetadataClient: endpoint=http://localhost:5000/metadata
CustomMetadataClient: HTTP status=400
CustomMetadataClient: response body={"error": "Missing required field: schema_version", ...}
```

---

## 🚀 新功能特性

### 1. 增强的日志系统
- **请求详情**: 记录URL、负载、头部
- **错误详情**: 包含HTTP状态码、响应体
- **方法选择**: 显示使用的请求方法
- **代理状态**: 记录代理设置清理

### 2. 客户端验证
- **URL验证**: 检查端点URL格式
- **参数验证**: 验证输入参数类型
- **错误预防**: 无效配置时禁用客户端

### 3. 配置界面优化
- **逻辑分组**: 相关选项放在一起
- **清晰标签**: 选项描述更明确
- **工具提示**: 提供详细的使用说明

---

## 📁 文件结构

```
Ehentai_metadata/
├── __init__.py              # 主插件文件 (选项重新排序)
├── protocol.py              # 自定义客户端 (HTTP 400修复)
├── net.py                   # 网络客户端
├── proxy.py                 # 代理配置
├── translation.py           # 标签翻译
├── ui.py                    # UI对话框
├── custom_metadata_server/  # 自定义服务器示例
│   ├── custom_metadata_server_example.py
│   ├── test_custom_server.py
│   └── README.md
├── image/                   # 插件图标
├── .gitignore              # Git忽略文件 (新增)
├── UPDATE_NOTES.md         # 更新说明 (本文件)
├── README.md               # 英文说明
└── README_cn.md            # 中文说明
```

---

## 🔄 向后兼容性

本次更新完全向后兼容：
- 现有配置保持不变
- 插件API未更改
- 自定义服务器协议未更改
- 所有现有功能正常工作

---

## 📞 支持与反馈

如果遇到问题：
1. 查看 `UPDATE_NOTES.md` 中的故障排除部分
2. 检查Calibre日志中的错误信息
3. 参考 `custom_metadata_server/README.md` 中的服务器指南
4. 在项目GitHub页面提交问题

---

**更新完成时间**: 2026年3月23日  
**版本**: 基于 v3.0.0 的增强更新  
**提交ID**: 775528dcc44d07ed2dc789cb2507819d5ca1c404