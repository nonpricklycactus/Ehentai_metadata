#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Proxy configuration parsing for E-hentai metadata plugin."""

from __future__ import (unicode_literals, division, absolute_import, print_function)

import base64
import re
from typing import Optional, Dict, Tuple

__license__ = 'GPL v3'
__copyright__ = '2026, nonpricklycactus'


class ProxyConfig:
    """Parses and holds proxy configuration with authentication."""

    # Pattern: [scheme://][username:password@]host:port
    _PROXY_RE = re.compile(
        r'^(?:(?P<scheme>https?|socks5?)://)?'
        r'(?:(?P<username>[^:@]+):(?P<password>[^@]+)@)?'
        r'(?P<host>[^:/]+)'
        r'(?::(?P<port>\d+))?$'
    )

    def __init__(self, proxy_string: Optional[str]):
        """Initialize proxy config from config string.

        Args:
            proxy_string: Proxy URL, e.g.  user:pass@host:8080  or
                          http://user:pass@host:8080  or  http://host:8080
        """
        self.raw = proxy_string or ''
        stripped = proxy_string.strip() if proxy_string else ''
        self.enabled = bool(stripped)
        self.proxy_url: Optional[str] = None
        self.auth_header: Optional[str] = None
        self.proxy_dict: Dict[str, str] = {}

        if self.enabled:
            self._parse(stripped)

    def _parse(self, proxy_string: str) -> None:
        """Parse proxy string into URL and auth header."""
        m = self._PROXY_RE.match(proxy_string)
        if not m:
            # Not parseable — try using as-is
            self.proxy_url = proxy_string
            self.proxy_dict = {'http': proxy_string, 'https': proxy_string}
            return

        scheme = m.group('scheme') or 'http'
        username = m.group('username')
        password = m.group('password')
        host = m.group('host')
        port = m.group('port')

        # Build clean proxy URL (no credentials embedded — use header instead)
        if port:
            host_port = f'{host}:{port}'
        else:
            host_port = host

        self.proxy_url = f'{scheme}://{host_port}'
        self.proxy_dict = {
            'http': self.proxy_url,
            'https': self.proxy_url,
        }

        # Build Authorization header if credentials present
        if username and password:
            credentials = base64.b64encode(
                f'{username}:{password}'.encode('utf-8')
            ).decode('ascii')
            self.auth_header = f'Proxy-Authorization: Basic {credentials}'

    def get_proxy_dict(self) -> Dict[str, str]:
        """Return proxy dict suitable for browser.set_proxies()."""
        return self.proxy_dict if self.enabled else {}

    def get_auth_header(self) -> Optional[str]:
        """Return Proxy-Authorization header value or None."""
        return self.auth_header if self.enabled else None

    def as_browser_headers(self) -> list:
        """Return list of (name, value) header tuples for proxy auth."""
        if self.enabled and self.auth_header:
            name, _, value = self.auth_header.partition(': ')
            return [(name, value)]
        return []

    def __bool__(self) -> bool:
        return self.enabled

    def __repr__(self) -> str:
        if not self.enabled:
            return 'ProxyConfig(disabled)'
        return f'ProxyConfig(url={self.proxy_url!r}, auth={bool(self.auth_header)})'
