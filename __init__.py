#!/usr/bin/env python3
# vim:fileencoding=UTF-8:ts=4:sw=4:sta:et:sts=4:ai
from __future__ import (unicode_literals, division, absolute_import,
                        print_function)
from typing import Dict, List, Set, Union

__license__   = 'GPL v3'
__copyright__ = '2021, nonpricklycactus <https://github.com/nonpricklycactus/Ehentai_metadata>'
__docformat__ = 'restructuredtext en'

from calibre.ebooks.metadata.sources.base import Source, Option
from calibre.ebooks.metadata.book.base import Metadata
from calibre import as_unicode

import re
import sys
import json
import sqlite3
import html
from urllib.parse import urlencode
from PyQt5 import QtCore,QtWidgets,QtGui

# TODO: fill the LANGUAGE_LIST
LANGUAGE_DICT = {
    'Chinese'   : 'chinese',
    '中国語'    : 'chinese',
    '中国翻訳'  : 'chinese',
    '中国語翻訳': 'chinese',
    'Japanese'  : 'japanese',
    '日語'      : 'japanese',
    'English'   : 'english',
    'Spanish'   : 'spanish',
    'French'    : 'french',
    'Russian'   : 'russian',
}

# TODO: fill the OTHER_LIST
OTHER_DICT = {
    'Digital'   : 'digital',
    'DL版'      : 'digital',
    'Full Color': 'full color',
    '全彩'      : 'full color',
    'Uncensored': 'uncensored',
    'Decensored': 'uncensored',
    '無修正'    : 'uncensored',
}


def getName(list,i):
    try:
        return list[i]
    except:
        return ""

def findName(conn,comment,raw):
    try:
        str = conn.execute(comment).fetchone()[0]
        if ")" in str:
            pattern = re.compile('\)(.*)')
            str = pattern.search(str).group(1)
        return str
    except:
        return raw

def traslate(sqlitUrl,gmetadata):
    conn = sqlite3.connect(sqlitUrl)
    c = conn.cursor()
    tranTag = []

    if len(gmetadata.languages)>0:
        languages = gmetadata.languages
        i = 0
        for language in languages:
            Newlanguage = findName(c,"SELECT name from language WHERE raw like '{raw}'".format(raw=language),language)
            languages[i] = Newlanguage
            i=i+1
        gmetadata.languages = languages

    for tag in gmetadata.tags:
        j = 0
        taglist = tag.split(":")
        tableName = getName(taglist,0)
        nameSpace = findName(c,"SELECT name from rows WHERE key like '{key}'".format(key=tableName),tableName)
        if tableName == "group":
            tableName = "groups"
        raws = getName(taglist,1).split(",")
        if len(taglist) == 1:
            comment = "SELECT name from reclass WHERE raw like '{raw}'".format(raw=taglist[0])
            Newtag = findName(c, comment, taglist[0])
            tranTag.append(Newtag)
            continue
        for raw in raws:
            comment = "SELECT name from {table} WHERE raw like '{raw}'".format(table=tableName, raw=raw)
            Newtag = findName(c,comment,raw)
            if tableName == "groups":
                gmetadata.publisher = Newtag
            elif tableName == "artist":
                authors = gmetadata.authors
                authors[j] = Newtag
                j = j+1
                gmetadata.authors = authors
            else:
                Newtag = nameSpace + ":" + Newtag
                tranTag.append(Newtag)
    gmetadata.tags = tranTag
    conn.close()


class FieldFromTitle:
    def __init__(
        self,
        title: str,
        author: Union[str, None],
        publisher: Union[str, None],
        magazine_or_parody: Union[str, None],
        addtions: List[str]
    ):
        self.publisher              = publisher
        self.title                  = title
        self.author                 = author
        self.magazine_or_parody     = magazine_or_parody
        self.addtions               = addtions
        
def optional(pattern : str):
    return '(?:' + pattern + ')?'

