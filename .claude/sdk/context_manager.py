"""
Context and state management system
"""

import json
import asyncio
import aiofiles
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import uuid

logger = logging.getLogger(__name__)


class ContextManager:
    """Manages context and state across agent interactions"""
    
    def __init__(self, storage_path: str = ".claude/context"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # In-memory context cache
        self.context_cache = {}
        self.session_contexts = {}
        
        # Current session
        self.current_session_id = None
        
        # Context expiration settings
        self.default_ttl = timedelta(hours=24)
        self.max_cache_size = 1000
        
    async def initialize(self):
        """Initialize context manager"""
        self.current_session_id = str(uuid.uuid4())
        logger.info(f"Context manager initialized with session: {self.current_session_id}")
        
        # Load existing contexts
        await self._load_existing_contexts()
    
    async def _load_existing_contexts(self):
        """Load existing context files"""
        try:
            for context_file in self.storage_path.glob("*.json"):
                if not context_file.name.startswith("session_"):
                    continue
                    
                try:
                    async with aiofiles.open(context_file, 'r') as f:
                        content = await f.read()
                        data = json.loads(content)
                        
                        # Check if context is expired
                        created_at = datetime.fromisoformat(data.get("created_at", ""))
                        if datetime.now() - created_at < self.default_ttl:
                            agent_name = data.get("agent_name", "unknown")
                            self.context_cache[f"{agent_name}_{data.get('session_id', '')}"] = data
                            
                except Exception as e:
                    logger.warning(f"Failed to load context file {context_file}: {e}")
                    
        except Exception as e:
            logger.error(f"Failed to load existing contexts: {e}")
    
    async def save_context(self, agent_name: str, context: Dict[str, Any], 
                          session_id: Optional[str] = None):
        """Save agent context to persistent storage"""
        session_id = session_id or self.current_session_id
        
        context_data = {
            "agent_name": agent_name,
            "session_id": session_id,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "context": context
        }
        
        # Save to cache
        cache_key = f"{agent_name}_{session_id}"
        self.context_cache[cache_key] = context_data
        
        # Save to file
        file_path = self.storage_path / f"session_{session_id}_{agent_name}.json"
        try:
            async with aiofiles.open(file_path, 'w') as f:
                await f.write(json.dumps(context_data, indent=2))
            
            logger.debug(f"Saved context for {agent_name} in session {session_id}")
            
        except Exception as e:
            logger.error(f"Failed to save context for {agent_name}: {e}")
        
        # Manage cache size
        await self._cleanup_cache()
    
    async def load_context(self, agent_name: str, 
                          session_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Load agent context from storage"""
        session_id = session_id or self.current_session_id
        cache_key = f"{agent_name}_{session_id}"
        
        # Check cache first
        if cache_key in self.context_cache:
            context_data = self.context_cache[cache_key]
            
            # Check expiration
            created_at = datetime.fromisoformat(context_data["created_at"])
            if datetime.now() - created_at < self.default_ttl:
                return context_data["context"]
            else:
                # Remove expired context
                del self.context_cache[cache_key]
        
        # Try to load from file
        file_path = self.storage_path / f"session_{session_id}_{agent_name}.json"
        if file_path.exists():
            try:
                async with aiofiles.open(file_path, 'r') as f:
                    content = await f.read()
                    context_data = json.loads(content)
                    
                    # Check expiration
                    created_at = datetime.fromisoformat(context_data["created_at"])
                    if datetime.now() - created_at < self.default_ttl:
                        # Add back to cache
                        self.context_cache[cache_key] = context_data
                        return context_data["context"]
                    else:
                        # Remove expired file
                        file_path.unlink()
                        
            except Exception as e:
                logger.error(f"Failed to load context for {agent_name}: {e}")
        
        return None
    
    async def share_context(self, source_agent: str, target_agent: str, 
                           context_keys: List[str], session_id: Optional[str] = None):
        """Share specific context between agents"""
        session_id = session_id or self.current_session_id
        
        source_context = await self.load_context(source_agent, session_id)
        if not source_context:
            logger.warning(f"No context found for source agent {source_agent}")
            return
        
        # Extract specified keys
        shared_context = {}
        for key in context_keys:
            if key in source_context:
                shared_context[key] = source_context[key]
        
        if not shared_context:
            logger.warning(f"No matching context keys found for sharing")
            return
        
        # Merge with target context
        target_context = await self.load_context(target_agent, session_id) or {}
        target_context.update(shared_context)
        
        # Add metadata about the sharing
        target_context["_shared_from"] = {
            "source_agent": source_agent,
            "shared_keys": context_keys,
            "shared_at": datetime.now().isoformat()
        }
        
        await self.save_context(target_agent, target_context, session_id)
        
        logger.info(f"Shared context from {source_agent} to {target_agent}: {context_keys}")
    
    async def get_session_context(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Get all context for a session"""
        session_id = session_id or self.current_session_id
        
        session_context = {}
        for cache_key, context_data in self.context_cache.items():
            if context_data["session_id"] == session_id:
                agent_name = context_data["agent_name"]
                session_context[agent_name] = context_data["context"]
        
        return session_context
    
    async def clear_context(self, agent_name: str, session_id: Optional[str] = None):
        """Clear context for specific agent"""
        session_id = session_id or self.current_session_id
        cache_key = f"{agent_name}_{session_id}"
        
        # Remove from cache
        if cache_key in self.context_cache:
            del self.context_cache[cache_key]
        
        # Remove file
        file_path = self.storage_path / f"session_{session_id}_{agent_name}.json"
        if file_path.exists():
            file_path.unlink()
        
        logger.info(f"Cleared context for {agent_name}")
    
    async def clear_session(self, session_id: Optional[str] = None):
        """Clear all context for a session"""
        session_id = session_id or self.current_session_id
        
        # Remove from cache
        cache_keys_to_remove = [
            key for key, data in self.context_cache.items()
            if data["session_id"] == session_id
        ]
        
        for key in cache_keys_to_remove:
            del self.context_cache[key]
        
        # Remove files
        for context_file in self.storage_path.glob(f"session_{session_id}_*.json"):
            context_file.unlink()
        
        logger.info(f"Cleared session context: {session_id}")
    
    async def _cleanup_cache(self):
        """Clean up cache if it's too large"""
        if len(self.context_cache) <= self.max_cache_size:
            return
        
        # Sort by last updated time and remove oldest
        cache_items = list(self.context_cache.items())
        cache_items.sort(key=lambda x: x[1].get("updated_at", ""))
        
        items_to_remove = len(cache_items) - self.max_cache_size
        for i in range(items_to_remove):
            key = cache_items[i][0]
            del self.context_cache[key]
        
        logger.info(f"Cleaned up {items_to_remove} items from context cache")
    
    async def cleanup_expired(self):
        """Clean up expired contexts"""
        current_time = datetime.now()
        expired_keys = []
        
        for key, data in self.context_cache.items():
            created_at = datetime.fromisoformat(data["created_at"])
            if current_time - created_at > self.default_ttl:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.context_cache[key]
        
        # Clean up expired files
        for context_file in self.storage_path.glob("session_*.json"):
            try:
                async with aiofiles.open(context_file, 'r') as f:
                    content = await f.read()
                    data = json.loads(content)
                    created_at = datetime.fromisoformat(data["created_at"])
                    
                    if current_time - created_at > self.default_ttl:
                        context_file.unlink()
                        
            except Exception as e:
                logger.warning(f"Error checking expiration for {context_file}: {e}")
        
        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired contexts")
    
    def get_context_stats(self) -> Dict[str, Any]:
        """Get context manager statistics"""
        total_contexts = len(self.context_cache)
        sessions = set(data["session_id"] for data in self.context_cache.values())
        agents = set(data["agent_name"] for data in self.context_cache.values())
        
        return {
            "total_contexts": total_contexts,
            "active_sessions": len(sessions),
            "agents_with_context": len(agents),
            "current_session": self.current_session_id,
            "storage_path": str(self.storage_path),
            "cache_size": len(self.context_cache),
            "max_cache_size": self.max_cache_size
        }
    
    async def export_session(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Export session context to a single data structure"""
        session_id = session_id or self.current_session_id
        session_data = await self.get_session_context(session_id)
        
        return {
            "session_id": session_id,
            "exported_at": datetime.now().isoformat(),
            "contexts": session_data
        }
    
    async def import_session(self, session_data: Dict[str, Any]):
        """Import session context from exported data"""
        session_id = session_data.get("session_id")
        contexts = session_data.get("contexts", {})
        
        if not session_id:
            raise ValueError("Session ID required for import")
        
        for agent_name, context in contexts.items():
            await self.save_context(agent_name, context, session_id)
        
        logger.info(f"Imported session {session_id} with {len(contexts)} agent contexts")
    
    async def shutdown(self):
        """Shutdown context manager and cleanup"""
        logger.info("Shutting down context manager...")
        
        # Final cleanup of expired contexts
        await self.cleanup_expired()
        
        # Save any pending contexts
        # (contexts are already saved on each update)
        
        logger.info("Context manager shutdown complete")