#!/usr/bin/env python3
# vim:fileencoding=UTF-8:ts=4:sw=4:sta:et:sts=4:ai
from __future__ import (unicode_literals, division, absolute_import,
                        print_function)

__license__   = 'GPL v3'
__copyright__ = '2021, nonpricklycactus <https://github.com/nonpricklycactus/Ehentai_metadata>'
__docformat__ = 'restructuredtext en'

from calibre.ebooks.metadata.sources.base import Source, Option
from calibre.ebooks.metadata.book.base import Metadata
from calibre import as_unicode

import re
import json
import sqlite3
from urllib.parse import urlencode


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
            print("language:",language)
            Newlanguage = findName(c,"SELECT name from language WHERE raw like '%{raw}%'".format(raw=language),language)
            languages[i] = Newlanguage.replace(" ", "")
            i=i+1
        gmetadata.languages = languages

    for tag in gmetadata.tags:
        j = 0
        taglist = tag.split(":")
        tableName = getName(taglist,0)
        nameSpace = findName(c,"SELECT name from rows WHERE key like '%{key}%'".format(key=tableName),tableName)
        if tableName == "group":
            tableName = "groups"
        raws = getName(taglist,1).split(",")
        if len(taglist) == 1:
            comment = "SELECT name from reclass WHERE raw like '%{raw}%'".format(raw=taglist[0])
            Newtag = findName(c, comment, taglist[0])
            Newtag = Newtag.replace(" ", "")
            tranTag.append(Newtag)
            continue
        for raw in raws:
            comment = "SELECT name from {table} WHERE raw like '%{raw}%'".format(table=tableName, raw=raw)
            Newtag = findName(c,comment,raw)
            Newtag = Newtag.replace(" ","")
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


def to_metadata(log, gmetadata, ExHentai_Status, Chinese_Status,sqlitUrl):  # {{{
    title = gmetadata['title']
    title_jpn = gmetadata['title_jpn']
    tags = gmetadata['tags']
    rating = gmetadata['rating']
    category = gmetadata['category']
    gid = gmetadata['gid']
    token = gmetadata['token']
    thumb = gmetadata['thumb']

    # title
    if title_jpn:
        raw_title = title_jpn
    else:
        raw_title = title
    pat1 = re.compile(
        r'(?P<comments>.*?\[(?P<author>(?:(?!汉化|漢化)[^\[\]])*)\](?:\s*(?:\[[^\(\)]+\]|\([^\[\]\(\)]+\))\s*)*(?P<title>[^\[\]\(\)]+).*)')
    if re.findall(pat1, raw_title):
        m = re.search(pat1, raw_title)
        title_ = m.group('title').strip()
        author = m.group('author').strip()
    else:
        title_ = raw_title.strip()
        author = 'Unknown'
        log.exception('Title match failed. Title is %s' % raw_title)

    authors = [(author)]

    mi = Metadata(title_, authors)
    mi.identifiers = {'ehentai': '%s_%s_%d' % (str(gid), str(token), int(ExHentai_Status))}

    # publisher
    pat2 = re.compile(r'^\(([^\[\]\(\)]*)\)')
    if re.findall(pat2, raw_title):
        publisher = re.search(pat2, raw_title).group(1).strip()
        mi.publisher = publisher
    else:
        mi.publisher = 'Unknown'
        log.exception('Not Found publisher.')

    # Tags
    tags_ = []
    for tag in tags:
        if re.match('language', tag):
            tag_ = re.sub('language:', '', tag)
            if tag_ != 'translated':
                mi.language = tag_
            else:
                tags_.append(tag_)
                #         elif re.match('parody|group|character|artist', tag):
                #             log('drop tag %s' % tag)
                #             continue
        elif not ':' in tag:
            log('drop tag %s' % tag)
            continue
        else:
            tags_.append(tag)

    tags_.append(category)
    mi.tags = tags_

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


