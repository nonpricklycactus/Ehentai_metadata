#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Network layer with rate limiting for E-hentai metadata plugin."""

from __future__ import (unicode_literals, division, absolute_import, print_function)

import time
import threading
from typing import Optional, Dict, List, Any

__license__ = 'GPL v3'
__copyright__ = '2026, nonpricklycactus'


class NetworkClient:
    """HTTP client with rate limiting and abort support."""
    
    def __init__(self, browser, rate_limit_seconds: float = 5.0):
        """Initialize network client.
        
        Args:
            browser: Calibre browser instance
            rate_limit_seconds: Minimum seconds between requests
        """
        self.browser = browser
        self.rate_limit = rate_limit_seconds
        self._last_request_time = 0.0
        self._lock = threading.Lock()
    
    def request(
        self,
        url: str,
        method: str = 'GET',
        data: Optional[bytes] = None,
        headers: Optional[Dict[str, str]] = None,
        cookies: Optional[List[Dict[str, str]]] = None,
        proxy: Optional[Dict[str, str]] = None,
        timeout: int = 30,
        abort = None
    ):
        """Make HTTP request with rate limiting.
        
        Args:
            url: Request URL
            method: HTTP method (GET/POST)
            data: Request body for POST
            headers: Custom headers dict
            cookies: List of cookie dicts with name/value/domain/path
            proxy: Proxy dict with http/https keys
            timeout: Request timeout in seconds
            abort: Calibre abort signal (EventType with is_set())
            
        Returns:
            Response object with read() method
            
        Raises:
            Exception: If abort is set or request fails
        """
        with self._lock:
            if abort and abort.is_set():
                raise Exception("Request aborted by user")
            
            # Rate limiting
            elapsed = time.time() - self._last_request_time
            if elapsed < self.rate_limit:
                sleep_time = self.rate_limit - elapsed
                time.sleep(sleep_time)
                
                if abort and abort.is_set():
                    raise Exception("Request aborted during rate limit wait")
            
            # Configure browser
            br = self.browser.clone_browser()
            
            if proxy:
                br.set_proxies(proxies=proxy, proxy_bypass=lambda hostname: False)
            
            if cookies:
                for cookie in cookies:
                    br.set_cookie(
                        name=cookie['name'],
                        value=cookie['value'],
                        domain=cookie['domain'],
                        path=cookie['path']
                    )
            
            if headers:
                br.addheaders = [(k, v) for k, v in headers.items()]
            
            # Make request
            self._last_request_time = time.time()
            
            if method == 'POST' and data:
                return br.open_novisit(url, data=data, timeout=timeout)
            else:
                return br.open_novisit(url, timeout=timeout)
