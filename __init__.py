#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E-hentai/ExHentai metadata source plugin for Calibre.

Downloads metadata (title, authors, publisher, tags, rating, cover) from
E-hentai.org or ExHentai.org galleries.

Version 3.0.0 - Complete refactoring for Calibre 9.5.0 with modular architecture.
"""

from __future__ import (unicode_literals, division, absolute_import, print_function)

__license__ = 'GPL v3'
__copyright__ = '2026, nonpricklycactus <https://github.com/nonpricklycactus/Ehentai_metadata>'
__docformat__ = 'restructuredtext en'

# Calibre imports
from calibre.ebooks.metadata.sources.base import Source, Option
from calibre.ebooks.metadata.book.base import Metadata
from calibre import as_unicode

# Local module imports - dynamic import to handle both contexts
import sys
import os

def import_local_module(module_name, class_name):
    """Import a class from a local module, handling both plugin and dev contexts."""
    plugin_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Try multiple import strategies
    for strategy in ['absolute', 'relative', 'sys_path']:
        try:
            if strategy == 'absolute':
                # Try absolute import (works in plugin context)
                module = __import__(module_name, fromlist=[class_name])
            elif strategy == 'relative':
                # Try relative import (works when __name__ is set)
                if '__name__' in globals() and globals()['__name__']:
                    parent = globals()['__name__'].rsplit('.', 1)[0] if '.' in globals()['__name__'] else ''
                    fullname = f'{parent}.{module_name}' if parent else module_name
                    module = __import__(fullname, fromlist=[class_name])
                else:
                    continue
            elif strategy == 'sys_path':
                # Try adding plugin dir to sys.path and importing
                if plugin_dir not in sys.path:
                    sys.path.insert(0, plugin_dir)
                module = __import__(module_name, fromlist=[class_name])
            
            return getattr(module, class_name)
        except (ImportError, ValueError, KeyError):
            continue
    
    # If all strategies fail, try a direct file import as last resort
    try:
        import importlib.util
        module_path = os.path.join(plugin_dir, f'{module_name}.py')
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return getattr(module, class_name)
    except Exception as e:
        raise ImportError(f'Failed to import {class_name} from {module_name}: {e}')

# Import all local modules
NetworkClient = import_local_module('net', 'NetworkClient')
ProxyConfig = import_local_module('proxy', 'ProxyConfig')
TranslationService = import_local_module('translation', 'TranslationService')
CustomMetadataClient = import_local_module('protocol', 'CustomMetadataClient')
AccurateLabelDialog = import_local_module('ui', 'AccurateLabelDialog')

# Standard library
import re
import json
import html
import os
import sys
from typing import Dict, List, Set, Union, Optional
from urllib.parse import urlencode

# Image processing - for WebP to JPEG conversion
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# Language mappings for tag parsing
LANGUAGE_DICT = {
    'Chinese': 'chinese',
    'chinese': 'chinese',
    '中国語': 'chinese',
    '中国翻訳': 'chinese',
    '中国語翻訳': 'chinese',
    'Japanese': 'japanese',
    '日語': 'japanese',
    'English': 'english',
    '英訳': 'english',
    'Spanish': 'spanish',
    'French': 'french',
    'Russian': 'russian',
}

OTHER_DICT = {
    'Digital': 'digital',
    'DL版': 'digital',
    'Full Color': 'full color',
    '全彩': 'full color',
    'Uncensored': 'uncensored',
    'Decensored': 'uncensored',
    '無修正': 'uncensored',
}


# ---------------------------------------------------------------------------
# Title parsing
# ---------------------------------------------------------------------------


class FieldFromTitle:
    """Parsed fields extracted from E-hentai gallery title strings."""

    def __init__(
        self,
        title: str,
        author: Optional[str],
        publisher: Optional[str],
        magazine_or_parody: Optional[str],
        additions: List[str],
    ) -> None:
        self.title = title
        self.author = author
        self.publisher = publisher
        self.magazine_or_parody = magazine_or_parody
        self.additions = additions


def _optional(pattern: str) -> str:
    """Wrap *pattern* in a non-capturing optional group."""
    return '(?:' + pattern + ')?'


# Pre-compiled title pattern:
# (publisher) [author] title (magazine_or_parody) [add1] [add2] [add3]
_TITLE_RE = re.compile(
    r'^\s*'
    + _optional(r'\((?P<publisher>[^\(\)]+)\)')
    + r'\s*'
    + _optional(r'\[(?P<author>[^\[\]]+)\]')
    + r'\s*'
    + r'(?P<title>[^\[\]\(\)]+)'
    + r'\s*'
    + _optional(r'\((?P<magazine_or_parody>[^\(\)]+)\)')
    + r'\s*'
    + _optional(r'\[(?P<add1>[^\[\]]+)\]')
    + r'\s*'
    + _optional(r'\[(?P<add2>[^\[\]]+)\]')
    + r'\s*'
    + _optional(r'\[(?P<add3>[^\[\]]+)\]')
)


def extract_field_from_title(title: str, log) -> FieldFromTitle:
    """Parse structured fields out of an E-hentai gallery title.

    Args:
        title: Raw title string from API.
        log: Calibre log object.

    Returns:
        FieldFromTitle with parsed components.
    """
    match = _TITLE_RE.match(title)
    if match:
        add_raw: List[Optional[str]] = [
            match.group('add1'),
            match.group('add2'),
            match.group('add3'),
        ]
        return FieldFromTitle(
            title=match.group('title').strip(),
            author=match.group('author'),
            publisher=match.group('publisher'),
            magazine_or_parody=match.group('magazine_or_parody'),
            additions=[x for x in add_raw if x is not None],
        )
    log.exception('Title regex match failed for: %s' % title)
    return FieldFromTitle(
        title=title,
        author=None,
        publisher=None,
        magazine_or_parody=None,
        additions=[],
    )


def is_subsequence(short: str, long: str) -> bool:
    """Return True if *short* is a subsequence of *long*.

    Used to filter API results by title relevance.

    Args:
        short: The shorter string to search for.
        long: The longer string to search in.

    Returns:
        True if all chars of *short* appear in *long* in order.
    """
    it = iter(long)
    return all(ch in it for ch in short)


# ---------------------------------------------------------------------------
# Metadata conversion
# ---------------------------------------------------------------------------


def to_metadata(gmetadata: Dict, log) -> Metadata:
    """Convert E-hentai API response dict to Calibre Metadata object.

    Args:
        gmetadata: Gallery metadata dict from API.
        log: Calibre log object.

    Returns:
        Calibre Metadata instance.
    """
    title = gmetadata.get('title', '')
    title_jpn = gmetadata.get('title_jpn', '')
    tags = gmetadata.get('tags', [])
    rating = gmetadata.get('rating', 0.0)
    category = gmetadata.get('category', '')
    gid = gmetadata.get('gid', 0)
    token = gmetadata.get('token', '')
    thumb = gmetadata.get('thumb', '')

    # Parse title structure
    has_jpn = bool(title_jpn)
    parsed = extract_field_from_title(title_jpn if has_jpn else title, log)

    # Build Metadata
    mi = Metadata(parsed.title, [parsed.author or 'Unknown'])
    mi.identifiers = {'ehentai': f'{gid}_{token}_0'}
    mi.publisher = parsed.publisher or 'Unknown'

    # Process tags
    tags_set: Set[str] = set()
    languages: Set[str] = set()
    is_parody = False

    for tag in tags:
        tags_set.add(tag)
        if tag.startswith('language:'):
            lang = tag.replace('language:', '', 1)
            if lang != 'translated':
                languages.add(lang)
        elif tag.startswith('parody:'):
            is_parody = True

    tags_set.add(f'category:{category}')

    # Add magazine tag if not parody
    if not is_parody and parsed.magazine_or_parody:
        tags_set.add(f'magazine:{parsed.magazine_or_parody}')

    # Process additions from both titles
    all_additions = parsed.additions
    if has_jpn:
        all_additions += extract_field_from_title(title, log).additions

    for add in all_additions:
        if add in OTHER_DICT:
            tags_set.add(f'other:{OTHER_DICT[add]}')
        elif add in LANGUAGE_DICT:
            lang_tag = LANGUAGE_DICT[add]
            tags_set.add(f'language:{lang_tag}')
            languages.add(lang_tag)
        else:
            # Skip date patterns
            if not re.match(r'^\d{4}[-年]\d{1,2}', add):
                tags_set.add(f'translator:{add}')

    # Default language for Japanese titles
    if not languages and has_jpn:
        languages.add('japanese')

    mi.tags = list(tags_set)
    mi.languages = list(languages)
    mi.rating = float(rating)
    
    # Process cover URL
    if thumb:
        # E-hentai API returns thumbnail URLs
        # Common patterns:
        # - https://ehgt.org/t/12/34/1234567890abcd.jpg
        # - https://exhentai.org/t/12/34/1234567890abcd.jpg
        # - Other CDN domains
        
        # For now, use the thumbnail URL as-is
        # Thumbnail URLs are usually accessible with proper headers
        mi.has_ehentai_cover = thumb
        log.info(f'Cover URL from API: {thumb}')
    else:
        mi.has_ehentai_cover = None

    return mi


def custom_result_to_metadata(custom_result: Dict, log) -> Metadata:
    """Convert custom metadata server response to Calibre Metadata object.
    
    Args:
        custom_result: Result dict from custom metadata server.
        log: Calibre log object.
    
    Returns:
        Calibre Metadata instance.
    """
    title = custom_result.get('title', '')
    authors = custom_result.get('authors', [])
    publisher = custom_result.get('publisher', '')
    tags = custom_result.get('tags', [])
    rating = custom_result.get('rating', 0.0)
    cover_url = custom_result.get('cover_url', '')
    identifiers = custom_result.get('identifiers', {})
    
    # Build Metadata
    mi = Metadata(title, authors if authors else ['Unknown'])
    mi.publisher = publisher or 'Unknown'
    mi.tags = tags
    mi.rating = float(rating)
    
    # Set identifiers (preserve ehentai identifier if present)
    if identifiers:
        mi.identifiers = identifiers
    elif 'ehentai' in custom_result:
        # Fallback for old format
        mi.identifiers = {'ehentai': custom_result['ehentai']}
    
    # Set cover URL if available
    if cover_url:
        mi.has_ehentai_cover = cover_url
    
    return mi


# ---------------------------------------------------------------------------
# Main plugin class
# ---------------------------------------------------------------------------


class Ehentai(Source):
    """E-hentai/ExHentai metadata source plugin for Calibre."""

    name = 'E-hentai Galleries'
    author = 'nonpricklycactus'
    version = (3, 0, 0)
    minimum_calibre_version = (9, 0, 0)
    description = _('Download metadata and covers from E-hentai.org or ExHentai.org')

    capabilities = frozenset(['identify', 'cover'])
    touched_fields = frozenset([
        'title', 'authors', 'tags', 'rating', 'publisher', 'identifier:ehentai'
    ])
    supports_gzip_transfer_encoding = True
    cached_cover_url_is_reliable = True

    # API endpoints
    EHENTAI_URL = 'https://e-hentai.org/g/%s/%s/'
    EXHENTAI_URL = 'https://exhentai.org/g/%s/%s/'
    API_URL = 'https://api.e-hentai.org/api.php'

    options = (
        Option('use_exhentai', 'bool', False,
               _('Use ExHentai'),
               _('Search ExHentai instead of E-hentai (requires cookies)')),
        Option('translate_tags', 'bool', False,
               _('Translate tags to Chinese'),
               _('Fetch translations from EhTagTranslation GitHub repository')),
        Option('accurate_label', 'bool', False,
               _('Accurate label mode'),
               _('Get metadata from specific URL (paste URL in title field)')),
        Option('use_custom_metadata', 'bool', False,
               _('Enable custom metadata server'),
               _('Use third-party metadata server when enabled')),
        Option('custom_metadata_url', 'string', None,
               _('Custom metadata server URL'),
               _('Optional: URL of custom metadata server endpoint')),
        Option('custom_metadata_token', 'string', None,
               _('Custom metadata auth token'),
               _('Optional: Bearer token or Basic auth for custom server')),
        Option('use_proxy', 'bool', False,
               _('Use proxy'),
               _('Enable proxy for all requests')),
        Option('proxy_url', 'string', None,
               _('Proxy URL'),
               _('Format: [user:pass@]host:port or http://host:port')),
        Option('ipb_member_id', 'string', None,
               _('ExHentai cookie: ipb_member_id'),
               _('Required for ExHentai access')),
        Option('ipb_pass_hash', 'string', None,
               _('ExHentai cookie: ipb_pass_hash'),
               _('Required for ExHentai access')),
        Option('igneous', 'string', None,
               _('ExHentai cookie: igneous'),
               _('Required for ExHentai access')),
    )

    def __init__(self, *args, **kwargs):
        Source.__init__(self, *args, **kwargs)
        self._init_services()

    def _get_cache_directory(self) -> str:
        """Get cache directory path, handling both development and plugin runtime.
        
        When plugin runs from ZIP file, we need to use a writable directory.
        """
        import os
        import tempfile
        
        # Get the plugin path from Calibre's Plugin base class
        # self.plugin_path is set by Calibre when plugin is loaded
        if hasattr(self, 'plugin_path') and self.plugin_path:
            # Plugin is running from ZIP file - use Calibre's config directory
            try:
                from calibre.utils.config import config_dir
                plugin_cache_dir = os.path.join(config_dir, 'plugins', 'Ehentai_metadata', 'cache')
                os.makedirs(plugin_cache_dir, exist_ok=True)
                return plugin_cache_dir
            except ImportError:
                # Fallback to temp directory for testing
                temp_dir = os.path.join(tempfile.gettempdir(), 'calibre_ehentai_cache')
                os.makedirs(temp_dir, exist_ok=True)
                return temp_dir
        else:
            # Development mode or plugin_path not set - use .cache in plugin directory
            file_path = os.path.abspath(__file__)
            cache_dir = os.path.join(os.path.dirname(file_path), '.cache')
            os.makedirs(cache_dir, exist_ok=True)
            return cache_dir

    def _init_services(self):
        """Initialize all service modules."""
        # Network client with rate limiting
        self.net = NetworkClient(self.browser, rate_limit_seconds=5.0)
        
        # Proxy configuration
        proxy_url = self.prefs.get('proxy_url')
        self.proxy_config = ProxyConfig(proxy_url)
        
        # Translation service (log injected later)
        # Get cache directory - handle both development and plugin runtime
        cache_dir = self._get_cache_directory()
        self.translation = TranslationService(cache_dir, log=None)
        
        # Custom metadata client (log injected later)
        custom_url = self.prefs.get('custom_metadata_url')
        custom_token = self.prefs.get('custom_metadata_token')
        self.custom_client = CustomMetadataClient(custom_url, custom_token, log=None)
        
        # ExHentai cookies
        self.exhentai_cookies = self._build_exhentai_cookies()

    def _convert_cover_to_jpeg(self, image_data: bytes, log) -> bytes:
        """Convert cover image to JPEG format for Calibre compatibility.
        
        Calibre requires JPEG format for covers. This function:
        1. Detects if image is WebP or other non-JPEG format
        2. Converts to JPEG using PIL if available
        3. Preserves image quality while ensuring compatibility
        
        Args:
            image_data: Raw image bytes
            log: Calibre log object for debugging
            
        Returns:
            JPEG image bytes (converted if needed, original if already JPEG or conversion fails)
        """
        if not image_data:
            return image_data
            
        # Check if already JPEG by magic bytes
        if len(image_data) >= 2 and image_data[:2] == b'\xff\xd8':
            log.info('Cover image is already JPEG format')
            return image_data
            
        if not PIL_AVAILABLE:
            log.warning('PIL/Pillow not available, cannot convert non-JPEG cover images')
            return image_data
            
        try:
            from io import BytesIO
            
            # Open image with PIL
            img = Image.open(BytesIO(image_data))
            original_format = img.format
            original_size = img.size
            
            log.info(f'Cover image format: {original_format}, size: {original_size}')
            
            # Check if conversion is needed
            if original_format == 'JPEG':
                log.info('Cover is already JPEG, no conversion needed')
                return image_data
                
            log.info(f'Converting cover from {original_format} to JPEG...')
            
            # Handle different image modes
            if img.mode in ('RGBA', 'LA', 'P'):
                # Convert transparent images to RGB with white background
                if img.mode == 'RGBA':
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[3] if img.mode == 'RGBA' else None)
                    img = background
                else:
                    img = img.convert('RGB')
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Save as JPEG
            output = BytesIO()
            img.save(output, format='JPEG', quality=85, optimize=True)
            jpeg_data = output.getvalue()
            
            log.info(f'Cover conversion complete: {len(image_data)} → {len(jpeg_data)} bytes')
            return jpeg_data
            
        except Exception as e:
            log.warning(f'Failed to convert cover image: {e}')
            # Return original data as fallback
            return image_data
        
    def _build_exhentai_cookies(self) -> List[Dict]:
        """Build ExHentai cookie list from preferences."""
        if not self.prefs.get('use_exhentai'):
            return []
        
        cookies = [
            {'name': 'ipb_member_id', 'value': self.prefs.get('ipb_member_id'),
             'domain': '.exhentai.org', 'path': '/'},
            {'name': 'ipb_pass_hash', 'value': self.prefs.get('ipb_pass_hash'),
             'domain': '.exhentai.org', 'path': '/'},
            {'name': 'igneous', 'value': self.prefs.get('igneous'),
             'domain': '.exhentai.org', 'path': '/'},
        ]
        
        # Validate all cookies present
        if any(c['value'] is None for c in cookies):
            return []
        
        return cookies

    def identify(self, log, result_queue, abort, title=None, authors=None, 
                 identifiers=None, timeout=30):
        """Main entry point for metadata identification."""
        # Inject log into services
        self.translation.log = log
        self.custom_client.log = log
        
        identifiers = identifiers or {}
        use_exhentai = bool(self.exhentai_cookies)
        
        # Accurate label mode - get URL from title field
        gallery_url = None
        if self.prefs.get('accurate_label'):
            # In accurate label mode, the title field should contain the E-hentai URL
            import re
            url_pattern = re.compile(r'https?://(?:e-hentai\.org|exhentai\.org)/g/\d+/[a-f0-9]+/?')
            
            if title and url_pattern.match(title.strip()):
                gallery_url = title.strip()
                log.info(f'Accurate label mode: Using URL from title field: {gallery_url}')
            else:
                # Title is not a valid E-hentai URL
                log.error('Accurate label mode is enabled but title is not a valid E-hentai URL.')
                log.error('Please paste the E-hentai gallery URL into the title field.')
                log.error('Example: https://e-hentai.org/g/1234567/abcdef123456/')
                log.error('Or disable accurate label mode to use normal search.')
                return  # Exit early since we can't proceed without a valid URL
        
        # Priority 1: Custom Metadata Server (if enabled and configured)
        custom_results = []
        if (self.prefs.get('use_custom_metadata') and 
            self.custom_client.enabled and 
            self.custom_client.endpoint):
            try:
                custom_results = self.custom_client.search(
                    self.browser,
                    title=title,
                    authors=authors,
                    identifiers=identifiers,
                    timeout=timeout
                )
                if custom_results:
                    log.info(f'Custom metadata server returned {len(custom_results)} results')
            except Exception as e:
                log.error(f'Custom metadata server failed: {e}')
        
        # If custom server returned results, use them and skip E-hentai/ExHentai
        if custom_results:
            for result in custom_results:
                try:
                    mi = custom_result_to_metadata(result, log)
                    result_queue.put(mi)
                except Exception as e:
                    log.error(f'Failed to convert custom result: {e}')
            return  # Skip E-hentai/ExHentai search
        
        # Build search query or use provided URL
        if gallery_url:
            raw_html = gallery_url
        else:
            query_url = self._build_search_url(title, authors, use_exhentai)
            if not query_url:
                log.error('Insufficient metadata to construct query')
                return
            
            try:
                resp = self.net.request(
                    query_url,
                    proxy=self.proxy_config.get_proxy_dict(),
                    cookies=self.exhentai_cookies,
                    timeout=timeout,
                    abort=abort
                )
                raw_html = resp.read().decode('unicode_escape')
            except Exception as e:
                log.error(f'Search request failed: {e}')
                return
        
        # Extract gallery IDs
        gidlist = self._extract_gallery_ids(raw_html, log)
        if not gidlist:
            log.error('No galleries found in search results')
            return
        
        # Fetch detailed metadata
        self._fetch_all_details(gidlist, log, abort, result_queue, timeout, title or '')

    def _build_search_url(self, title, authors, use_exhentai):
        """Build E-hentai search URL from title/authors."""
        if not title:
            return None
        
        tokens = list(self.get_title_tokens(title))
        if not tokens:
            return None
        
        query = ' '.join(tokens)
        if 'chinese' in query.lower() or '汉化' in query or '中国' in query:
            query += ' l:chinese'
        
        base = 'https://exhentai.org/?' if use_exhentai else 'https://e-hentai.org/?'
        params = {'f_cats': 0, 'f_search': query.encode('utf-8')}
        return base + urlencode(params)

    def _extract_gallery_ids(self, html, log):
        """Extract gallery ID/token pairs from search results HTML."""
        pattern = re.compile(
            r'https://(?:e-hentai\.org|exhentai\.org)/g/(\d+)/([a-f0-9]+)/'
        )
        matches = pattern.findall(html)
        return [[int(gid), token] for gid, token in matches] if matches else []

    def _fetch_all_details(self, gidlist, log, abort, result_queue, timeout, title):
        """Fetch detailed metadata from E-hentai API."""
        payload = {
            'method': 'gdata',
            'gidlist': gidlist[:25],  # API limit: 25 per request
            'namespace': 1
        }
        
        try:
            resp = self.net.request(
                self.API_URL,
                method='POST',
                data=json.dumps(payload).encode('utf-8'),
                proxy=self.proxy_config.get_proxy_dict(),
                timeout=timeout,
                abort=abort
            )
            data = json.loads(resp.read())
            gmetadatas = data.get('gmetadata', [])
        except Exception as e:
            log.error(f'API request failed: {e}')
            return
        
        # Filter by title relevance
        if title:
            filtered = []
            for gm in gmetadatas:
                title_jpn = html.unescape(gm.get('title_jpn', ''))
                if is_subsequence(title, title_jpn):
                    filtered.append(gm)
            if filtered:
                gmetadatas = filtered
        
        # Convert to Metadata objects
        for relevance, gm in enumerate(gmetadatas):
            if abort.is_set():
                break
            
            try:
                mi = to_metadata(gm, log)
                mi.source_relevance = relevance
                
                # Apply translation if enabled
                if self.prefs.get('translate_tags'):
                    if not self.translation._loaded:
                        self.translation.load(
                            self.browser,
                            self.proxy_config.get_proxy_dict()
                        )
                    self.translation.translate(mi)
                
                # Cache cover URL
                if mi.has_ehentai_cover:
                    identifier = mi.identifiers.get('ehentai')
                    cover_url = mi.has_ehentai_cover
                    if identifier and cover_url:
                        log.info(f'Caching cover URL: {cover_url} for identifier: {identifier}')
                        self.cache_identifier_to_cover_url(identifier, cover_url)
                    else:
                        log.warning(f'Cannot cache cover: identifier={identifier}, cover_url={cover_url}')
                
                result_queue.put(mi)
            except Exception as e:
                log.exception(f'Failed to process metadata: {e}')

    def download_cover(self, log, result_queue, abort, title=None, authors=None,
                       identifiers=None, timeout=30, get_best_cover=False):
        """Download cover image for identified book."""
        identifiers = identifiers or {}
        cached_url = self.get_cached_cover_url(identifiers)
        
        log.info(f'Cover download: identifiers={identifiers}')
        log.info(f'Cover download: cached_url={cached_url}')
        
        if cached_url is None:
            log.warning('Cover download: No cached URL found')
            return
        
        if abort.is_set():
            log.warning('Cover download: Abort signal received')
            return
        
        try:
            log.info(f'Cover download: Attempting to download from {cached_url}')
            
            # Check if we need ExHentai cookies
            cookies = []
            # ExHentai cookies are needed for:
            # 1. exhentai.org URLs (galleries)
            # 2. ehgt.org URLs (image CDN used by ExHentai)
            # 3. Other ExHentai CDN domains
            if self.exhentai_cookies:
                # Check if this URL likely requires ExHentai cookies
                requires_cookies = (
                    'exhentai.org' in cached_url or 
                    'ehgt.org' in cached_url or
                    # Check if this is from an ExHentai gallery (identifier ends with _1)
                    (identifiers.get('ehentai', '').endswith('_1'))
                )
                
                if requires_cookies:
                    cookies = self.exhentai_cookies
                    log.info(f'Cover download: Using ExHentai cookies for {cached_url}')
                    log.info(f'Cover download: Identifier suggests ExHentai: {identifiers.get("ehentai", "")}')
            
            # E-hentai image servers may require specific headers
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': 'https://e-hentai.org/' if 'e-hentai.org' in cached_url else 'https://exhentai.org/'
            }
            
            resp = self.net.request(
                cached_url,
                proxy=self.proxy_config.get_proxy_dict(),
                cookies=cookies,
                headers=headers,
                timeout=timeout,
                abort=abort
            )
            
            log.info(f'Cover download: Response received, status: {getattr(resp, "getcode", lambda: "unknown")()}')
            
            cdata = resp.read()
            if cdata:
                log.info(f'Cover download: Successfully downloaded {len(cdata)} bytes')
                
                # Convert WebP or other non-JPEG formats to JPEG for Calibre compatibility
                converted_cdata = self._convert_cover_to_jpeg(cdata, log)
                if converted_cdata is not cdata:
                    log.info(f'Cover format converted: {len(cdata)} → {len(converted_cdata)} bytes')
                    cdata = converted_cdata
                
                result_queue.put((self, cdata))
            else:
                log.warning('Cover download: No data received')
                
        except Exception as e:
            log.exception(f'Failed to download cover from {cached_url}: {e}')
            # Add more detailed error information
            import traceback
            log.error(f'Cover download error traceback: {traceback.format_exc()}')
            
            # Try alternative method: get cover from gallery page
            # This is a fallback if direct thumbnail download fails
            self._try_alternative_cover_download(log, result_queue, abort, identifiers, timeout)

    def get_cached_cover_url(self, identifiers: Dict) -> Optional[str]:
        """Retrieve cached cover URL from identifier."""
        db = identifiers.get('ehentai')
        if db:
            return self.cached_identifier_to_cover_url(db)
        return None

    def get_book_url(self, identifiers: Dict):
        """Reconstruct gallery URL from identifier."""
        db = identifiers.get('ehentai')
        if not db:
            return None
        parts = db.split('_')
        if len(parts) < 3:
            return None
        gid, token, exhentai_flag = parts[0], parts[1], parts[2]
        if exhentai_flag == '1':
            url = self.EXHENTAI_URL % (gid, token)
        else:
            url = self.EHENTAI_URL % (gid, token)
        return ('ehentai', db, url)
    
    def _process_cover_url(self, thumb_url: str, log) -> str:
        """Process and validate cover URL from E-hentai API.
        
        Args:
            thumb_url: Thumbnail URL from API
            log: Calibre log object
            
        Returns:
            Processed cover URL
        """
        if not thumb_url:
            return ''
        
        # Common E-hentai thumbnail URL patterns
        # 1. https://ehgt.org/t/12/34/1234567890abcd.jpg
        # 2. https://exhentai.org/t/12/34/1234567890abcd.jpg
        # 3. Other CDN domains
        
        # For now, return the URL as-is
        # In the future, we might need to:
        # 1. Convert thumbnail URL to full-size URL
        # 2. Handle different CDN domains
        # 3. Add referrer headers
        
        log.info(f'Processing cover URL: {thumb_url}')
        return thumb_url
    
    def _try_alternative_cover_download(self, log, result_queue, abort, identifiers, timeout):
        """Try alternative method to download cover if direct download fails.
        
        This method attempts to:
        1. Get the gallery URL from identifiers
        2. Fetch the gallery page
        3. Extract cover image URL from page
        4. Download the cover
        """
        try:
            log.info('Attempting alternative cover download method')
            
            # Get gallery URL from identifiers
            book_url_info = self.get_book_url(identifiers)
            if not book_url_info:
                log.warning('Alternative method: Cannot get gallery URL from identifiers')
                return
            
            _, _, gallery_url = book_url_info
            log.info(f'Alternative method: Gallery URL: {gallery_url}')
            
            # Check if we need ExHentai cookies
            cookies = []
            if 'exhentai.org' in gallery_url and self.exhentai_cookies:
                cookies = self.exhentai_cookies
            
            # Fetch gallery page
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9'
            }
            
            resp = self.net.request(
                gallery_url,
                proxy=self.proxy_config.get_proxy_dict(),
                cookies=cookies,
                headers=headers,
                timeout=timeout,
                abort=abort
            )
            
            html_content = resp.read().decode('utf-8', errors='ignore')
            
            # Try to extract cover image URL from page
            # Look for og:image meta tag or cover image in HTML
            import re
            
            # Pattern 1: og:image meta tag
            og_image_pattern = r'<meta\s+property="og:image"\s+content="([^"]+)"'
            match = re.search(og_image_pattern, html_content)
            
            if not match:
                # Pattern 2: img tag with id="img"
                img_pattern = r'<img[^>]*id="img"[^>]*src="([^"]+)"'
                match = re.search(img_pattern, html_content)
            
            if not match:
                # Pattern 3: First image in the gallery
                img_pattern = r'<img[^>]*src="(https?://[^"]+\.(?:jpg|jpeg|png|gif|webp))"[^>]*>'
                match = re.search(img_pattern, html_content)
            
            if match:
                cover_url = match.group(1)
                log.info(f'Alternative method: Found cover URL: {cover_url}')
                
                # Download the cover
                resp = self.net.request(
                    cover_url,
                    proxy=self.proxy_config.get_proxy_dict(),
                    cookies=cookies,
                    headers=headers,
                    timeout=timeout,
                    abort=abort
                )
                
                cdata = resp.read()
                if cdata:
                    log.info(f'Alternative method: Successfully downloaded {len(cdata)} bytes')
                    result_queue.put((self, cdata))
                    return
            
            log.warning('Alternative method: Could not find cover image in gallery page')
            
        except Exception as e:
            log.error(f'Alternative cover download failed: {e}')


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    from calibre.ebooks.metadata.sources.test import (
        test_identify_plugin, title_test, authors_test
    )

    test_identify_plugin(Ehentai.name, [
        (
            {'title': 'https://exhentai.org/g/3852759/28339df42d/', 'authors': ['すもも堂']},
            [title_test('拘束する部活動', exact=False)]
        ),
        (
            {'title': '桜の蜜', 'authors': ['劇毒少女 (ke-ta)']},
            [title_test('桜の蜜', exact=False)]
        ),
    ])
