# AGENTS.md - Developer Guide for AI Coding Agents

## Project Overview

This is a **Calibre Metadata Plugin** for E-Hentai/ExHentai galleries. It is NOT a standard Python package — it is distributed as a Calibre plugin ZIP file and runs inside the Calibre runtime.

- **Type**: Calibre metadata source plugin
- **Version**: 3.0.0
- **Minimum Calibre**: 9.0.0
- **License**: GPL v3
- **Author**: nonpricklycactus
- **Architecture**: Modular (6 files: __init__.py + 5 service modules)

## Build / Test Commands

```bash
# Build and install into running Calibre
calibre-customize -b .

# Run inline tests
calibre-debug -e __init__.py

# Install from ZIP (manual)
# Zip the project folder, then: Calibre → Preferences → Plugins → Load plugin from file
```

No CI/CD, no pytest, no linters are configured.

## Project Structure

```
Ehentai_metadata/
├── __init__.py       # Main plugin (Ehentai class) — orchestrates all modules
├── net.py            # HTTP client with rate limiting (5 s, threading.Lock)
├── proxy.py          # Proxy URL parser (user:pass@host:port → auth header)
├── translation.py    # Tag translation via GitHub EhTagTranslation (24 h cache)
├── protocol.py       # Custom metadata server client (JSON protocol v1.0)
├── ui.py             # Qt dialog for Accurate Label mode
├── image/            # Plugin assets
├── AGENTS.md
├── README.md
└── README_cn.md
```

## Code Style Guidelines

### Imports

```python
from __future__ import (unicode_literals, division, absolute_import, print_function)

# Calibre imports first
from calibre.ebooks.metadata.sources.base import Source, Option
from calibre.ebooks.metadata.book.base import Metadata

# Local plugin modules (relative imports)
from .net import NetworkClient
from .proxy import ProxyConfig

# Stdlib last
import re
import json
```

### Qt Imports (Calibre 9.x)

```python
try:
    from qt.core import QDialog, QVBoxLayout, QLabel
except ImportError:
    from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel
```

### Type Hints

Use consistently for all new functions:

```python
def extract_field_from_title(title: str, log) -> FieldFromTitle: ...
def is_subsequence(short: str, long: str) -> bool: ...
```

### Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Classes | PascalCase | `TranslationService`, `ProxyConfig` |
| Functions | snake_case | `extract_field_from_title` |
| Constants | SCREAMING_SNAKE_CASE | `LANGUAGE_DICT`, `API_URL` |
| Private methods | `_snake_case` | `_build_search_url`, `_fetch_all_details` |

### Error Handling

```python
# Specific exceptions, log + return (don't raise for expected failures)
try:
    resp = self.net.request(url, ...)
except Exception as e:
    log.error(f'Request failed: {e}')
    return

# In loops: log and continue
try:
    mi = to_metadata(gm, log)
except Exception as e:
    log.exception(f'Failed to process: {e}')
```

### Logging

Use Calibre's `log` parameter (NOT Python's `logging` module):

```python
log.info('Starting search')
log.error('No results found')
log.exception('Failed to parse:', exc)
```

### Docstrings (Google style for new code)

```python
def my_func(arg: str) -> bool:
    """Short description.

    Args:
        arg: What this arg does.

    Returns:
        True if successful.
    """
```

## Architecture

```
Calibre calls Ehentai.identify()
  └─ net.NetworkClient          rate-limited HTTP for all requests
  └─ proxy.ProxyConfig          parses proxy URL + auth header
  └─ translation.TranslationService  fetches/caches GitHub translations
  └─ protocol.CustomMetadataClient   optional custom metadata server
  └─ ui.AccurateLabelDialog          Qt URL input dialog

Data flow:
  identify()
    → _build_search_url() → search page fetch via NetworkClient
    → _extract_gallery_ids() → parse gid/token from HTML
    → _fetch_all_details() → POST to api.e-hentai.org (max 25/request)
    → to_metadata() → Calibre Metadata object
    → TranslationService.translate() if translate_tags enabled
    → CustomMetadataClient.search() if configured
    → result_queue.put(mi)

  download_cover()
    → NetworkClient fetch cached cover URL
```

## Key Constraints

1. **No async/await** — plugin is entirely synchronous
2. **No external dependencies** — use only Calibre's stdlib + bundled libs
3. **Rate limiting** — 5 s between bursts enforced in `net.NetworkClient`
4. **No pytest** — use inline `if __name__ == '__main__'` tests only
5. **LSP errors for Calibre imports are expected** — Calibre runtime not installed locally
6. **`_()` is injected by Calibre** — undefined in type checker, normal in plugin context

## Configuration Options

| Key | Type | Description |
|-----|------|-------------|
| `use_exhentai` | bool | Use ExHentai (requires cookies) |
| `translate_tags` | bool | Translate tags via GitHub EhTagTranslation |
| `accurate_label` | bool | Prompt for exact gallery URL |
| `use_proxy` | bool | Enable proxy |
| `ipb_member_id` | string | ExHentai cookie |
| `ipb_pass_hash` | string | ExHentai cookie |
| `igneous` | string | ExHentai cookie |
| `proxy_url` | string | Proxy: `user:pass@host:port` or `http://host:port` |
| `custom_metadata_url` | string | Custom server endpoint URL |
| `custom_metadata_token` | string | Bearer/Basic token for custom server |

## Custom Metadata Server Protocol (v1.0)

Third-party developers can implement their own metadata server compatible with this plugin.

### Request

```json
POST /your-endpoint
Content-Type: application/json
Authorization: Bearer <token>

{
  "schema_version": "1.0",
  "search_type": "identify",
  "title": "Gallery Title",
  "authors": ["Artist Name"],
  "identifiers": {"ehentai": "12345_abc_0"}
}
```

### Response

```json
{
  "schema_version": "1.0",
  "source": "My Metadata Server",
  "results": [
    {
      "title": "Gallery Title",
      "authors": ["Artist Name"],
      "publisher": "Circle Name",
      "tags": ["female:glasses", "category:doujinshi"],
      "rating": 4.5,
      "cover_url": "https://example.com/cover.jpg",
      "identifiers": {"ehentai": "12345_abc_0"}
    }
  ],
  "error": null
}
```

## When Making Changes

1. Test: `calibre-customize -b . && calibre-debug -e __init__.py`
2. Rate limiting is in `net.NetworkClient` — do not add delays elsewhere
3. All HTTP calls must go through `self.net.request()` in `__init__.py`
4. Translation cache is in `.cache/translation_cache.json` (relative to plugin dir)
5. Update version tuple in `Ehentai` class for significant changes
6. Update `README.md` and `README_cn.md` changelog sections