def extractFieldFromTitle(title: str, log):
    pattern = re.compile(
          r'^\s*'                                               # match spaces                  (optional)
        + optional(r'\((?P<publisher>[^\(\)]+)\)')              # match publisher, such as C99  (optional)
        + r'\s*'                                                # match spaces                  (optional)
        + optional(r'\[(?P<author>[^\[\]]+)\]')                 # match author                  (optional)
        + r'\s*'                                                # match spaces                  (optional)
        + r'(?P<title>[^\[\]\(\)]+)'                            # match title                   (must, need strip)
        + r'\s*'                                                # match spaces                  (optional)
        + optional(r'\((?P<magazine_or_parody>[^\(\)]+)\)')     # match magazine_or_parody      (optional)
        + r'\s*'                                                # match spaces                  (optional)
        + optional(r'\[(?P<addtional1>[^\[\]]+)\]')             # match addtional_field_1       (optional)
        + r'\s*'                                                # match spaces                  (optional)
        + optional(r'\[(?P<addtional2>[^\[\]]+)\]')             # match addtional_field_2       (optional)
        + r'\s*'                                                # match spaces                  (optional)
        + optional(r'\[(?P<addtional3>[^\[\]]+)\]')             # match addtional_field_3       (optional)
    )

    match = re.match(pattern, title)

    if match:
        publisher = match.group('publisher')
        author = match.group('author')
        re_title = match.group('title').strip()
        magazine_or_parody = match.group('magazine_or_parody')
        addtions_with_none: List[Union[str, None]] = [match.group('addtional1'), match.group('addtional2'), match.group('addtional3')]
        addtions_without_none = [x for x in addtions_with_none if isinstance(x, str)]
    else:
        publisher = None
        author = None
        re_title = title
        magazine_or_parody = None
        addtions_without_none = []
        log.exception('Title match failed. Title is %s' % title)

    return FieldFromTitle(
        publisher           = publisher,
        title               = re_title,
        author              = author,
        magazine_or_parody  = magazine_or_parody,
        addtions            = addtions_without_none,
    )


def toMetadata(log, gmetadata, ExHentai_Status, Chinese_Status,sqlitUrl):  # {{{
    title = gmetadata['title']
    title_jpn = gmetadata['title_jpn']
    tags = gmetadata['tags']
    rating = gmetadata['rating']
    category = gmetadata['category']
    gid = gmetadata['gid']
    token = gmetadata['token']
    thumb = gmetadata['thumb']
    uploader = gmetadata['uploader']

    # determine if magazine_or_parody is magazine or parody
    is_parody = False
    has_jpn_title = bool(title_jpn)

    # title
    field_from_title = extractFieldFromTitle(title_jpn if title_jpn else title, log)
    title_ = field_from_title.title
    publisher = field_from_title.publisher
    author = field_from_title.author if field_from_title.author else 'Unknown'
    magazine_or_parody = field_from_title.magazine_or_parody
    addtional = field_from_title.addtions

    authors = [(author)]

    mi = Metadata(title_, authors)
    mi.identifiers = {'ehentai': '%s_%s_%d' % (str(gid), str(token), int(ExHentai_Status))}
    mi.publisher = publisher if publisher else 'Unknown'

    # tags and languages
    tags_ : Set[str] = set()
    languages: Set[str] = set()
    for tag in tags:
        tags_.add(tag)
        if re.match('language', tag):
            tag_ = re.sub('language:', '', tag)
            if tag_ != 'translated':
                languages.add(tag_)
        elif re.match('parody', tag):
            is_parody = True 

    tags_.add('category:%s' % category)

    # add magazine to tag if it has magazine attribute
    if not is_parody and magazine_or_parody:
        tags_.add('manazine:%s' % magazine_or_parody)

    # add uploader to tag
    tags_.add('uploader:%s' % uploader)

    for addtion in extractFieldFromTitle(title, log).addtions + (addtional if has_jpn_title else []):
        if addtion in OTHER_DICT:
            tags_.add('other:%s' % OTHER_DICT[addtion])
        elif addtion in LANGUAGE_DICT:
            tags_.add('language:%s' % LANGUAGE_DICT[addtion])
            languages.add(LANGUAGE_DICT[addtion])
        else:
            # assume addtion fields that aren't languages nor other tags are translators
            tags_.add('translator:%s' % addtion)

    mi.tags = list(tags_)
    mi.languages = list(languages)

    # rating
    mi.rating = float(rating)

    # cover
    mi.has_ehentai_cover = None
    if thumb:
        mi.has_ehentai_cover = thumb

    if Chinese_Status:
        traslate(sqlitUrl,mi)

    return mi
    # }}}

