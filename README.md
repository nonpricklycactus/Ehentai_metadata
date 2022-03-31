[中文版README](README_cn.md)

This plugin downloads metadata from [E-Hentai Galleries](https://e-hentai.org/).

**Main Features**

- Can retrieve title, author, rating , tags and cover.
- If you enter the cookies of `exhentai.org` , it can download metadata from [ExHentai.org](https://exhentai.org/).

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

** Database configuration **

1. After the plug-in is installed
2. Install the database file (ehtagTranslation.db) where you want to save it
3. Select Chinese_Exhentai in the plug-in and enter the location of the database file in the EhTagTranslation_db text box. Such as:


&emsp; &emsp; &emsp; &emsp; Position to E: \ Code \ python \ Ehentai_metadata \ EhTagTranslation db

&emsp; &emsp; &emsp; &emsp; Enter a value in the text box E:\Code\python\Ehentai_metadata in the text box

**Special Thanks**

This plug-in is adapted from the idea of ​​[doujinshi_metadata_plugins](https://github.com/yingziwu/doujinshi_metadata_plugins) of wuyingren.

The Database from EhTagTranslation [Database](https://github.com/EhTagTranslation/Database) and data transformation

**Version History:**

**Version 2.2.0** -  31 March 2022

- Added whether to translate


- To change the translation database mode, manually add the data source


**Version 2.1.0** - 25 August 2021

- New label can convert English to Chinese


**Version 1.1.0** - 5 April 2021

- Initial release


