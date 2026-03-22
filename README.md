[中文版README](README_cn.md)
<br/>

<img src="/image/telegram.png" width="200" height="200" alt="插件开发"/>


[![Telegram](/image/TelegramBots.svg)](https://t.me/+TAT5NFNLhI83MTc1)


This plugin downloads metadata from [E-Hentai Galleries](https://e-hentai.org/).

**Main Features**

- Can retrieve title, author, rating, tags and cover.
- If you enter the cookies of `exhentai.org`, it can download metadata from [ExHentai.org](https://exhentai.org/).
- Automatic tag translation to Chinese (fetches latest data from GitHub, no manual database setup required).
- Support for custom metadata servers to extend metadata sources. [See example implementation](custom_metadata_server/).

**Special Notes**

- Because E-Hentai Galleries dosen't have the author field , the title and author are regular expression matches. 
- Due to the particularity of E-Hentai, a vpn is needed in the mainland for the plug-in to operate normally
- Applicable to all versions of python3 in calibre

**Installation Notes**

1. Open the calibre client and select the preferences in the interface
2. After entering, we choose to load the plug-in option from the file
3. Select the plug-in zip installation package that we downloaded, and select the plug-in path
4. Then we will be prompted whether to install the plug-in and we choose yes
5. After selecting, the plug-in installation is complete
6. If there are other warnings, select yes, restart the client and see if the installation is successful

**Database configuration**

> ⚠️ As of v3.0.0, manual database configuration is no longer required. The plugin automatically fetches the latest translation data from the GitHub EhTagTranslation repository and caches it for 24 hours.
>
> Simply check "Translate tags to Chinese" in the plugin settings.

## ⚙️ Complete Configuration Guide

### Search Mode Options

#### 1. Use ExHentai
- **Function**: Search ExHentai instead of E-Hentai
- **Requirement**: Valid ExHentai cookies
- **Default**: Off

#### 2. Translate tags to Chinese
- **Function**: Automatically translate tags to Chinese
- **Mechanism**: Fetch latest translations from GitHub EhTagTranslation repository
- **Cache**: 24-hour automatic update
- **Default**: Off

#### 3. Accurate label mode
- **Function**: Get metadata from specific gallery URL
- **Use case**: When you know the exact gallery URL
- **Workflow**: Paste URL into title field, enable this option, then download metadata
- **Default**: Off
- **Note**: No dialog popup - URL must be pasted into title field

### Custom Metadata Server Options

#### 4. Enable custom metadata server
- **Function**: Enable third-party metadata server
- **Purpose**: Extend metadata sources, integrate other data sources
- **Requirement**: Server URL must be configured
- **Default**: Off

#### 5. Custom metadata server URL
- **Format**: `http://host:port/path` or `https://host:port/path`
- **Example**: `http://localhost:5000/metadata`
- **Protocol**: Must support Custom Metadata Server Protocol v1.0

#### 6. Custom metadata auth token
- **Format**: `Bearer <token>` or `Basic <base64>`
- **Example**: `Bearer my-secret-token-123`
- **Optional**: Leave empty if server doesn't require authentication

### Network Options

#### 7. Use proxy
- **Function**: Enable proxy server
- **Use case**: When proxy is needed to access E-Hentai/ExHentai
- **Default**: Off

#### 8. Proxy URL
- **Format**: `[user:pass@]host:port` or `http://host:port`
- **Example**: `127.0.0.1:1080` or `user:pass@proxy.example.com:8080`
- **Requirement**: Must be configured when "Use proxy" is enabled

### ExHentai Cookie Options

#### 9-11. ExHentai cookies (ipb_member_id, ipb_pass_hash, igneous)
- **How to obtain**:
  1. Log in to ExHentai website
  2. Open browser developer tools (F12)
  3. Go to Application/Storage → Cookies
  4. Find and copy the three cookie values
- **Requirement**: Must be configured when "Use ExHentai" is enabled
- **Security note**: These are sensitive information, keep them secure

## 🔧 Advanced Features

### Custom Metadata Server

#### Server Protocol
Plugin supports Custom Metadata Server Protocol v1.0:

**Request Format**:
```json
{
  "schema_version": "1.0",
  "search_type": "identify",
  "title": "Gallery Title",
  "authors": ["Artist Name"],
  "identifiers": {"ehentai": "12345_abc_0"}
}
```

**Response Format**:
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

#### Example Server
Complete example server implementation included:
```bash
cd custom_metadata_server
python custom_metadata_server_example.py
```

### Tag Translation System

#### How it works
1. **Automatic fetching**: Get latest translations from GitHub EhTagTranslation/Database
2. **Smart caching**: 24-hour cache, reduces network requests
3. **Real-time updates**: Check for updates each time plugin starts

#### Supported languages
- Chinese (Simplified)
- English (original tags)
- Japanese (some tags)

### Accurate Label Mode

#### Use cases
- Know the exact E-Hentai/ExHentai gallery URL
- When search returns no results or inaccurate results
- Need metadata for specific gallery

#### Steps (New Method - v3.0.0+)
1. Paste the gallery URL into the **Title** field (e.g., `https://e-hentai.org/g/1234567/abcdef123456/`)
2. Enable "Accurate label mode" in plugin settings
3. Download metadata - plugin will fetch from the specified URL

#### Important Change
- **v2.x**: Dialog popup for URL input
- **v3.0.0+**: No dialog - URL must be pasted into title field
- **Reason**: Calibre worker processes cannot display GUI dialogs

## 🐛 Troubleshooting

### Common Issues

#### 1. "No results found"
**Possible causes**:
- Network connection issues
- Title/author mismatch
- E-Hentai access restrictions

**Solutions**:
- Check network connection
- Try different search keywords
- Use "Accurate label mode" to specify URL directly

#### 2. "HTTP Error" or connection failure
**Possible causes**:
- Proxy configuration error
- Firewall blocking
- Server unavailable

**Solutions**:
- Check proxy settings
- Temporarily disable firewall for testing
- Confirm E-Hentai is accessible

#### 3. ExHentai access failure
**Possible causes**:
- Cookies expired or invalid
- Cookie format error
- ExHentai server issues

**Solutions**:
- Get fresh valid cookies
- Check all three cookie values are complete
- Confirm ExHentai account status is normal

#### 4. Custom server connection failure
**Possible causes**:
- Server not running
- URL format error
- Authentication failure
- Protocol incompatibility

**Solutions**:
1. Confirm server is running
2. Check URL format
3. Verify authentication token
4. Check server logs

### Debugging Steps

#### Check logs
1. Open Calibre → Preferences → Miscellaneous → Open Calibre configuration directory
2. Go to `logs` folder
3. Check latest log file
4. Search for "E-hentai Galleries" or "CustomMetadataClient"

#### Test connection
```bash
# Test E-Hentai access
curl https://e-hentai.org

# Test custom server
curl -X POST http://localhost:5000/metadata \
  -H "Content-Type: application/json" \
  -d '{"schema_version":"1.0","search_type":"identify","title":"test","authors":[],"identifiers":{}}'
```

#### Verify configuration
1. Confirm all required options are configured
2. Check dependencies between options
3. Test each feature separately

## 🔒 Security Notes

### Sensitive Information
1. **ExHentai Cookies**: Equivalent to passwords, do not share
2. **Proxy credentials**: Contain username and password
3. **Authentication tokens**: Access tokens for custom servers

### Security Recommendations
1. **Regular updates**: Periodically change sensitive information
2. **Local storage**: Configuration stored locally with encryption
3. **Minimum permissions**: Use accounts with minimum necessary permissions

### Privacy Protection
1. **Search history**: Not recorded in plugin
2. **Personal information**: No collection of user personal information
3. **Data transmission**: Use HTTPS for sensitive data transmission

## 📚 Version History

**Version 3.0.0** - 2026-03-22

- **Major refactoring for Calibre 9.5.0 compatibility**
- Modular architecture: split into 6 files (net, proxy, translation, protocol, ui, __init__)
- Rate limiting: 5-second delay between API bursts (prevents IP bans)
- Translation: automatic fetching from GitHub EhTagTranslation (no manual database setup)
- Custom metadata server: JSON protocol v1.0 for third-party integrations
- Proxy improvements: parse username:password@host:port with auth headers
- Accurate label mode: Changed from dialog popup to URL-in-title-field method (fixes worker process crashes)
- Qt compatibility: qt.core imports for Calibre 9.x
- Minimum Calibre version: 9.0.0
- Breaking changes: removed local SQLite database requirement

**Version 2.3.2** - 2022-11-23

- Optimize plug-in search ability
- Remove the Chinese Tags checkbox

**Version 2.3.1** - 2022-11-07

- Fix the problem that the revision data of e-station cannot be found

**Version 2.3.0** - 21 August 2022

- Remove uploader tag
- Resolved an issue where only one would be added when there are multiple artists and societies


**Version 2.2.7** - 20 August 2022

- Solve the problem of Accurate_Label crash in Calibre 6 version


**Version 2.2.6** - 4 May 2022

- Resolve to capitalize a tag if the language is English or undefined
- If the language is not defined, the language of the manga can be set to Japanese depending on whether there is a Japanese title
- Fixed some minor issues


**Version 2.2.5** - 21 April 2022

- Added the option to customize the proxy


**Version 2.2.4** - 17 April 2022

- Modify the regular expression to get information such as the author from the title
- Increased the type of meta information parsed
- Handle manga in multiple languages correctly


**Version 2.2.3** - 5 April 2022

- Change the accurate_URL input to pop-up box input
- After selecting Accurate_Label, the plug-in will be from the input e stand accurate_url:https://exhentai.org/g/21843\*\*/175ff141\*\*/ to get the label data


**Version 2.2.2** - 3 April 2022

- Add checkbox Accurate_Label
- After selecting Accurate_Label, the plug-in will be from the input e stand accurate_url:https://exhentai.org/g/21843\*\*/175ff141\*\*/ to get the label data


**Version 2.2.1** - 2 April 2022

- Add checkbox Chinese Tags
- After selecting Chinese Tags, the plug-in will search only Chinese books to obtain tag data, reducing the acquisition time


**Version 2.2.0** - 31 March 2022

- Added whether to translate

- To change the translation database mode, manually add the data source


**Version 2.1.1** - 25 March 2022

- Fixed the problem of not being able to access the Exhentai
- Cookie entry adds igneous value


**Version 2.1.0** - 25 August 2021

- New label can convert English to Chinese

**Version 1.1.0** - 5 April 2021

- Initial release

**Special Thanks**

This plug-in is adapted from the idea of ​​[doujinshi_metadata_plugins](https://github.com/yingziwu/doujinshi_metadata_plugins) of wuyingren.

The Database from EhTagTranslation [Database](https://github.com/EhTagTranslation/Database) and data transformation