class getUrlUI():

    def setUI(self,w):
        #设置工具窗口的大小，前两个参数决定窗口的位置
        w.setGeometry(300,300,500,100)
        #设置工具窗口的标题
        w.setWindowTitle("精确获取标签")
        #设置窗口的图标
        #w.setWindowIcon(QtGui.QIcon('x.jpg'))

        # 添加文本标签
        self.label = QtWidgets.QLabel(w)
        # 设置标签的左边距，上边距，宽，高
        self.label.setGeometry(QtCore.QRect(60, 20, 150, 45))
        # 设置文本标签的字体和大小，粗细等
        self.label.setFont(QtGui.QFont("Roman times",20))
        self.label.setText("url:")
        #添加设置一个文本框
        self.text = QtWidgets.QLineEdit(w)
        #调整文本框的位置大小
        self.text.setGeometry(QtCore.QRect(150,30,180,30))
        #添加提交按钮和单击事件
        self.btn = QtWidgets.QPushButton(w)
        #设置按钮的位置大小
        self.btn.setGeometry(QtCore.QRect(150,140,70,30))
        #设置按钮的位置，x坐标,y坐标
        self.btn.move(400,30)
        self.btn.setText("提交")
        #为按钮添加单击事件
        self.btn.clicked.connect(self.getText)
        # 按钮点下后自动关闭当前界面
        self.btn.clicked.connect(w.close)
        w.show()

    def getText(self):
        global accurate_url
        accurate_url = self.text.text()

