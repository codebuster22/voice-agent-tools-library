"""
GitHub Knowledge Base Fetcher

Fetches latest knowledge base content from GitHub raw URLs
for car dealership voice agent knowledge synchronization.
"""

import asyncio
import httpx
from datetime import datetime
from typing import List, Dict, Any
from urllib.parse import urlparse
import re


async def fetch_latest_kb(
    github_raw_urls: List[str],
    cache_duration_minutes: int = 30,
    max_file_size_mb: int = 10,
    timeout_seconds: int = 30
) -> Dict[str, Any]:
    """
    Fetch latest knowledge base content from GitHub raw URLs
    
    Args:
        github_raw_urls: List of GitHub raw URLs to fetch
        cache_duration_minutes: Cache duration for future use (metadata only)
        max_file_size_mb: Maximum file size in MB (warning threshold)
        timeout_seconds: Request timeout in seconds
        
    Returns:
        Dict containing files data, metadata, and any warnings
        
    Raises:
        ValueError: Invalid input parameters
        Exception: Network, HTTP, or processing errors
    """
    # Input validation
    if not github_raw_urls:
        raise ValueError("Must provide at least one URL")
    
    # Validate URLs
    for url in github_raw_urls:
        if not _is_valid_url(url):
            raise ValueError(f"Invalid URL format: {url}")
    
    start_time = datetime.now()
    files = []
    warnings = []
    
    # Configure HTTP client with proper headers and timeout
    headers = {
        "User-Agent": "Elite Motors KB Sync Tool/1.0",
        "Accept": "text/plain, text/markdown, */*"
    }
    
    try:
        async with httpx.AsyncClient(timeout=timeout_seconds, headers=headers) as client:
            # Fetch all files concurrently
            tasks = [_fetch_single_file(client, url, max_file_size_mb) for url in github_raw_urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    raise Exception(f"Failed to fetch {github_raw_urls[i]}: {str(result)}")
                
                file_data, file_warnings = result
                files.append(file_data)
                warnings.extend(file_warnings)
    
    except httpx.NetworkError as e:
        raise Exception(f"Network error while fetching knowledge base: {str(e)}")
    except httpx.TimeoutException as e:
        raise Exception(f"Request timeout while fetching knowledge base: {str(e)}")
    except Exception as e:
        if "Failed to fetch" in str(e) or "Network error" in str(e) or "timeout" in str(e).lower():
            raise
        raise Exception(f"Error fetching knowledge base: {str(e)}")
    
    end_time = datetime.now()
    fetch_duration_ms = (end_time - start_time).total_seconds() * 1000
    
    result = {
        "files": files,
        "total_files": len(files),
        "last_updated": end_time.isoformat(),
        "fetch_duration_ms": round(fetch_duration_ms, 2),
        "cache_duration_minutes": cache_duration_minutes
    }
    
    if warnings:
        result["warnings"] = warnings
    
    return result


async def _fetch_single_file(
    client: httpx.AsyncClient, 
    url: str, 
    max_file_size_mb: int
) -> tuple[Dict[str, Any], List[str]]:
    """
    Fetch a single file from GitHub raw URL
    
    Args:
        client: HTTP client instance
        url: GitHub raw URL
        max_file_size_mb: Maximum file size warning threshold
        
    Returns:
        Tuple of (file_data, warnings)
    """
    fetch_start = datetime.now()
    warnings = []
    
    try:
        response = await client.get(url)
        response.raise_for_status()
        
        # Extract filename from URL
        filename = url.split('/')[-1]
        if not filename.endswith('.md'):
            filename += '.md'
        
        content = response.text
        size_bytes = len(content.encode('utf-8'))
        
        # Check file size and warn if large
        size_mb = size_bytes / (1024 * 1024)
        if size_mb > max_file_size_mb:
            warnings.append(f"Large file warning: {filename} is {size_mb:.1f}MB")
        
        file_data = {
            "filename": filename,
            "content": content,
            "size_bytes": size_bytes,
            "url": url,
            "fetch_time": fetch_start.isoformat()
        }
        
        return file_data, warnings
        
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 403 and "X-RateLimit-Remaining" in e.response.headers:
            if e.response.headers["X-RateLimit-Remaining"] == "0":
                raise Exception("GitHub API rate limit exceeded")
        raise Exception(f"HTTP {e.response.status_code}: {e.response.reason_phrase}")
    except httpx.NetworkError:
        raise Exception("Network connection failed")
    except httpx.TimeoutException:
        raise Exception("Request timeout")


def _is_valid_url(url: str) -> bool:
    """
    Validate URL format
    
    Args:
        url: URL string to validate
        
    Returns:
        True if valid URL format
    """
    try:
        parsed = urlparse(url)
        # Basic URL validation
        if not parsed.scheme or not parsed.netloc:
            return False
        
        # GitHub raw URL pattern validation
        github_raw_pattern = r'https://raw\.githubusercontent\.com/[\w\-\.]+/[\w\-\.]+/[\w\-\.]+/.+\.md$'
        if not re.match(github_raw_pattern, url):
            # Allow other valid URLs but prefer GitHub raw URLs
            return parsed.scheme in ['http', 'https'] and len(parsed.netloc) > 0
        
        return True
    except Exception:
        return False
