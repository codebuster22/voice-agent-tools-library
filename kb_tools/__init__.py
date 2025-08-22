"""
Knowledge Base Tools for Car Dealership Voice Agent

This package provides tools for synchronizing knowledge base content
between GitHub repositories and Vapi's knowledge base system.
"""

from .fetch_latest_kb import fetch_latest_kb
from .sync_knowledge_base import sync_knowledge_base

__all__ = [
    "fetch_latest_kb",
    "sync_knowledge_base"
]