class Ehentai(Source):
    name = 'E-hentai Galleries'
    author = 'nonpricklycactus'
    version = (2, 2, 3)
    minimum_calibre_version = (1, 0, 0)

    description = _('Download metadata and cover from e-hentai.org.'
                    'Useful only for doujinshi.')

    capabilities = frozenset(['identify', 'cover'])
    touched_fields = frozenset(['title', 'authors', 'tags', 'rating', 'publisher', 'identifier:ehentai'])
    supports_gzip_transfer_encoding = True
    cached_cover_url_is_reliable = True

    EHentai_url = 'https://e-hentai.org/g/%s/%s/'
    ExHentai_url = 'https://exhentai.org/g/%s/%s/'

    sqlitUrl = "E:\Environment\EhTagTranslation.db"

    options = (
        Option('Use_Exhentai', 'bool', False, _('Use Exhentai'),
               _('If Use Exhentai is True, the plugin will search metadata on exhentai.')),
        Option('Chinese_Exhentai', 'bool', False, _('Chinese Exhentai'),
               _('If Use Chinese Exhentai is True, This plugin will translate metadata into Chinese.')),
        Option('Chinese_Tags', 'bool', False, _('Chinese Tags'),
               _('如果勾选Chinese_Tags，那么将只会搜索中文本子')),
        Option('Accurate_Label', 'bool', False, _('Accurate_Label'),
               _('如果勾选Accurate_Label，那么将只会获取给定accurate_url页面的tag')),
        Option('ipb_member_id', 'string', None, _('ipb_member_id'),
               _('If Use Exhentai is True, please input your cookies.')),
        Option('ipb_pass_hash', 'string', None, _('ipb_pass_hash'),
               _('If Use Exhentai is True, please input your cookies.')),
        Option('igneous', 'string', None, _('igneous'),
               _('If Use Exhentai is True, please input your cookies.')),
        Option('EhTagTranslation_db', 'string', None, _('EhTagTranslation_db'),
               _('Translate the location of the database files(翻译数据库文件所在位置)')

               )
    )

    config_help_message = ('<p>' + _('To Download Metadata from exhentai.org you must sign up'
                                     ' a free account and get the cookies of .exhentai.org.'
                                     ' If you don\'t have an account, you can <a href="%s">sign up</a>.')) % 'https://forums.e-hentai.org/index.php'

    def __init__(self, *args, **kwargs):  # {{{
        Source.__init__(self, *args, **kwargs)
        self.config_exhentai()
        self.config_chinese()
        self.config_tags()
    # }}}

    def config_tags(self):
        self.Accurate_Label = self.prefs['Accurate_Label']
        return


    def config_chinese(self):
        self.Chinese_Status = self.prefs['Chinese_Exhentai']
        self.Chinese_Tags = self.prefs['Chinese_Tags']
        EhTagTranslation_db = self.prefs['EhTagTranslation_db']
        if self.Chinese_Status is True:
            self.sqlitUrl = EhTagTranslation_db + "\EhTagTranslation.db"
        return

    def config_exhentai(self):  # {{{

        ExHentai_Status = self.prefs['Use_Exhentai']
        ExHentai_Cookies = [
            {'name': 'ipb_member_id', 'value': self.prefs['ipb_member_id'], 'domain': '.exhentai.org', 'path': '/'},
            {'name': 'igneous', 'value': self.prefs['igneous'], 'domain': '.exhentai.org', 'path': '/'},
            {'name': 'ipb_pass_hash', 'value': self.prefs['ipb_pass_hash'], 'domain': '.exhentai.org', 'path': '/'}]

        if ExHentai_Status is True:
            for cookie in ExHentai_Cookies:
                if cookie['value'] is None:
                    ExHentai_Status = False
                    break

        self.ExHentai_Status = ExHentai_Status
        self.ExHentai_Cookies = ExHentai_Cookies
        return

    # }}}

    def create_query(self, log, title=None, authors=None , identifiers={}, is_exhentai=False, chinese_tags = False):  # {{{

        EHentai_SEARCH_URL = 'https://e-hentai.org/?'
        ExHentai_SEARCH_URL = 'https://exhentai.org/?'

        q = ''

        if title or authors:
            def build_term(type, parts):
                return ' '.join(x for x in parts)

            title_token = list(self.get_title_tokens(title))
            if title_token:
                q = q + build_term('title', title_token)
            author_token = list(self.get_author_tokens(authors, only_first_author=True))
            if author_token:
                q = q + (' ' if q != '' else '') + build_term('author', author_token)

        if chinese_tags:
            q = q + " " + "chinese"
        q = q.strip()
        #print("查询条码：", q)
        if isinstance(q, str):
            q = q.encode('utf-8')
        if not q:
            return None
        q_dict = {'f_doujinshi': 1, 'f_manga': 1, 'f_artistcg': 1, 'f_gamecg': 1, 'f_western': 1, 'f_non-h': 1,
                  'f_imageset': 1, 'f_cosplay': 1, 'f_asianporn': 1, 'f_misc': 1, 'f_search': q,
                  'f_apply': 'Apply+Filter',
                  'advsearch': 1, 'f_sname': 'on','f_sh': 'on', 'f_srdd': 2}
        if is_exhentai is False:
            url = EHentai_SEARCH_URL + urlencode(q_dict)
        else:
            url = ExHentai_SEARCH_URL + urlencode(q_dict)
        #print("查询连接：",url)
        return url

    # }}}

    def get_gallery_info(self, log, raw):  # {{{

        pattern = re.compile(
            r'https:\/\/(?:e-hentai\.org|exhentai\.org)\/g\/(?P<gallery_id>\d+)/(?P<gallery_token>\w+)/')
        results = re.findall(pattern, raw)
        if not results:
            log.exception('Failed to get gallery_id and gallery_token!')
            return None
        #print("获取的信息：",results)
        gidlist = []
        for r in results:
            gidlist.append(list(r))
        return gidlist

    # }}}

    def isSubsequence(self,s: str, t: str) -> bool:
        n, m = len(s), len(t)
        i = j = 0
        while i < n and j < m:
            if s[i] == t[j]:
                i += 1
            j += 1
        return i == n

    def get_all_details(self, gidlist, log, abort, result_queue, timeout,title):  # {{{

        EHentai_API_url = 'https://api.e-hentai.org/api.php'
        br = self.browser
        data = {"method": "gdata", "gidlist": gidlist, "namespace": 1}
        data = json.dumps(data)
        try:
            raw = br.open_novisit(EHentai_API_url, data=data, timeout=timeout).read()
        except Exception as e:
            log.exception('Failed to make api request.', e)
            return

        gmetadatas = json.loads(raw)['gmetadata']
        Newgmetadatas = []
        for gmetadata in gmetadatas:
            gmetadata['title_jpn'] = html.unescape(gmetadata['title_jpn'])
            if self.isSubsequence(title,gmetadata['title_jpn']):
                Newgmetadatas.append(gmetadata)
        if len(Newgmetadatas)>0:
            gmetadatas = Newgmetadatas
        for relevance, gmetadata in enumerate(gmetadatas):
            try:
                ans = toMetadata(log, gmetadata, self.ExHentai_Status,self.Chinese_Status,self.sqlitUrl)
                if isinstance(ans, Metadata):
                    ans.source_relevance = relevance
                    db = ans.identifiers['ehentai']
                    if ans.has_ehentai_cover:
                        self.cache_identifier_to_cover_url(db, ans.has_ehentai_cover)
                    self.clean_downloaded_metadata(ans)
                    result_queue.put(ans)
            except:
                log.exception('Failed to get metadata for identify entry:', gmetadata)
            if abort.is_set():
                break

    # }}}

    def get_book_url(self, identifiers):  # {{{

        db = identifiers.get('ehentai', None)
        d = {'0': False, '1': True}
        if db is not None:
            gid, token, s = re.split('_', db)
            ExHentai_Status = d[str(s)]
            if ExHentai_Status:
                url = self.ExHentai_url % (gid, token)
            else:
                url = self.EHentai_url % (gid, token)
            return ('ehentai', db, url)

    # }}}

    def download_cover(self, log, result_queue, abort, title=None, authors=None, identifiers={}, timeout=30,
                       get_best_cover=False):  # {{{

        cached_url = self.get_cached_cover_url(identifiers)
        if cached_url is None:
            return
        if abort.is_set():
            return
        br = self.browser
        log('Downloading cover from:', cached_url)
        try:
            cdata = br.open_novisit(cached_url, timeout=timeout).read()
            if cdata:
                result_queue.put((self, cdata))
        except:
            log.exception('Failed to download cover from:', cached_url)

    # }}}

    def get_cached_cover_url(self, identifiers):  # {{{

        url = None
        db = identifiers.get('ehentai', None)
        if db is None:
            pass
        if db is not None:
            url = self.cached_identifier_to_cover_url(db)
        return url

    # }}}


    def identify(self, log, result_queue, abort, title=None, authors=None, identifiers={}, timeout=30):  # {{{

        is_exhentai = self.ExHentai_Status
        chinese_tags = self.Chinese_Tags
        accurate_label = self.Accurate_Label
        global accurate_url
        #获取将查询信息进行拼接
        query = self.create_query(log, title=title, authors=authors, identifiers=identifiers, is_exhentai=is_exhentai, chinese_tags = chinese_tags)
        if not query:
            log.error('Insufficient metadata to construct query')
            return
        br = self.browser
        br.addheaders = [('User-agent',
                          'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36')]
        if is_exhentai is True:
            for cookie in self.ExHentai_Cookies:
                br.set_cookie(name=cookie['name'], value=cookie['value'], domain=cookie['domain'], path=cookie['path'])



        if not accurate_label:
            try:
                #获取查询结果页面的数据
                _raw = br.open_novisit(query, timeout=timeout)
                raw = _raw.read()
                # print("页面类型：",type(raw))
                raw = raw.decode('unicode_escape')
            except Exception as e:
                log.exception('Failed to make identify query: %r' % query)
                return as_unicode(e)
            if not raw and identifiers and title and authors and not abort.is_set():
                return self.identify(log, result_queue, abort, title=title, authors=authors, timeout=timeout)
            if is_exhentai is True:
                try:
                    'https://exhentai.org/' in raw
                except Exception as e:
                    log.error('The cookies for ExHentai is invalid.')
                    log.error('Exhentai cookies:')
                    log.error(self.ExHentai_Cookies)
                    return

        #得到查询页面结果信息
        gidlist = []
        if accurate_label:
            # 创建应用程序和对象
            app = QtWidgets.QApplication(sys.argv)
            w = QtWidgets.QWidget()
            ui = getUrlUI()
            ui.setUI(w)
            app.exec_()
            #print("获取的数据：", accurate_url)

        if accurate_label:
            pattern = re.compile(
                r'https:\/\/(?:e-hentai\.org|exhentai\.org)\/g\/(?P<gallery_id>\d+)/(?P<gallery_token>\w+)/')
            results = re.findall(pattern, accurate_url)
            if not results:
                log.exception('Failed to get gallery_id and gallery_token!')
                return None
            # print("获取的信息：",results)
            for r in results:
                gidlist.append(list(r))
        else:
            gidlist = self.get_gallery_info(log, raw)

        if not gidlist:
            log.error('No result found.\n', 'query: %s' % query)
            return
        self.get_all_details(gidlist=gidlist, log=log, abort=abort, result_queue=result_queue, timeout=timeout, title = title)
        # }}}







