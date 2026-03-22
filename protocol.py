#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Custom metadata server protocol client."""

from __future__ import (unicode_literals, division, absolute_import, print_function)

import json
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse

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
        
        # Validate endpoint URL format on initialization
        if self.enabled and not self._validate_endpoint():
            if self.log:
                self.log.warning(f'CustomMetadataClient: invalid endpoint URL format: {endpoint_url}')
            self.enabled = False

    def _validate_endpoint(self) -> bool:
        """Validate endpoint URL format.
        
        Returns:
            True if URL has valid scheme (http/https) and network location.
        """
        try:
            result = urlparse(self.endpoint)
            return all([result.scheme in ('http', 'https'), result.netloc])
        except Exception:
            return False

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
        title: str = '',
        authors: Optional[List[str]] = None,
        identifiers: Optional[Dict[str, str]] = None,
        timeout: int = 30
    ) -> List[Dict[str, Any]]:
        """Search custom metadata server.
        
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
        
        # Validate and normalize input parameters
        if not isinstance(title, str):
            title = str(title) if title else ''
        if not isinstance(authors, list):
            authors = []
        if not isinstance(identifiers, dict):
            identifiers = {}
        
        payload = {
            'schema_version': PROTOCOL_VERSION,
            'search_type': 'identify',
            'title': title or '',
            'authors': authors or [],
            'identifiers': identifiers or {},
        }
        
        try:
            # Log request details for debugging
            if self.log:
                self.log.info(f'CustomMetadataClient: sending request to {self.endpoint}')
                self.log.info(f'CustomMetadataClient: payload={payload}')
                if auth_headers := self._build_auth_headers():
                    self.log.info(f'CustomMetadataClient: auth headers present')
            
            br = browser.clone_browser()
            auth_headers = self._build_auth_headers()
            
            # Clear any proxy settings to prevent interference
            # When use_proxy is not checked, we should not use proxy
            try:
                # Clear proxy settings
                br.set_proxies({})
                if self.log:
                    self.log.info(f'CustomMetadataClient: cleared proxy settings')
            except Exception as e:
                if self.log:
                    self.log.info(f'CustomMetadataClient: could not clear proxy settings: {e}')
            
            # Build all headers - ensure Content-Type is set for JSON
            all_headers = {}
            all_headers['Content-Type'] = 'application/json'
            all_headers['Accept'] = 'application/json'
            if auth_headers:
                # Convert auth_headers (list of tuples) to dict
                for key, value in auth_headers:
                    all_headers[key] = value
            
            # Debug: log the actual headers being sent
            if self.log:
                self.log.info(f'CustomMetadataClient: request headers: {all_headers}')
                self.log.info(f'CustomMetadataClient: browser type: {type(br)}')
            
            data = json.dumps(payload).encode('utf-8')
            if self.log:
                self.log.info(f'CustomMetadataClient: request data length: {len(data)} bytes')
                self.log.info(f'CustomMetadataClient: request data preview: {data[:100]}...')
            
            # Try direct urllib approach first (more reliable for JSON)
            try:
                import urllib.request
                import urllib.error
                
                if self.log:
                    self.log.info(f'CustomMetadataClient: trying direct urllib.request approach')
                
                # Create request with headers
                req = urllib.request.Request(
                    self.endpoint,
                    data=data,
                    headers=all_headers,
                    method='POST'
                )
                
                # Open with timeout
                resp = urllib.request.urlopen(req, timeout=timeout)
                
                if self.log:
                    self.log.info(f'CustomMetadataClient: direct urllib.request succeeded')
                
            except Exception as urllib_error:
                if self.log:
                    self.log.info(f'CustomMetadataClient: direct urllib.request failed: {urllib_error}, falling back to browser')
                
                # Fall back to browser method
                # Clear any existing headers and set ours
                br.addheaders = []
                
                # Convert headers dict to list of tuples for addheaders
                headers_list = [(k, v) for k, v in all_headers.items()]
                br.addheaders = headers_list
                
                # Debug: check what headers are actually set
                if self.log:
                    self.log.info(f'CustomMetadataClient: browser.addheaders after setting: {br.addheaders}')
                
                # Make the request
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
                self.log.error(f'CustomMetadataClient: endpoint={self.endpoint}')
                self.log.error(f'CustomMetadataClient: payload={payload}')
                # Try to get HTTP status code if available
                if hasattr(exc, 'code'):
                    self.log.error(f'CustomMetadataClient: HTTP status={exc.code}')
                elif hasattr(exc, 'status'):
                    self.log.error(f'CustomMetadataClient: HTTP status={exc.status}')
                # Try to get response body if available
                if hasattr(exc, 'read'):
                    try:
                        error_body = exc.read().decode('utf-8', errors='ignore')
                        self.log.error(f'CustomMetadataClient: response body={error_body[:500]}')
                    except:
                        pass
            return []

    def __bool__(self) -> bool:
        return self.enabled
