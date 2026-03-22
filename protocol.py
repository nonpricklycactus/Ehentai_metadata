#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Custom metadata server protocol client."""

from __future__ import (unicode_literals, division, absolute_import, print_function)

import json
from typing import Dict, List, Optional, Any

__license__ = 'GPL v3'
__copyright__ = '2026, nonpricklycactus'

PROTOCOL_VERSION = '1.0'


class CustomMetadataClient:
    """Client for custom metadata server protocol.
    
    Protocol schema v1.0:
    
    Request (POST /metadata):
    {
        "schema_version": "1.0",
        "search_type": "identify" | "cover",
        "title": str,
        "authors": [str],
        "identifiers": {str: str}
    }
    
    Response:
    {
        "schema_version": "1.0",
        "source": str,
        "results": [{
            "title": str,
            "authors": [str],
            "publisher": str,
            "tags": [str],
            "rating": float,
            "cover_url": str,
            "identifiers": {str: str}
        }],
        "error": str (optional)
    }
    """
    
    def __init__(self, endpoint_url: str, auth_token: Optional[str], log=None):
        """Initialize custom metadata client.
        
        Args:
            endpoint_url: Server URL (e.g. http://localhost:8080/metadata)
            auth_token: Bearer token or Basic auth string
            log: Calibre log object (optional, injected later if None)
        """
        self.endpoint = endpoint_url
        self.auth_token = auth_token
        self.log = log
        self.enabled = bool(endpoint_url and endpoint_url.strip())

    def _build_auth_headers(self) -> List[tuple]:
        """Build Authorization headers from auth_token config.
        
        Supports formats:
          - 'Bearer <token>'
          - 'Basic <base64>'
          - Raw token string (wrapped as Bearer)
          
        Returns:
            List of (header_name, header_value) tuples.
        """
        if not self.auth_token:
            return []
        token = self.auth_token.strip()
        if token.startswith('Bearer ') or token.startswith('Basic '):
            return [('Authorization', token)]
        # Treat plain token as Bearer
        return [('Authorization', f'Bearer {token}')]

    def search(
        self,
        browser,
        title: Optional[str] = None,
        authors: Optional[List[str]] = None,
        identifiers: Optional[Dict[str, str]] = None,
        timeout: int = 30,
    ) -> List[Dict[str, Any]]:
        """Query custom metadata server for identify results.
        
        Args:
            browser: Calibre browser instance (clone_browser() called internally).
            title: Book title to search for.
            authors: List of author names.
            identifiers: Calibre identifiers dict.
            timeout: Request timeout in seconds.
            
        Returns:
            List of result dicts matching the protocol schema, or empty list.
        """
        if not self.enabled:
            return []
        
        payload = {
            'schema_version': PROTOCOL_VERSION,
            'search_type': 'identify',
            'title': title or '',
            'authors': authors or [],
            'identifiers': identifiers or {},
        }
        
        try:
            br = browser.clone_browser()
            auth_headers = self._build_auth_headers()
            if auth_headers:
                br.addheaders = auth_headers + [
                    ('Content-Type', 'application/json'),
                    ('Accept', 'application/json'),
                ]
            else:
                br.addheaders = [
                    ('Content-Type', 'application/json'),
                    ('Accept', 'application/json'),
                ]
            
            data = json.dumps(payload).encode('utf-8')
            resp = br.open_novisit(self.endpoint, data=data, timeout=timeout)
            raw = resp.read()
            response = json.loads(raw.decode('utf-8'))
            
            # Validate schema
            if response.get('schema_version') != PROTOCOL_VERSION:
                if self.log:
                    self.log.error(
                        f'CustomMetadataClient: unexpected schema version '
                        f'{response.get("schema_version")!r}'
                    )
                return []
            
            if 'error' in response and response['error']:
                if self.log:
                    self.log.error(
                        f'CustomMetadataClient: server error: {response["error"]}'
                    )
                return []
            
            results = response.get('results', [])
            if self.log:
                self.log.info(
                    f'CustomMetadataClient: got {len(results)} results from '
                    f'{response.get("source", self.endpoint)}'
                )
            return results
        
        except Exception as exc:  # noqa: BLE001
            if self.log:
                self.log.error(f'CustomMetadataClient: request failed: {exc}')
            return []

    def __bool__(self) -> bool:
        return self.enabled