class Ehentai(Source):
    name = 'E-hentai Galleries'
    author = 'nonpricklycactus'
    version = (2, 2, 0)
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
        Option('ipb_member_id', 'string', None, _('ipb_member_id'),
               _('If Use Exhentai is True, please input your cookies.')),
        Option('ipb_pass_hash', 'string', None, _('ipb_pass_hash'),
               _('If Use Exhentai is True, please input your cookies.')),
        Option('EhTagTranslation_db', 'string', None, _('EhTagTranslation_db'),
               _('Translate the location of the database files(翻译数据库文件所在位置)'))
    )

    config_help_message = ('<p>' + _('To Download Metadata from exhentai.org you must sign up'
                                     ' a free account and get the cookies of .exhentai.org.'
                                     ' If you don\'t have an account, you can <a href="%s">sign up</a>.')) % 'https://forums.e-hentai.org/index.php'

    def __init__(self, *args, **kwargs):  # {{{
        Source.__init__(self, *args, **kwargs)
        self.config_exhentai()
        self.config_chinese()

    # }}}

    def config_chinese(self):
        self.Chinese_Status = self.prefs['Chinese_Exhentai']
        EhTagTranslation_db = self.prefs['EhTagTranslation_db']
        if self.Chinese_Status is True:
            self.sqlitUrl = EhTagTranslation_db + "\EhTagTranslation.db"
        return

    def config_exhentai(self):  # {{{

        ExHentai_Status = self.prefs['Use_Exhentai']
        ExHentai_Cookies = [
            {'name': 'ipb_member_id', 'value': self.prefs['ipb_member_id'], 'domain': '.exhentai.org', 'path': '/'},
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

    def create_query(self, log, title=None, authors=None, identifiers={}, is_exhentai=False):  # {{{

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
        q = q.strip()
        if isinstance(q, str):
            q = q.encode('utf-8')
        if not q:
            return None
        q_dict = {'f_doujinshi': 1, 'f_manga': 1, 'f_artistcg': 1, 'f_gamecg': 1, 'f_western': 1, 'f_non-h': 1,
                  'f_imageset': 1, 'f_cosplay': 1, 'f_asianporn': 1, 'f_misc': 1, 'f_search': q,
                  'f_apply': 'Apply+Filter',
                  'advsearch': 1, 'f_sname': 'on', 'f_sh': 'on', 'f_srdd': 2}
        if is_exhentai is False:
            url = EHentai_SEARCH_URL + urlencode(q_dict)
        else:
            url = ExHentai_SEARCH_URL + urlencode(q_dict)
        return url

    # }}}

    def get_gallery_info(self, log, raw):  # {{{

        pattern = re.compile(
            r'https:\/\/(?:e-hentai\.org|exhentai\.org)\/g\/(?P<gallery_id>\d+)/(?P<gallery_token>\w+)/')
        results = re.findall(pattern, raw)
        if not results:
            log.exception('Failed to get gallery_id and gallery_token!')
            return None
        gidlist = []
        for r in results:
            gidlist.append(list(r))
        return gidlist

    # }}}

    def get_all_details(self, gidlist, log, abort, result_queue, timeout):  # {{{

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
        for relevance, gmetadata in enumerate(gmetadatas):
            try:
                ans = to_metadata(log, gmetadata, self.ExHentai_Status,self.Chinese_Status,self.sqlitUrl)
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
        # print("里站状态",is_exhentai)
        query = self.create_query(log, title=title, authors=authors, identifiers=identifiers, is_exhentai=is_exhentai)
        if not query:
            log.error('Insufficient metadata to construct query')
            return
        br = self.browser
        br.addheaders = [('User-agent',
                          'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36')]
        if is_exhentai is True:
            for cookie in self.ExHentai_Cookies:
                br.set_cookie(name=cookie['name'], value=cookie['value'], domain=cookie['domain'], path=cookie['path'])
        try:
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
        gidlist = self.get_gallery_info(log, raw)
        if not gidlist:
            log.error('No result found.\n', 'query: %s' % query)
            return
        self.get_all_details(gidlist=gidlist, log=log, abort=abort, result_queue=result_queue, timeout=timeout)
        # }}}







if __name__ == '__main__': # tests {{{
    # To run these test use: calibre-customize -b ehentai_metadata && calibre-debug -e ehentai_metadata/__init__.py
    from calibre.ebooks.metadata.sources.test import (test_identify_plugin,
        title_test, authors_test)

    test_identify_plugin(Ehentai.name,
        [
            (
                {'title': 'キリト君の白くべたつくなにか', 'authors':['しらたま肉球']},
                [title_test('キリト君の白くべたつくなにか', exact=False)]
            ),
            (
                {'title':'拘束する部活動 (僕は友達が少ない)','authors':['すもも堂 (すももEX) ','有条色狼']},
                [title_test('拘束する部活動', exact=False)]
            ),
            (
                {'title':'桜の蜜','authors':['劇毒少女 (ke-ta)']},
                [title_test('桜の蜜', exact=False)]
            )
    ])
# }}}