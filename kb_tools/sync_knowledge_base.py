"""
Vapi Knowledge Base Synchronizer

Complete workflow for synchronizing knowledge base files with Vapi:
1. List existing files
2. Delete matching knowledge base files  
3. Upload new markdown files
4. Update knowledge base tool with new file IDs
"""

import asyncio
import httpx
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
import io

# Load environment variables
load_dotenv()


async def sync_knowledge_base(
    knowledge_base_tool_id: str,
    markdown_files: List[Dict[str, str]],
    file_name_prefix: str = "kb_",
    vapi_base_url: str = "https://api.vapi.ai",
    timeout_seconds: int = 30
) -> Dict[str, Any]:
    """
    Complete Vapi knowledge base synchronization workflow
    
    Args:
        knowledge_base_tool_id: Existing knowledge base tool ID to update
        markdown_files: List of markdown files from fetch_latest_kb
        file_name_prefix: Prefix for knowledge base file identification  
        vapi_base_url: Vapi API base URL
        timeout_seconds: Request timeout in seconds
        
    Returns:
        Dict containing sync results and metadata
        
    Raises:
        ValueError: Invalid input parameters
        Exception: API, network, or processing errors
    """
    # Get API key from environment
    vapi_api_key = os.getenv("VAPI_API_KEY")
    if not vapi_api_key:
        raise ValueError("VAPI_API_KEY environment variable is required")
    
    if not knowledge_base_tool_id or not knowledge_base_tool_id.strip():
        raise ValueError("Knowledge base tool ID is required")
    
    if not markdown_files:
        raise ValueError("Must provide at least one markdown file")
    
    # Validate markdown files structure
    for file_data in markdown_files:
        if not all(key in file_data for key in ["filename", "content"]):
            raise ValueError("Each markdown file must have 'filename' and 'content' fields")
    
    start_time = datetime.now()
    
    # Configure HTTP client with authentication
    headers = {
        "Authorization": f"Bearer {vapi_api_key}",
        "User-Agent": "Elite Motors KB Sync Tool/1.0"
    }
    
    files_deleted = 0
    files_uploaded = 0
    new_file_ids = []
    
    try:
        async with httpx.AsyncClient(
            timeout=timeout_seconds, 
            headers=headers,
            base_url=vapi_base_url
        ) as client:
            
            # Step 1: List existing files
            existing_files = await _list_existing_files(client)
            
            # Step 2: Delete matching knowledge base files
            kb_files_to_delete = [
                file for file in existing_files 
                if file.get("name", "").startswith(file_name_prefix)
            ]
            
            if kb_files_to_delete:
                files_deleted = await _delete_existing_files(client, kb_files_to_delete)
            
            # Step 3: Upload new markdown files
            new_file_ids = await _upload_markdown_files(
                client, markdown_files, file_name_prefix
            )
            files_uploaded = len(new_file_ids)
            
            # Step 4: Update knowledge base tool with new file IDs
            await _update_knowledge_base_tool(client, knowledge_base_tool_id, new_file_ids)
    
    except httpx.NetworkError as e:
        raise Exception(f"Network error during sync: {str(e)}")
    except httpx.TimeoutException as e:
        raise Exception(f"Request timeout during sync: {str(e)}")
    except Exception as e:
        if "list files" in str(e).lower() or "delete file" in str(e).lower() or \
           "upload file" in str(e).lower() or "update tool" in str(e).lower():
            raise
        raise Exception(f"Error during knowledge base sync: {str(e)}")
    
    end_time = datetime.now()
    sync_duration_ms = (end_time - start_time).total_seconds() * 1000
    
    return {
        "success": True,
        "files_deleted": files_deleted,
        "files_uploaded": files_uploaded,
        "new_file_ids": new_file_ids,
        "tool_updated": True,
        "knowledge_base_tool_id": knowledge_base_tool_id,
        "sync_duration_ms": round(sync_duration_ms, 2),
        "timestamp": end_time.isoformat()
    }


async def _list_existing_files(client: httpx.AsyncClient) -> List[Dict[str, Any]]:
    """
    List all existing files in Vapi
    
    Args:
        client: HTTP client instance
        
    Returns:
        List of existing file objects
    """
    try:
        response = await client.get("/file")
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        raise Exception(f"Failed to list files: HTTP {e.response.status_code}")
    except Exception as e:
        raise Exception(f"Failed to list files: {str(e)}")


async def _delete_existing_files(
    client: httpx.AsyncClient, 
    files_to_delete: List[Dict[str, Any]]
) -> int:
    """
    Delete existing knowledge base files
    
    Args:
        client: HTTP client instance
        files_to_delete: List of file objects to delete
        
    Returns:
        Number of files successfully deleted
    """
    deleted_count = 0
    
    for file_data in files_to_delete:
        file_id = file_data.get("id")
        if not file_id:
            continue
            
        try:
            response = await client.delete(f"/file/{file_id}")
            response.raise_for_status()
            deleted_count += 1
        except httpx.HTTPStatusError as e:
            raise Exception(f"Failed to delete file {file_id}: HTTP {e.response.status_code}")
        except Exception as e:
            raise Exception(f"Failed to delete file {file_id}: {str(e)}")
    
    return deleted_count


async def _upload_markdown_files(
    client: httpx.AsyncClient,
    markdown_files: List[Dict[str, str]],
    file_name_prefix: str
) -> List[str]:
    """
    Upload new markdown files to Vapi
    
    Args:
        client: HTTP client instance
        markdown_files: List of markdown file data
        file_name_prefix: Prefix for file names
        
    Returns:
        List of new file IDs
    """
    new_file_ids = []
    
    for file_data in markdown_files:
        filename = file_data["filename"]
        content = file_data["content"]
        
        # Create prefixed filename
        prefixed_filename = f"{file_name_prefix}{filename}"
        
        # Prepare multipart file data
        file_obj = io.StringIO(content)
        files = {
            "file": (prefixed_filename, file_obj, "text/markdown")
        }
        
        try:
            response = await client.post("/file", files=files)
            response.raise_for_status()
            
            upload_result = response.json()
            file_id = upload_result.get("id")
            
            if not file_id:
                raise Exception(f"No file ID returned for {filename}")
            
            new_file_ids.append(file_id)
            
        except httpx.HTTPStatusError as e:
            raise Exception(f"Failed to upload file {filename}: HTTP {e.response.status_code}")
        except Exception as e:
            raise Exception(f"Failed to upload file {filename}: {str(e)}")
        finally:
            file_obj.close()
    
    return new_file_ids


async def _update_knowledge_base_tool(
    client: httpx.AsyncClient,
    tool_id: str, 
    new_file_ids: List[str]
) -> None:
    """
    Update knowledge base tool with new file IDs
    
    Args:
        client: HTTP client instance
        tool_id: Knowledge base tool ID to update
        new_file_ids: List of new file IDs to associate with tool
    """
    tool_update_data = {
        "fileIds": new_file_ids
    }
    
    try:
        response = await client.patch(f"/tool/{tool_id}", json=tool_update_data)
        response.raise_for_status()
    except httpx.HTTPStatusError as e:
        raise Exception(f"Failed to update tool {tool_id}: HTTP {e.response.status_code}")
    except Exception as e:
        raise Exception(f"Failed to update tool {tool_id}: {str(e)}")
