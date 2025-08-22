"""
Test suite for fetch_latest_kb tool - GitHub integration
Following TDD methodology: write comprehensive tests first
"""

import pytest
import httpx
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
import asyncio
import os

from kb_tools.fetch_latest_kb import fetch_latest_kb


class TestFetchLatestKB:
    """Test fetch_latest_kb GitHub integration functionality"""

    @pytest.fixture
    def mock_urls(self):
        """Sample GitHub raw URLs for testing"""
        return [
            "https://raw.githubusercontent.com/test/repo/main/about-company.md",
            "https://raw.githubusercontent.com/test/repo/main/financing-options.md",
            "https://raw.githubusercontent.com/test/repo/main/services-provided.md",
            "https://raw.githubusercontent.com/test/repo/main/current-offers.md"
        ]

    @pytest.fixture
    def mock_markdown_content(self):
        """Sample markdown content for testing"""
        return {
            "about-company.md": "# About Elite Motors\n\nWe are a family-owned dealership...",
            "financing-options.md": "# Financing Options\n\nWe offer comprehensive financing...",
            "services-provided.md": "# Services Provided\n\nComplete automotive solutions...",
            "current-offers.md": "# Current Offers\n\nSeptember 2025 Special Promotions..."
        }

    @pytest.mark.asyncio
    async def test_fetch_latest_kb_success_all_files(self, mock_urls, mock_markdown_content):
        """Test successful fetching of all knowledge base files"""
        # Mock httpx.AsyncClient responses
        mock_responses = []
        for url in mock_urls:
            filename = url.split('/')[-1]
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = mock_markdown_content[filename]
            mock_response.headers = {"content-length": str(len(mock_markdown_content[filename]))}
            mock_responses.append(mock_response)

        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(side_effect=mock_responses)
            
            result = await fetch_latest_kb(github_raw_urls=mock_urls)
            
            # Verify structure
            assert "files" in result
            assert "total_files" in result
            assert "last_updated" in result
            assert "fetch_duration_ms" in result
            
            # Verify content
            assert result["total_files"] == 4
            assert len(result["files"]) == 4
            
            # Check each file
            for i, file_data in enumerate(result["files"]):
                expected_filename = mock_urls[i].split('/')[-1]
                assert file_data["filename"] == expected_filename
                assert file_data["content"] == mock_markdown_content[expected_filename]
                assert file_data["size_bytes"] == len(mock_markdown_content[expected_filename])
                assert file_data["url"] == mock_urls[i]
                assert "fetch_time" in file_data

    @pytest.mark.asyncio
    async def test_fetch_latest_kb_single_file(self, mock_markdown_content):
        """Test fetching single file"""
        single_url = ["https://raw.githubusercontent.com/test/repo/main/about-company.md"]
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = mock_markdown_content["about-company.md"]
        mock_response.headers = {"content-length": "50"}

        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            result = await fetch_latest_kb(github_raw_urls=single_url)
            
            assert result["total_files"] == 1
            assert len(result["files"]) == 1
            assert result["files"][0]["filename"] == "about-company.md"

    @pytest.mark.asyncio
    async def test_fetch_latest_kb_with_cache_duration(self, mock_urls, mock_markdown_content):
        """Test fetch with custom cache duration"""
        mock_responses = []
        for url in mock_urls:
            filename = url.split('/')[-1]
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = mock_markdown_content[filename]
            mock_response.headers = {"content-length": "100"}
            mock_responses.append(mock_response)

        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(side_effect=mock_responses)
            
            result = await fetch_latest_kb(
                github_raw_urls=mock_urls,
                cache_duration_minutes=60
            )
            
            assert result["total_files"] == 4
            # Cache duration should be stored for future use
            assert "cache_duration_minutes" in result
            assert result["cache_duration_minutes"] == 60

    @pytest.mark.asyncio
    async def test_fetch_latest_kb_http_error(self, mock_urls):
        """Test handling of HTTP errors"""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Not Found", request=MagicMock(), response=mock_response
        )

        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            with pytest.raises(Exception) as exc_info:
                await fetch_latest_kb(github_raw_urls=mock_urls[:1])
            
            assert "Failed to fetch" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_fetch_latest_kb_network_error(self, mock_urls):
        """Test handling of network errors"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=httpx.NetworkError("Connection failed")
            )
            
            with pytest.raises(Exception) as exc_info:
                await fetch_latest_kb(github_raw_urls=mock_urls[:1])
            
            # Should contain either "Network error" or "Network connection failed"
            error_msg = str(exc_info.value).lower()
            assert "network" in error_msg

    @pytest.mark.asyncio
    async def test_fetch_latest_kb_empty_urls(self):
        """Test handling of empty URL list"""
        with pytest.raises(ValueError) as exc_info:
            await fetch_latest_kb(github_raw_urls=[])
        
        assert "at least one URL" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_fetch_latest_kb_invalid_urls(self):
        """Test handling of invalid URLs"""
        invalid_urls = ["not-a-url", "http://"]
        
        with pytest.raises(ValueError) as exc_info:
            await fetch_latest_kb(github_raw_urls=invalid_urls)
        
        assert "Invalid URL" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_fetch_latest_kb_large_file_warning(self, mock_urls):
        """Test warning for large files"""
        large_content = "x" * (10 * 1024 * 1024 + 1)  # 10MB + 1 byte
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = large_content
        mock_response.headers = {"content-length": str(len(large_content))}

        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            result = await fetch_latest_kb(
                github_raw_urls=mock_urls[:1],
                max_file_size_mb=10
            )
            
            # Should include warning but still process
            assert "warnings" in result
            assert any("large file" in warning.lower() for warning in result["warnings"])

    @pytest.mark.asyncio
    async def test_fetch_latest_kb_concurrent_requests(self, mock_urls, mock_markdown_content):
        """Test concurrent fetching of multiple files"""
        mock_responses = []
        for url in mock_urls:
            filename = url.split('/')[-1]
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = mock_markdown_content[filename]
            mock_response.headers = {"content-length": "100"}
            mock_responses.append(mock_response)

        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(side_effect=mock_responses)
            
            start_time = datetime.now()
            result = await fetch_latest_kb(github_raw_urls=mock_urls)
            end_time = datetime.now()
            
            # Should complete relatively quickly due to concurrent requests
            duration_ms = (end_time - start_time).total_seconds() * 1000
            assert duration_ms < 1000  # Should be much faster than sequential
            
            assert result["total_files"] == 4
            assert len(result["files"]) == 4

    @pytest.mark.asyncio
    async def test_fetch_latest_kb_partial_failure(self, mock_urls, mock_markdown_content):
        """Test handling when some files fail to fetch"""
        # First file succeeds, second fails, third succeeds
        mock_responses = [
            # Success
            MagicMock(status_code=200, text=mock_markdown_content["about-company.md"], headers={"content-length": "100"}),
            # Failure
            None,  # Will cause exception
            # Success  
            MagicMock(status_code=200, text=mock_markdown_content["services-provided.md"], headers={"content-length": "100"}),
        ]
        
        def side_effect(*args, **kwargs):
            response = mock_responses.pop(0)
            if response is None:
                raise httpx.NetworkError("Failed to fetch")
            return response

        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(side_effect=side_effect)
            
            # Should raise exception on any failure for data integrity
            with pytest.raises(Exception):
                await fetch_latest_kb(github_raw_urls=mock_urls[:3])

    @pytest.mark.asyncio
    async def test_fetch_latest_kb_timeout_handling(self, mock_urls):
        """Test handling of request timeouts"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=httpx.TimeoutException("Request timed out")
            )
            
            with pytest.raises(Exception) as exc_info:
                await fetch_latest_kb(github_raw_urls=mock_urls[:1])
            
            assert "timeout" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_fetch_latest_kb_custom_timeout(self, mock_urls, mock_markdown_content):
        """Test custom timeout configuration"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = mock_markdown_content["about-company.md"]
        mock_response.headers = {"content-length": "100"}

        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            result = await fetch_latest_kb(
                github_raw_urls=mock_urls[:1],
                timeout_seconds=30
            )
            
            assert result["total_files"] == 1
            
            # Verify timeout was passed to client
            mock_client.assert_called_once()
            call_kwargs = mock_client.call_args[1]
            assert call_kwargs["timeout"] == 30

    @pytest.mark.asyncio
    async def test_fetch_latest_kb_user_agent(self, mock_urls, mock_markdown_content):
        """Test proper User-Agent header is set"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = mock_markdown_content["about-company.md"]
        mock_response.headers = {"content-length": "100"}

        with patch('httpx.AsyncClient') as mock_client:
            mock_get = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value.get = mock_get
            
            await fetch_latest_kb(github_raw_urls=mock_urls[:1])
            
            # Verify User-Agent header was set in client initialization
            mock_client.assert_called_once()
            call_kwargs = mock_client.call_args[1]
            assert "headers" in call_kwargs
            assert "User-Agent" in call_kwargs["headers"]
            assert "Elite Motors KB Sync" in call_kwargs["headers"]["User-Agent"]

    @pytest.mark.asyncio  
    async def test_fetch_latest_kb_github_rate_limit(self, mock_urls):
        """Test handling of GitHub API rate limits"""
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.headers = {"X-RateLimit-Remaining": "0"}
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Rate limit exceeded", request=MagicMock(), response=mock_response
        )

        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            with pytest.raises(Exception) as exc_info:
                await fetch_latest_kb(github_raw_urls=mock_urls[:1])
            
            assert "rate limit" in str(exc_info.value).lower()
