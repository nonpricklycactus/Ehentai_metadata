#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Custom Metadata Server Example for Ehentai_metadata Calibre Plugin

This is a Flask-based example server that implements the Custom Metadata Server
Protocol v1.0 as defined in the Ehentai_metadata plugin.

Usage:
1. Install dependencies: pip install flask
2. Run server: python custom_metadata_server_example.py
3. Configure plugin in Calibre:
   - Custom metadata server URL: http://localhost:5000/metadata
   - Custom metadata auth token: Bearer test-token-123 (optional)

Protocol Specification (v1.0):
- Endpoint: POST /metadata
- Request JSON format:
  {
    "schema_version": "1.0",
    "search_type": "identify",
    "title": "Gallery Title",
    "authors": ["Artist Name"],
    "identifiers": {"ehentai": "12345_abc_0"}
  }
- Response JSON format:
  {
    "schema_version": "1.0",
    "source": "My Metadata Server",
    "results": [{
      "title": "Gallery Title",
      "authors": ["Artist Name"],
      "publisher": "Circle Name",
      "tags": ["female:glasses", "category:doujinshi"],
      "rating": 4.5,
      "cover_url": "https://example.com/cover.jpg",
      "identifiers": {"ehentai": "12345_abc_0"}
    }],
    "error": null
  }
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

from flask import Flask, request, jsonify, make_response

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
CONFIG = {
    'host': '0.0.0.0',
    'port': 5000,
    'debug': True,
    'secret_key': 'dev-secret-key-change-in-production',
    # Optional authentication token (Bearer token)
    'auth_token': 'test-token-123',  # Set to None to disable authentication
    'require_auth': False,  # Set to True to require authentication
}

# Sample metadata database (in-memory for example)
# In a real implementation, this would be a database
SAMPLE_METADATA = {
    # Key: (title, authors_tuple) tuple - authors must be tuple for hashability
    ('拘束する部活動', ('すもも堂',)): {
        'title': '拘束する部活動',
        'authors': ['すもも堂'],
        'publisher': 'みらくるバーン',
        'tags': [
            'category:doujinshi',
            'parody:fate',
            'character:saber',
            'female:glasses',
            'female:maid',
            'group:type-moon',
            'language:japanese',
            'translator:ehnd',
            'digital:version'
        ],
        'rating': 4.7,
        'cover_url': 'https://ehgt.org/w/02/312/55359-g5vlf056.webp',
        'identifiers': {'ehentai': '3852762_f65294d2bb_0'}
    },
    ('イブキとい～っぱいシようねっ♡', ('比宮じょーず',)): {
        'title': 'イブキとい～っぱいシようねっ♡',
        'authors': ['比宮じょーず'],
        'publisher': 'みらくるバーン',
        'tags': [
            'category:doujinshi',
            'parody:blue-archive',
            'character:ibuki',
            'female:glasses',
            'female:maid',
            'group:blue-archive',
            'language:japanese',
            'translator:ehnd'
        ],
        'rating': 4.5,
        'cover_url': 'https://ehgt.org/w/01/123/45678-abc123def.webp',
        'identifiers': {'ehentai': '1234567_abcdef_0'}
    },
    ('Example Manga', ('Sample Artist',)): {
        'title': 'Example Manga',
        'authors': ['Sample Artist'],
        'publisher': 'Sample Publisher',
        'tags': [
            'category:manga',
            'female:catgirl',
            'female:animal ears',
            'language:english',
            'digital:version'
        ],
        'rating': 3.8,
        'cover_url': 'https://example.com/cover.jpg',
        'identifiers': {'ehentai': '9999999_xyz_0'}
    }
}

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = CONFIG['secret_key']

# Protocol constants
PROTOCOL_VERSION = '1.0'
SERVER_NAME = 'Ehentai Metadata Example Server'