if __name__ == '__main__': # tests {{{
    # To run these test use: calibre-customize -b ehentai_metadata && calibre-debug -e ehentai_metadata/__init__.py
    from calibre.ebooks.metadata.sources.test import (test_identify_plugin,
        title_test, authors_test)

    test_identify_plugin(Ehentai.name,
        [
            (
                {'title': '(C72) [Kabayakiya (Unagimaru)] L&G - Ladies & Gentlemen (CODE GEASS_ Lelouch of the Rebellion) [Chinese] [飞雪汉化组]', 'authors': ['Unknown']},
                [title_test('L&G - Ladies & Gentlemen', exact=False)]
            )
    ])
# }}}

'''
(C72) [Kabayakiya (Unagimaru)] L&G - Ladies & Gentlemen (CODE GEASS_ Lelouch of the Rebellion) [Chinese] [飞雪汉化组]
            (
                {'title': 'キリト君の白くべたつくなにか', 'authors': ['しらたま肉球']},
                [title_test('キリト君の白くべたつくなにか', exact=False)]
            )
            (
                {'title':'拘束する部活動 (僕は友達が少ない)','authors':['すもも堂 (すももEX) ','有条色狼']},
                [title_test('拘束する部活動', exact=False)]
            ),
            (
                {'title':'桜の蜜','authors':['劇毒少女 (ke-ta)']},
                [title_test('桜の蜜', exact=False)]
            )
'''
