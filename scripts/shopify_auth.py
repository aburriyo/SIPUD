#!/usr/bin/env python
"""
Shopify Client Credentials Grant Authentication
Automatically obtains and refreshes access tokens using client_id + client_secret.

Tokens expire in 24 hours and are cached in memory and optionally in a file.
"""
import os
import json
import time
import requests
from pathlib import Path
from threading import Lock

# Configuration from environment
SHOPIFY_CLIENT_ID = os.environ.get('SHOPIFY_CLIENT_ID', '')
SHOPIFY_CLIENT_SECRET = os.environ.get('SHOPIFY_CLIENT_SECRET', '')
SHOPIFY_STORE_DOMAIN = os.environ.get('SHOPIFY_STORE_DOMAIN', '')

# Token cache
_token_cache = {
    'access_token': None,
    'expires_at': 0,
    'scope': None
}
_token_lock = Lock()

# Optional: persist token to file to survive restarts
TOKEN_CACHE_FILE = os.environ.get('SHOPIFY_TOKEN_CACHE_FILE', '/tmp/shopify_token_cache.json')


def _load_cached_token():
    """Load token from file cache if exists and not expired."""
    global _token_cache
    
    try:
        cache_path = Path(TOKEN_CACHE_FILE)
        if cache_path.exists():
            with open(cache_path, 'r') as f:
                cached = json.load(f)
                if cached.get('expires_at', 0) > time.time() + 300:  # 5 min buffer
                    _token_cache = cached
                    return True
    except Exception:
        pass
    return False


def _save_token_cache():
    """Save current token to file cache."""
    try:
        cache_path = Path(TOKEN_CACHE_FILE)
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        with open(cache_path, 'w') as f:
            json.dump(_token_cache, f)
    except Exception:
        pass  # Silently fail - memory cache still works


def get_access_token(
    client_id: str = None,
    client_secret: str = None,
    store_domain: str = None,
    force_refresh: bool = False
) -> str:
    """
    Get a valid Shopify access token using client credentials grant.
    
    Args:
        client_id: Shopify app client ID (defaults to SHOPIFY_CLIENT_ID env var)
        client_secret: Shopify app client secret (defaults to SHOPIFY_CLIENT_SECRET env var)
        store_domain: Store domain like 'mystore.myshopify.com' (defaults to SHOPIFY_STORE_DOMAIN env var)
        force_refresh: Force token refresh even if not expired
    
    Returns:
        Valid access token string
    
    Raises:
        ValueError: If credentials are missing
        RuntimeError: If token acquisition fails
    """
    global _token_cache
    
    # Use provided values or fall back to env vars
    client_id = client_id or SHOPIFY_CLIENT_ID
    client_secret = client_secret or SHOPIFY_CLIENT_SECRET
    store_domain = store_domain or SHOPIFY_STORE_DOMAIN
    
    # Validate inputs
    if not client_id:
        raise ValueError("Missing SHOPIFY_CLIENT_ID - set env var or pass client_id")
    if not client_secret:
        raise ValueError("Missing SHOPIFY_CLIENT_SECRET - set env var or pass client_secret")
    if not store_domain:
        raise ValueError("Missing SHOPIFY_STORE_DOMAIN - set env var or pass store_domain")
    
    with _token_lock:
        # Check if we have a valid cached token
        if not force_refresh:
            # Try memory cache first
            if _token_cache['access_token'] and _token_cache['expires_at'] > time.time() + 300:
                return _token_cache['access_token']
            
            # Try file cache
            if _load_cached_token():
                return _token_cache['access_token']
        
        # Need to fetch a new token
        token_url = f"https://{store_domain}/admin/oauth/access_token"
        
        payload = {
            'grant_type': 'client_credentials',
            'client_id': client_id,
            'client_secret': client_secret
        }
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        try:
            response = requests.post(token_url, data=payload, headers=headers, timeout=30)
            
            if response.status_code != 200:
                error_msg = f"Failed to get access token: HTTP {response.status_code}"
                try:
                    error_data = response.json()
                    if 'error_description' in error_data:
                        error_msg += f" - {error_data['error_description']}"
                    elif 'error' in error_data:
                        error_msg += f" - {error_data['error']}"
                except Exception:
                    error_msg += f" - {response.text[:200]}"
                raise RuntimeError(error_msg)
            
            data = response.json()
            
            # Update cache
            _token_cache['access_token'] = data['access_token']
            _token_cache['expires_at'] = time.time() + data.get('expires_in', 86399)
            _token_cache['scope'] = data.get('scope', '')
            
            # Persist to file
            _save_token_cache()
            
            return _token_cache['access_token']
            
        except requests.RequestException as e:
            raise RuntimeError(f"Network error getting access token: {str(e)}")


def get_auth_headers(
    client_id: str = None,
    client_secret: str = None,
    store_domain: str = None
) -> dict:
    """
    Get headers dict with valid authorization for Shopify API requests.
    
    Returns:
        Dict with X-Shopify-Access-Token and Content-Type headers
    """
    token = get_access_token(client_id, client_secret, store_domain)
    return {
        'X-Shopify-Access-Token': token,
        'Content-Type': 'application/json'
    }


def get_token_info() -> dict:
    """
    Get information about the current cached token.
    
    Returns:
        Dict with token info (masked), expiration, and scope
    """
    with _token_lock:
        if not _token_cache['access_token']:
            return {'status': 'no_token'}
        
        token = _token_cache['access_token']
        expires_at = _token_cache['expires_at']
        remaining = max(0, expires_at - time.time())
        
        return {
            'status': 'valid' if remaining > 0 else 'expired',
            'token_preview': f"{token[:8]}...{token[-4:]}" if len(token) > 12 else '***',
            'expires_in_seconds': int(remaining),
            'expires_in_hours': round(remaining / 3600, 1),
            'scope': _token_cache.get('scope', '')
        }


# Convenience: preload token on module import if env vars are set
if SHOPIFY_CLIENT_ID and SHOPIFY_CLIENT_SECRET and SHOPIFY_STORE_DOMAIN:
    try:
        _load_cached_token()
    except Exception:
        pass


if __name__ == '__main__':
    # Test the module
    print("🔐 Testing Shopify Client Credentials Grant...")
    print(f"   Store: {SHOPIFY_STORE_DOMAIN}")
    print(f"   Client ID: {SHOPIFY_CLIENT_ID[:8]}..." if SHOPIFY_CLIENT_ID else "   Client ID: NOT SET")
    
    try:
        token = get_access_token()
        info = get_token_info()
        print(f"\n✅ Token obtained successfully!")
        print(f"   Preview: {info['token_preview']}")
        print(f"   Expires in: {info['expires_in_hours']} hours")
        print(f"   Scope: {info['scope']}")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