def validate_auth() -> Optional[Dict[str, Any]]:
    """Validate Bearer token authentication.
    
    Returns:
        Error response dict if authentication fails, None if successful.
    """
    if not CONFIG['require_auth'] or not CONFIG['auth_token']:
        return None
    
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return {
            'schema_version': PROTOCOL_VERSION,
            'source': SERVER_NAME,
            'results': [],
            'error': 'Missing Authorization header'
        }
    
    # Check Bearer token
    if not auth_header.startswith('Bearer '):
        return {
            'schema_version': PROTOCOL_VERSION,
            'source': SERVER_NAME,
            'results': [],
            'error': 'Invalid Authorization format. Expected: Bearer <token>'
        }
    
    token = auth_header[7:]  # Remove 'Bearer ' prefix
    if token != CONFIG['auth_token']:
        return {
            'schema_version': PROTOCOL_VERSION,
            'source': SERVER_NAME,
            'results': [],
            'error': 'Invalid authentication token'
        }
    
    return None


def validate_request(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Validate incoming request against protocol schema.
    
    Args:
        data: Parsed JSON request data.
        
    Returns:
        Error response dict if validation fails, None if valid.
    """
    # Check required fields
    required_fields = ['schema_version', 'search_type', 'title', 'authors', 'identifiers']
    for field in required_fields:
        if field not in data:
            error_msg = f'Missing required field: {field}'
            logger.warning(f"Validation failed - {error_msg}. Data keys: {list(data.keys())}")
            return {
                'schema_version': PROTOCOL_VERSION,
                'source': SERVER_NAME,
                'results': [],
                'error': error_msg
            }
    
    # Check schema version
    if data['schema_version'] != PROTOCOL_VERSION:
        error_msg = f'Unsupported schema version: {data["schema_version"]}. Expected: {PROTOCOL_VERSION}'
        logger.warning(f"Validation failed - {error_msg}")
        return {
            'schema_version': PROTOCOL_VERSION,
            'source': SERVER_NAME,
            'results': [],
            'error': error_msg
        }
    
    # Check search type
    if data['search_type'] not in ['identify', 'cover']:
        error_msg = f'Invalid search_type: {data["search_type"]}. Expected: "identify" or "cover"'
        logger.warning(f"Validation failed - {error_msg}")
        return {
            'schema_version': PROTOCOL_VERSION,
            'source': SERVER_NAME,
            'results': [],
            'error': error_msg
        }
    
    # Validate types
    if not isinstance(data['title'], str):
        error_msg = 'title must be a string'
        logger.warning(f"Validation failed - {error_msg}. title type: {type(data['title'])}, value: {repr(data['title'])}")
        return {
            'schema_version': PROTOCOL_VERSION,
            'source': SERVER_NAME,
            'results': [],
            'error': error_msg
        }
    
    if not isinstance(data['authors'], list):
        error_msg = 'authors must be a list'
        logger.warning(f"Validation failed - {error_msg}. authors type: {type(data['authors'])}, value: {repr(data['authors'])}")
        return {
            'schema_version': PROTOCOL_VERSION,
            'source': SERVER_NAME,
            'results': [],
            'error': error_msg
        }
    
    if not all(isinstance(a, str) for a in data['authors']):
        error_msg = 'authors must be a list of strings'
        invalid_authors = [(i, repr(a), type(a)) for i, a in enumerate(data['authors']) if not isinstance(a, str)]
        logger.warning(f"Validation failed - {error_msg}. Invalid authors: {invalid_authors}")
        return {
            'schema_version': PROTOCOL_VERSION,
            'source': SERVER_NAME,
            'results': [],
            'error': error_msg
        }
    
    if not isinstance(data['identifiers'], dict):
        error_msg = 'identifiers must be a dictionary'
        logger.warning(f"Validation failed - {error_msg}. identifiers type: {type(data['identifiers'])}, value: {repr(data['identifiers'])}")
        return {
            'schema_version': PROTOCOL_VERSION,
            'source': SERVER_NAME,
            'results': [],
            'error': error_msg
        }
    
    logger.debug(f"Validation passed for request with title: {data['title'][:50]}...")
    return None


def search_metadata(title: str, authors: List[str], identifiers: Dict[str, str]) -> List[Dict[str, Any]]:
    """Search for metadata matching the query.
    
    This is a simple example implementation. In a real server, you would:
    1. Query a database
    2. Search external APIs
    3. Use more sophisticated matching algorithms
    
    Args:
        title: Book title to search for.
        authors: List of author names.
        identifiers: Calibre identifiers dict.
        
    Returns:
        List of matching metadata results.
    """
    results = []
    
    # Try to match by ehentai identifier first
    ehentai_id = identifiers.get('ehentai')
    if ehentai_id:
        for metadata in SAMPLE_METADATA.values():
            if metadata['identifiers'].get('ehentai') == ehentai_id:
                results.append(metadata.copy())
                return results
    
    # Try to match by title and authors (simple exact match for example)
    search_key = (title.strip().lower(), tuple(a.lower() for a in authors))
    
    for (db_title, db_authors), metadata in SAMPLE_METADATA.items():
        # Simple matching logic - in real implementation, use fuzzy matching
        title_match = title.strip().lower() in db_title.lower() or db_title.lower() in title.strip().lower()
        
        # Check if any author matches
        author_match = False
        if authors:
            search_authors_lower = [a.lower() for a in authors]
            db_authors_lower = [a.lower() for a in db_authors]
            for author in search_authors_lower:
                if any(author in db_author or db_author in author for db_author in db_authors_lower):
                    author_match = True
                    break
        else:
            author_match = True  # No authors specified, match any
        
        if title_match and author_match:
            results.append(metadata.copy())
    
    return results


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'server': SERVER_NAME,
        'version': PROTOCOL_VERSION,
        'timestamp': datetime.now().isoformat()
    })


@app.route('/metadata', methods=['POST'])
def metadata_endpoint():
    """Main metadata search endpoint.
    
    Implements the Custom Metadata Server Protocol v1.0.
    """
    # Log request
    client_ip = request.remote_addr
    logger.info(f"Metadata request from {client_ip}")
    logger.debug(f"Request headers: {dict(request.headers)}")
    logger.debug(f"Request content type: {request.content_type}")
    logger.debug(f"Request content length: {request.content_length}")
    
    # Check authentication
    auth_error = validate_auth()
    if auth_error:
        logger.warning(f"Authentication failed for {client_ip}")
        logger.debug(f"Auth headers: {request.headers.get('Authorization', 'None')}")
        return jsonify(auth_error), 401
    
    # Parse request JSON
    try:
        data = request.get_json()
        if not data:
            logger.warning(f"Empty request body from {client_ip}")
            return jsonify({
                'schema_version': PROTOCOL_VERSION,
                'source': SERVER_NAME,
                'results': [],
                'error': 'Invalid JSON or empty request body'
            }), 400
        logger.debug(f"Parsed JSON data keys: {list(data.keys())}")
    except Exception as e:
        logger.error(f"JSON parse error from {client_ip}: {e}")
        # Try to read raw body for debugging
        try:
            raw_body = request.get_data(as_text=True)
            logger.debug(f"Raw request body (first 500 chars): {raw_body[:500]}")
        except:
            pass
        return jsonify({
            'schema_version': PROTOCOL_VERSION,
            'source': SERVER_NAME,
            'results': [],
            'error': f'Invalid JSON: {str(e)}'
        }), 400
    
    # Validate request
    validation_error = validate_request(data)
    if validation_error:
        logger.warning(f"Validation failed: {validation_error.get('error')}")
        return jsonify(validation_error), 400
    
    # Extract search parameters
    title = data['title']
    authors = data['authors']
    identifiers = data['identifiers']
    search_type = data['search_type']
    
    logger.info(f"Search: type={search_type}, title={title}, authors={authors}, identifiers={identifiers}")
    
    # Handle different search types
    if search_type == 'identify':
        # Search for metadata
        results = search_metadata(title, authors, identifiers)
        
        response = {
            'schema_version': PROTOCOL_VERSION,
            'source': SERVER_NAME,
            'results': results,
            'error': None
        }
        
        logger.info(f"Found {len(results)} results for '{title}'")
        return jsonify(response)
    
    elif search_type == 'cover':
        # For cover search, we'd return cover URLs
        # This example just returns the same as identify
        results = search_metadata(title, authors, identifiers)
        
        # Extract just cover URLs for cover search
        cover_results = []
        for result in results:
            if 'cover_url' in result:
                cover_results.append({
                    'cover_url': result['cover_url'],
                    'identifiers': result.get('identifiers', {})
                })
        
        response = {
            'schema_version': PROTOCOL_VERSION,
            'source': SERVER_NAME,
            'results': cover_results,
            'error': None
        }
        
        logger.info(f"Found {len(cover_results)} covers for '{title}'")
        return jsonify(response)
    
    else:
        # Should not reach here due to validation
        return jsonify({
            'schema_version': PROTOCOL_VERSION,
            'source': SERVER_NAME,
            'results': [],
            'error': f'Unhandled search_type: {search_type}'
        }), 400


@app.route('/example-request', methods=['GET'])
def example_request():
    """Return an example request JSON for testing."""
    example = {
        'schema_version': '1.0',
        'search_type': 'identify',
        'title': '拘束する部活動',
        'authors': ['すもも堂'],
        'identifiers': {'ehentai': '3852762_f65294d2bb_0'}
    }
    
    return jsonify({
        'description': 'Example request for testing the metadata endpoint',
        'endpoint': 'POST /metadata',
        'headers': {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer test-token-123 (if authentication enabled)'
        },
        'example_request': example,
        'curl_command': 'curl -X POST http://localhost:5000/metadata \\\n  -H "Content-Type: application/json" \\\n  -H "Authorization: Bearer test-token-123" \\\n  -d \'{"schema_version":"1.0","search_type":"identify","title":"拘束する部活動","authors":["すもも堂"],"identifiers":{"ehentai":"3852762_f65294d2bb_0"}}\''
    })


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({
        'schema_version': PROTOCOL_VERSION,
        'source': SERVER_NAME,
        'results': [],
        'error': f'Endpoint not found: {request.path}'
    }), 404


@app.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 errors."""
    return jsonify({
        'schema_version': PROTOCOL_VERSION,
        'source': SERVER_NAME,
        'results': [],
        'error': f'Method not allowed: {request.method}'
    }), 405


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {error}")
    return jsonify({
        'schema_version': PROTOCOL_VERSION,
        'source': SERVER_NAME,
        'results': [],
        'error': 'Internal server error'
    }), 500


if __name__ == '__main__':
    print("=" * 70)
    print("Custom Metadata Server Example for Ehentai_metadata Calibre Plugin")
    print("=" * 70)
    print(f"Server: {SERVER_NAME}")
    print(f"Protocol Version: {PROTOCOL_VERSION}")
    print(f"Host: {CONFIG['host']}")
    print(f"Port: {CONFIG['port']}")
    print(f"Debug: {CONFIG['debug']}")
    print(f"Authentication: {'Enabled' if CONFIG['require_auth'] else 'Disabled'}")
    if CONFIG['require_auth']:
        print(f"Auth Token: Bearer {CONFIG['auth_token']}")
    print()
    print("Endpoints:")
    print("  GET  /health          - Health check")
    print("  POST /metadata        - Metadata search (main endpoint)")
    print("  GET  /example-request - Example request format")
    print()
    print("Calibre Plugin Configuration:")
    print("  Custom metadata server URL: http://localhost:5000/metadata")
    if CONFIG['require_auth']:
        print(f"  Custom metadata auth token: Bearer {CONFIG['auth_token']}")
    else:
        print("  Custom metadata auth token: (leave empty)")
    print("=" * 70)
    print()
    
    # Start Flask server
    app.run(
        host=CONFIG['host'],
        port=CONFIG['port'],
        debug=CONFIG['debug']
    )