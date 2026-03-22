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

**Special Thanks**

This plug-in is adapted from the idea of ​​[doujinshi_metadata_plugins](https://github.com/yingziwu/doujinshi_metadata_plugins) of wuyingren.

The Database from EhTagTranslation [Database](https://github.com/EhTagTranslation/Database) and data transformation

**Version History:**

**Version 3.0.0** - 2026-03-22

- **Major refactoring for Calibre 9.5.0 compatibility**
- Modular architecture: split into 6 files (net, proxy, translation, protocol, ui, __init__)
- Rate limiting: 5-second delay between API bursts (prevents IP bans)
- Translation: automatic fetching from GitHub EhTagTranslation (no manual database setup)
- Custom metadata server: JSON protocol v1.0 for third-party integrations
- Proxy improvements: parse username:password@host:port with auth headers
- UI improvements: Accurate Label dialog with URL validation and layouts
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



