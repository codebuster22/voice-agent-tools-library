"""
Test suite for sync_knowledge_base tool - Complete Vapi workflow
Following TDD methodology: write comprehensive tests first
"""

import pytest
import httpx
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
import asyncio
import os

from kb_tools.sync_knowledge_base import sync_knowledge_base


class TestSyncKnowledgeBase:
    """Test sync_knowledge_base Vapi integration functionality"""

    @pytest.fixture
    def mock_vapi_credentials(self):
        """Sample Vapi credentials for testing"""
        return {
            "vapi_api_key": "test_vapi_key_123",
            "knowledge_base_tool_id": "tool_kb_456",
            "vapi_base_url": "https://api.vapi.ai"
        }

    @pytest.fixture
    def mock_markdown_files(self):
        """Sample markdown files from fetch_latest_kb"""
        return [
            {
                "filename": "about-company.md",
                "content": "# About Elite Motors\n\nWe are a family-owned dealership...",
                "size_bytes": 5120,
                "url": "https://raw.githubusercontent.com/test/repo/main/about-company.md"
            },
            {
                "filename": "financing-options.md", 
                "content": "# Financing Options\n\nWe offer comprehensive financing...",
                "size_bytes": 8192,
                "url": "https://raw.githubusercontent.com/test/repo/main/financing-options.md"
            },
            {
                "filename": "services-provided.md",
                "content": "# Services Provided\n\nComplete automotive solutions...",
                "size_bytes": 12288,
                "url": "https://raw.githubusercontent.com/test/repo/main/services-provided.md"
            },
            {
                "filename": "current-offers.md",
                "content": "# Current Offers\n\nSeptember 2025 Special Promotions...",
                "size_bytes": 6144,
                "url": "https://raw.githubusercontent.com/test/repo/main/current-offers.md"
            }
        ]

    @pytest.fixture
    def mock_existing_files(self):
        """Sample existing files in Vapi"""
        return [
            {
                "id": "file_old_001",
                "name": "dealership_kb_about-company.md",
                "originalName": "about-company.md",
                "status": "done",
                "bytes": 4096,
                "createdAt": "2025-01-13T10:00:00Z"
            },
            {
                "id": "file_old_002", 
                "name": "dealership_kb_financing-options.md",
                "originalName": "financing-options.md",
                "status": "done",
                "bytes": 7168,
                "createdAt": "2025-01-13T10:00:00Z"
            },
            {
                "id": "file_unrelated_003",
                "name": "some_other_file.pdf",
                "originalName": "other.pdf",
                "status": "done", 
                "bytes": 1024,
                "createdAt": "2025-01-13T09:00:00Z"
            }
        ]

    @pytest.fixture
    def mock_new_file_uploads(self):
        """Sample successful file upload responses"""
        return [
            {
                "id": "file_new_001",
                "name": "dealership_kb_about-company.md",
                "originalName": "about-company.md",
                "status": "processing",
                "bytes": 5120,
                "createdAt": "2025-01-14T10:30:00Z"
            },
            {
                "id": "file_new_002",
                "name": "dealership_kb_financing-options.md", 
                "originalName": "financing-options.md",
                "status": "processing",
                "bytes": 8192,
                "createdAt": "2025-01-14T10:30:00Z"
            },
            {
                "id": "file_new_003",
                "name": "dealership_kb_services-provided.md",
                "originalName": "services-provided.md", 
                "status": "processing",
                "bytes": 12288,
                "createdAt": "2025-01-14T10:30:00Z"
            },
            {
                "id": "file_new_004",
                "name": "dealership_kb_current-offers.md",
                "originalName": "current-offers.md",
                "status": "processing", 
                "bytes": 6144,
                "createdAt": "2025-01-14T10:30:00Z"
            }
        ]

    @pytest.mark.asyncio
    async def test_sync_knowledge_base_success_full_workflow(
        self, mock_vapi_credentials, mock_markdown_files, mock_existing_files, mock_new_file_uploads
    ):
        """Test complete successful sync workflow"""
        with patch('kb_tools.sync_knowledge_base._list_existing_files') as mock_list, \
             patch('kb_tools.sync_knowledge_base._delete_existing_files') as mock_delete, \
             patch('kb_tools.sync_knowledge_base._upload_markdown_files') as mock_upload, \
             patch('kb_tools.sync_knowledge_base._update_knowledge_base_tool') as mock_update:
            
            # Mock the helper functions
            mock_list.return_value = mock_existing_files
            mock_delete.return_value = 2  # 2 files deleted
            mock_upload.return_value = ["file_new_001", "file_new_002", "file_new_003", "file_new_004"]
            mock_update.return_value = None
            
            result = await sync_knowledge_base(
                vapi_api_key=mock_vapi_credentials["vapi_api_key"],
                knowledge_base_tool_id=mock_vapi_credentials["knowledge_base_tool_id"],
                markdown_files=mock_markdown_files,
                file_name_prefix="dealership_kb_"
            )
            
            # Verify result structure
            assert result["success"] is True
            assert result["files_deleted"] == 2
            assert result["files_uploaded"] == 4
            assert result["tool_updated"] is True
            assert result["knowledge_base_tool_id"] == "tool_kb_456"
            assert len(result["new_file_ids"]) == 4
            assert "sync_duration_ms" in result
            
            # Verify helper functions were called
            mock_list.assert_called_once()
            mock_delete.assert_called_once()
            mock_upload.assert_called_once()
            mock_update.assert_called_once()

    @pytest.mark.asyncio
    async def test_sync_knowledge_base_no_existing_files(
        self, mock_vapi_credentials, mock_markdown_files, mock_new_file_uploads
    ):
        """Test sync when no existing knowledge base files"""
        with patch('kb_tools.sync_knowledge_base._list_existing_files') as mock_list, \
             patch('kb_tools.sync_knowledge_base._delete_existing_files') as mock_delete, \
             patch('kb_tools.sync_knowledge_base._upload_markdown_files') as mock_upload, \
             patch('kb_tools.sync_knowledge_base._update_knowledge_base_tool') as mock_update:
            
            # Mock empty file list
            mock_list.return_value = []
            mock_delete.return_value = 0  # No files deleted
            mock_upload.return_value = ["file_new_001", "file_new_002", "file_new_003", "file_new_004"]
            mock_update.return_value = None
            
            result = await sync_knowledge_base(
                vapi_api_key=mock_vapi_credentials["vapi_api_key"],
                knowledge_base_tool_id=mock_vapi_credentials["knowledge_base_tool_id"],
                markdown_files=mock_markdown_files
            )
            
            assert result["success"] is True
            assert result["files_deleted"] == 0  # No files to delete
            assert result["files_uploaded"] == 4
            assert result["tool_updated"] is True
            
            # Should not call delete since no KB files exist
            mock_delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_sync_knowledge_base_empty_markdown_files(self, mock_vapi_credentials):
        """Test sync with empty markdown files list"""
        with pytest.raises(ValueError) as exc_info:
            await sync_knowledge_base(
                vapi_api_key=mock_vapi_credentials["vapi_api_key"],
                knowledge_base_tool_id=mock_vapi_credentials["knowledge_base_tool_id"],
                markdown_files=[]
            )
        
        assert "at least one markdown file" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_sync_knowledge_base_invalid_credentials(self, mock_markdown_files):
        """Test sync with invalid credentials"""
        with pytest.raises(ValueError) as exc_info:
            await sync_knowledge_base(
                vapi_api_key="",
                knowledge_base_tool_id="tool_123",
                markdown_files=mock_markdown_files
            )
        
        assert "API key" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_sync_knowledge_base_list_files_error(self, mock_vapi_credentials, mock_markdown_files):
        """Test handling of file listing errors"""
        with patch('kb_tools.sync_knowledge_base._list_existing_files') as mock_list:
            # Mock list files error
            mock_list.side_effect = Exception("Failed to list files: HTTP 403")
            
            with pytest.raises(Exception) as exc_info:
                await sync_knowledge_base(
                    vapi_api_key=mock_vapi_credentials["vapi_api_key"],
                    knowledge_base_tool_id=mock_vapi_credentials["knowledge_base_tool_id"],
                    markdown_files=mock_markdown_files
                )
            
            assert "list files" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_sync_knowledge_base_delete_file_error(
        self, mock_vapi_credentials, mock_markdown_files, mock_existing_files
    ):
        """Test handling of file deletion errors"""
        with patch('kb_tools.sync_knowledge_base._list_existing_files') as mock_list, \
             patch('kb_tools.sync_knowledge_base._delete_existing_files') as mock_delete:
            
            # Mock successful file listing
            mock_list.return_value = mock_existing_files
            # Mock delete error
            mock_delete.side_effect = Exception("Failed to delete file file_old_001: HTTP 404")
            
            with pytest.raises(Exception) as exc_info:
                await sync_knowledge_base(
                    vapi_api_key=mock_vapi_credentials["vapi_api_key"],
                    knowledge_base_tool_id=mock_vapi_credentials["knowledge_base_tool_id"],
                    markdown_files=mock_markdown_files,
                    file_name_prefix="dealership_kb_"
                )
            
            assert "delete file" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_sync_knowledge_base_upload_file_error(
        self, mock_vapi_credentials, mock_markdown_files
    ):
        """Test handling of file upload errors"""
        with patch('kb_tools.sync_knowledge_base._list_existing_files') as mock_list, \
             patch('kb_tools.sync_knowledge_base._delete_existing_files') as mock_delete, \
             patch('kb_tools.sync_knowledge_base._upload_markdown_files') as mock_upload:
            
            # Mock successful file listing (no existing files)
            mock_list.return_value = []
            mock_delete.return_value = 0
            # Mock upload error
            mock_upload.side_effect = Exception("Failed to upload file about-company.md: HTTP 400")
            
            with pytest.raises(Exception) as exc_info:
                await sync_knowledge_base(
                    vapi_api_key=mock_vapi_credentials["vapi_api_key"],
                    knowledge_base_tool_id=mock_vapi_credentials["knowledge_base_tool_id"],
                    markdown_files=mock_markdown_files
                )
            
            assert "upload file" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_sync_knowledge_base_tool_update_error(
        self, mock_vapi_credentials, mock_markdown_files, mock_new_file_uploads
    ):
        """Test handling of tool update errors"""
        with patch('kb_tools.sync_knowledge_base._list_existing_files') as mock_list, \
             patch('kb_tools.sync_knowledge_base._delete_existing_files') as mock_delete, \
             patch('kb_tools.sync_knowledge_base._upload_markdown_files') as mock_upload, \
             patch('kb_tools.sync_knowledge_base._update_knowledge_base_tool') as mock_update:
            
            # Mock successful file operations
            mock_list.return_value = []
            mock_delete.return_value = 0
            mock_upload.return_value = ["file_new_001", "file_new_002", "file_new_003", "file_new_004"]
            # Mock tool update error
            mock_update.side_effect = Exception("Failed to update tool tool_kb_456: HTTP 404")
            
            with pytest.raises(Exception) as exc_info:
                await sync_knowledge_base(
                    vapi_api_key=mock_vapi_credentials["vapi_api_key"],
                    knowledge_base_tool_id=mock_vapi_credentials["knowledge_base_tool_id"],
                    markdown_files=mock_markdown_files
                )
            
            assert "update tool" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_sync_knowledge_base_custom_prefix(
        self, mock_vapi_credentials, mock_markdown_files, mock_new_file_uploads
    ):
        """Test sync with custom file name prefix"""
        custom_prefix = "custom_kb_"
        
        with patch('kb_tools.sync_knowledge_base._list_existing_files') as mock_list, \
             patch('kb_tools.sync_knowledge_base._delete_existing_files') as mock_delete, \
             patch('kb_tools.sync_knowledge_base._upload_markdown_files') as mock_upload, \
             patch('kb_tools.sync_knowledge_base._update_knowledge_base_tool') as mock_update:
            
            # Mock file listing with custom prefix files
            existing_files = [
                {
                    "id": "file_custom_001",
                    "name": f"{custom_prefix}about-company.md",
                    "status": "done"
                }
            ]
            mock_list.return_value = existing_files
            mock_delete.return_value = 1  # One custom prefix file deleted
            mock_upload.return_value = ["file_new_001", "file_new_002", "file_new_003", "file_new_004"]
            mock_update.return_value = None
            
            result = await sync_knowledge_base(
                vapi_api_key=mock_vapi_credentials["vapi_api_key"],
                knowledge_base_tool_id=mock_vapi_credentials["knowledge_base_tool_id"],
                markdown_files=mock_markdown_files,
                file_name_prefix=custom_prefix
            )
            
            assert result["success"] is True
            assert result["files_deleted"] == 1  # One custom prefix file deleted

    @pytest.mark.asyncio
    async def test_sync_knowledge_base_network_error(self, mock_vapi_credentials, mock_markdown_files):
        """Test handling of network errors"""
        with patch('kb_tools.sync_knowledge_base._list_existing_files') as mock_list:
            # Mock network error in list files
            mock_list.side_effect = Exception("Network error during sync: Connection failed")
            
            with pytest.raises(Exception) as exc_info:
                await sync_knowledge_base(
                    vapi_api_key=mock_vapi_credentials["vapi_api_key"],
                    knowledge_base_tool_id=mock_vapi_credentials["knowledge_base_tool_id"],
                    markdown_files=mock_markdown_files
                )
            
            error_msg = str(exc_info.value).lower()
            assert "network" in error_msg

    @pytest.mark.asyncio
    async def test_sync_knowledge_base_timeout_error(self, mock_vapi_credentials, mock_markdown_files):
        """Test handling of timeout errors"""
        with patch('kb_tools.sync_knowledge_base._list_existing_files') as mock_list:
            # Mock timeout error in list files
            mock_list.side_effect = Exception("Request timeout during sync: Request timed out")
            
            with pytest.raises(Exception) as exc_info:
                await sync_knowledge_base(
                    vapi_api_key=mock_vapi_credentials["vapi_api_key"],
                    knowledge_base_tool_id=mock_vapi_credentials["knowledge_base_tool_id"],
                    markdown_files=mock_markdown_files
                )
            
            error_msg = str(exc_info.value).lower()
            assert "timeout" in error_msg

    @pytest.mark.asyncio
    async def test_sync_knowledge_base_partial_upload_failure(
        self, mock_vapi_credentials, mock_markdown_files
    ):
        """Test handling when some file uploads fail"""
        with patch('kb_tools.sync_knowledge_base._list_existing_files') as mock_list, \
             patch('kb_tools.sync_knowledge_base._delete_existing_files') as mock_delete, \
             patch('kb_tools.sync_knowledge_base._upload_markdown_files') as mock_upload:
            
            # Mock successful file operations leading to upload failure
            mock_list.return_value = []
            mock_delete.return_value = 0
            # Mock upload failure (simulating partial failure)
            mock_upload.side_effect = Exception("Failed to upload file financing-options.md: HTTP 400")
            
            with pytest.raises(Exception) as exc_info:
                await sync_knowledge_base(
                    vapi_api_key=mock_vapi_credentials["vapi_api_key"],
                    knowledge_base_tool_id=mock_vapi_credentials["knowledge_base_tool_id"],
                    markdown_files=mock_markdown_files
                )
            
            # Should fail on first upload error for data integrity
            assert "upload file" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_sync_knowledge_base_authentication_headers(
        self, mock_vapi_credentials, mock_markdown_files
    ):
        """Test proper authentication headers are set"""
        with patch('httpx.AsyncClient') as mock_client, \
             patch('kb_tools.sync_knowledge_base._list_existing_files') as mock_list, \
             patch('kb_tools.sync_knowledge_base._delete_existing_files') as mock_delete, \
             patch('kb_tools.sync_knowledge_base._upload_markdown_files') as mock_upload, \
             patch('kb_tools.sync_knowledge_base._update_knowledge_base_tool') as mock_update:
            
            # Mock successful operations
            mock_list.return_value = []
            mock_delete.return_value = 0
            mock_upload.return_value = ["file_001"]
            mock_update.return_value = None
            
            # Mock the async context manager
            mock_client.return_value.__aenter__ = AsyncMock()
            mock_client.return_value.__aexit__ = AsyncMock()
            
            await sync_knowledge_base(
                vapi_api_key=mock_vapi_credentials["vapi_api_key"],
                knowledge_base_tool_id=mock_vapi_credentials["knowledge_base_tool_id"],
                markdown_files=mock_markdown_files[:1]  # Just one file for simplicity
            )
            
            # Verify authentication headers were passed to client
            mock_client.assert_called_once()
            call_kwargs = mock_client.call_args[1]
            assert "headers" in call_kwargs
            assert "Authorization" in call_kwargs["headers"]
            assert f"Bearer {mock_vapi_credentials['vapi_api_key']}" in call_kwargs["headers"]["Authorization"]

    @pytest.mark.asyncio
    async def test_sync_knowledge_base_file_name_formatting(
        self, mock_vapi_credentials, mock_markdown_files, mock_new_file_uploads
    ):
        """Test proper file name formatting for uploads"""
        with patch('kb_tools.sync_knowledge_base._list_existing_files') as mock_list, \
             patch('kb_tools.sync_knowledge_base._delete_existing_files') as mock_delete, \
             patch('kb_tools.sync_knowledge_base._upload_markdown_files') as mock_upload, \
             patch('kb_tools.sync_knowledge_base._update_knowledge_base_tool') as mock_update:
            
            # Mock operations
            mock_list.return_value = []
            mock_delete.return_value = 0
            mock_upload.return_value = ["file_new_001", "file_new_002", "file_new_003", "file_new_004"]
            mock_update.return_value = None
            
            await sync_knowledge_base(
                vapi_api_key=mock_vapi_credentials["vapi_api_key"],
                knowledge_base_tool_id=mock_vapi_credentials["knowledge_base_tool_id"],
                markdown_files=mock_markdown_files,
                file_name_prefix="kb_"
            )
            
            # Verify upload was called with correct parameters
            mock_upload.assert_called_once()
            call_args = mock_upload.call_args[0]
            # Should be called with client, markdown_files, and file_name_prefix
            assert len(call_args) == 3
            assert call_args[1] == mock_markdown_files  # markdown_files
            assert call_args[2] == "kb_"  # file_name_prefix
