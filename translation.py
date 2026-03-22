#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Translation service using GitHub EhTagTranslation database.

Fetches db.text.json.gz from EhTagTranslation/DatabaseReleases mirror,
caches it locally for 24 hours using ETag-based conditional requests,
and provides namespace-keyed tag lookup (e.g. 'female:glasses' -> '眼镜').

Calibre's browser stack (not requests) is used so proxy/SSL settings are
inherited automatically.
"""

from __future__ import (unicode_literals, division, absolute_import, print_function)

import gzip
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

__license__ = 'GPL v3'
__copyright__ = '2026, nonpricklycactus'

# Direct raw URL to the DatabaseReleases mirror.
# This file auto-syncs from the main Database repo via GitHub Actions
# and is always up-to-date with the latest release.
_RELEASE_URL = (
    'https://raw.githubusercontent.com/EhTagTranslation/DatabaseReleases/'
    'master/db.text.json.gz'
)
_CACHE_TTL_HOURS = 24

# Namespaces that map to specific Calibre fields rather than tags.
_NS_AUTHORS = 'artist'
_NS_PUBLISHER = 'group'
_NS_LANGUAGE = 'language'

# Calibre language code mapping for EhTagTranslation language tags.
_CALIBRE_LANGUAGE: Dict[str, str] = {
    '中文': '中文',
    '朝鲜语': '朝鲜语',
    '日语': '日语',
    '英语': '英语',
    '俄语': '俄语',
}

# Namespace mapping for E-hentai tags that don't have direct equivalents
# in the EhTagTranslation database.
_NAMESPACE_MAPPING: Dict[str, str] = {
    # E-hentai uses 'category' but EhTagTranslation uses 'reclass'
    'category': 'reclass',
    # Other potential mappings
    'parody': 'parody',
    'character': 'character',
    'group': 'group',
    'artist': 'artist',
    'female': 'female',
    'male': 'male',
    'mixed': 'mixed',
    'other': 'other',
    'cosplayer': 'cosplayer',
    'location': 'location',
    'language': 'language',
    # Namespaces with hardcoded translations
    'translator': 'translator',
    'digital': 'digital',
    # Default fallback for unknown namespaces
}

# Hardcoded translations for namespaces not in the EhTagTranslation database
_HARDCODED_TRANSLATIONS: Dict[str, Dict[str, str]] = {
    'rows': {
        'translator': '翻译',
        'digital': '数字',
    },
    'translator': {
        # Common translation groups
        'ehnd': 'EHND',
        'c.c': 'C.C',
        'fakku': 'Fakku',
        'irodori': 'Irodori',
        'project-h': 'Project-H',
    },
    'digital': {
        'version': '版本',
        'original': '原版',
        'scan': '扫描版',
        'web': '网页版',
        'digital': '数字版',
    },
}


def _parse_db(raw_json: bytes) -> Dict[str, Dict[str, str]]:
    """Parse db.text.json into {namespace: {raw_tag: translated_name}}.

    The EhTagTranslation db.text.json structure is::

        {
          "data": [
            { "namespace": "female",
              "data": { "glasses": { "name": "眼镜", ... }, ... } },
            ...
          ]
        }

    Args:
        raw_json: Raw bytes of the JSON file (already decompressed).

    Returns:
        Nested dict: namespace -> raw_tag -> translated_name.
    """
    result: Dict[str, Dict[str, str]] = {}
    root = json.loads(raw_json.decode('utf-8'))
    for ns_block in root.get('data', []):
        ns = ns_block.get('namespace', '')
        ns_data = ns_block.get('data', {})
        mapping: Dict[str, str] = {}
        for raw_tag, tag_info in ns_data.items():
            name = tag_info.get('name', '') if isinstance(tag_info, dict) else str(tag_info)
            if name:
                mapping[raw_tag] = name
        result[ns] = mapping
    return result


class TranslationService:
    """Fetches and caches tag translations from EhTagTranslation on GitHub.

    Usage::

        svc = TranslationService(cache_dir, log)
        svc.load()               # loads from cache or fetches from GitHub
        svc.translate(mi)        # mutates Calibre Metadata object in-place
        svc.force_refresh()      # ignores 24 h TTL and re-fetches

    The cache is stored as JSON in *cache_dir*. Writes are atomic (tmp -> rename)
    so a crashed mid-write never corrupts the existing cache.
    """

    def __init__(self, cache_dir: str, log=None):
        """Initialize the translation service.

        Args:
            cache_dir: Directory for cache files (created if absent).
            log: Calibre log object (optional, injected later if None).
        """
        self.cache_dir = cache_dir
        self.log = log
        self.cache_file = os.path.join(cache_dir, 'translation_cache.json')
        self._ttl = timedelta(hours=_CACHE_TTL_HOURS)
        # {namespace: {raw: translated}}
        self._db: Dict[str, Dict[str, str]] = {}
        self._loaded = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load(self, browser=None, proxy: Optional[Dict] = None) -> bool:
        """Load translations from cache, or fetch from GitHub if stale.

        Args:
            browser: Calibre browser (clone_browser() is called internally).
                     If None, only the on-disk cache is used.
            proxy: Proxy dict for the browser, e.g. {'http': ..., 'https': ...}.

        Returns:
            True if translations are available (from cache or fresh fetch).
        """
        cached = self._load_cache()

        if not self._needs_refresh(cached):
            self._db = cached.get('data', {})
            self._loaded = bool(self._db)
            return self._loaded

        if browser is None:
            # No network: use stale cache as fallback.
            self._db = cached.get('data', {})
            self._loaded = bool(self._db)
            return self._loaded

        return self._fetch(browser, cached.get('etag'), proxy)

    def force_refresh(self, browser, proxy: Optional[Dict] = None) -> bool:
        """Bypass TTL and unconditionally re-fetch from GitHub.

        Args:
            browser: Calibre browser instance.
            proxy: Optional proxy dict.

        Returns:
            True on success.
        """
        return self._fetch(browser, etag=None, proxy=proxy)

    def translate(self, mi) -> None:
        """Translate tags, authors, publisher, and language in a Metadata object.

        Mutates *mi* in-place.  When no translation DB is loaded this is a
        no-op so the plugin degrades gracefully.

        Args:
            mi: calibre.ebooks.metadata.book.base.Metadata instance.
        """
        if not self._loaded or not self._db:
            return

        translated_tags: List[str] = []
        authors: List[str] = []
        groups: List[str] = []
        languages: List[str] = []

        for tag in mi.tags:
            parts = tag.split(':', 1)
            if len(parts) == 1:
                # No namespace — look up in 'reclass' as fallback.
                name = self._lookup('reclass', parts[0], parts[0])
                translated_tags.append(name)
                continue

            ns_raw, raw_value = parts[0].strip(), parts[1].strip()
            # Map namespace if needed (e.g., category -> reclass)
            # Ensure ns_lookup is always a string
            ns_lookup = _NAMESPACE_MAPPING.get(ns_raw)
            if ns_lookup is None:
                ns_lookup = ns_raw

            # Individual comma-separated values (rare but possible).
            for raw in raw_value.split(','):
                raw = raw.strip()
                name = self._lookup(ns_lookup, raw, raw)

                if ns_raw == _NS_AUTHORS:
                    authors.append(name)
                elif ns_raw == _NS_PUBLISHER:
                    groups.append(name)
                elif ns_raw == _NS_LANGUAGE:
                    # Map EhTag Chinese name -> Calibre language code.
                    calibre_lang = _CALIBRE_LANGUAGE.get(name, name)
                    languages.append(calibre_lang)
                    # Use mapped namespace for display name lookup
                    ns_display = self._lookup('rows', ns_lookup, ns_raw)
                    translated_tags.append(f'{ns_display}:{name}')
                else:
                    # Use mapped namespace for display name lookup
                    ns_display = self._lookup('rows', ns_lookup, ns_raw)
                    translated_tags.append(f'{ns_display}:{name}')

        if authors:
            mi.authors = authors
        if groups:
            mi.publisher = '&'.join(groups)
        if languages:
            mi.languages = languages
        mi.tags = translated_tags

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _lookup(self, namespace: str, raw: str, default: str) -> str:
        """Look up a single tag in the translation DB.

        Args:
            namespace: EhTagTranslation namespace key (e.g. 'female').
            raw: Raw E-hentai tag string.
            default: Value to return when no translation found.

        Returns:
            Translated name or *default*.
        """
        # Check hardcoded translations first
        if namespace in _HARDCODED_TRANSLATIONS:
            hc_data = _HARDCODED_TRANSLATIONS[namespace]
            if raw in hc_data:
                return hc_data[raw]
            raw_lower = raw.lower()
            for k, v in hc_data.items():
                if k.lower() == raw_lower:
                    return v
        
        # Check database
        ns_data = self._db.get(namespace, {})
        # Exact match first, then case-insensitive.
        if raw in ns_data:
            return ns_data[raw]
        raw_lower = raw.lower()
        for k, v in ns_data.items():
            if k.lower() == raw_lower:
                return v
        return default

    def _needs_refresh(self, cached: Dict) -> bool:
        """Return True if the cache is absent or older than TTL."""
        if not cached or 'cached_at' not in cached:
            return True
        try:
            cached_time = datetime.fromisoformat(cached['cached_at'])
            return datetime.now() - cached_time > self._ttl
        except (ValueError, KeyError):
            return True

    def _load_cache(self) -> Dict:
        """Load metadata + translation data from the on-disk cache."""
        if not os.path.exists(self.cache_file):
            return {}
        try:
            with open(self.cache_file, 'r', encoding='utf-8') as fh:
                return json.load(fh)
        except (IOError, json.JSONDecodeError) as exc:
            if self.log:
                self.log.error(f'TranslationService: failed to read cache: {exc}')
            return {}

    def _save_cache(self, data: Dict, etag: Optional[str]) -> None:
        """Atomically write translation data to disk.

        Args:
            data: Parsed translation DB dict.
            etag: ETag header value from GitHub response, for future
                  conditional requests.
        """
        cache_data = {
            'data': data,
            'etag': etag,
            'cached_at': datetime.now().isoformat(),
        }
        os.makedirs(self.cache_dir, exist_ok=True)
        tmp = self.cache_file + '.tmp'
        try:
            with open(tmp, 'w', encoding='utf-8') as fh:
                json.dump(cache_data, fh, ensure_ascii=False)
            if os.path.exists(self.cache_file):
                os.remove(self.cache_file)
            os.rename(tmp, self.cache_file)
        except IOError as exc:
            if self.log:
                self.log.error(f'TranslationService: failed to save cache: {exc}')
            if os.path.exists(tmp):
                try:
                    os.remove(tmp)
                except OSError:
                    pass

    def _fetch(
        self,
        browser,
        etag: Optional[str],
        proxy: Optional[Dict],
    ) -> bool:
        """Fetch the translation asset from GitHub.

        Uses ETag conditional request when *etag* is supplied so unchanged
        data is not re-downloaded (GitHub returns 304).

        Args:
            browser: Calibre browser instance.
            etag: ETag value from last successful fetch (may be None).
            proxy: Proxy configuration dict.

        Returns:
            True if translation data is now available.
        """
        try:
            br = browser.clone_browser()
            if proxy:
                br.set_proxies(proxies=proxy, proxy_bypass=lambda h: False)

            headers = [('Accept-Encoding', 'gzip')]
            if etag:
                headers.append(('If-None-Match', etag))
            br.addheaders = headers

            response = br.open_novisit(_RELEASE_URL, timeout=60)
            status = getattr(response, 'getcode', lambda: 200)()
            raw_bytes = response.read()
            new_etag = None
            info = getattr(response, 'info', lambda: None)()
            if info:
                new_etag = info.get('ETag') or info.get('etag')

            if status == 304:
                # GitHub says not modified — extend TTL without re-parsing.
                cached = self._load_cache()
                self._db = cached.get('data', {})
                self._loaded = bool(self._db)
                # Update cached_at so TTL resets.
                self._save_cache(self._db, etag)
                return self._loaded

            # Decompress (GitHub redirects; the final response may be raw gzip
            # or already decompressed by Calibre's browser).
            try:
                decompressed = gzip.decompress(raw_bytes)
            except (OSError, EOFError):
                decompressed = raw_bytes  # Already plain JSON.

            self._db = _parse_db(decompressed)
            self._loaded = bool(self._db)
            self._save_cache(self._db, new_etag)
            if self.log:
                self.log.info(
                    f'TranslationService: loaded {sum(len(v) for v in self._db.values())} tags'
                )
            return self._loaded

        except Exception as exc:  # noqa: BLE001
            if self.log:
                self.log.error(f'TranslationService: fetch failed: {exc}')
            # Fall back to stale cache.
            cached = self._load_cache()
            self._db = cached.get('data', {})
            self._loaded = bool(self._db)
            return self._loaded
