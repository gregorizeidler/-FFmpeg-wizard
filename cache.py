"""
Caching and Optimization Module
Caches transcriptions and optimizes processing.
"""

import os
import json
import hashlib
import pickle
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import redis
from dotenv import load_dotenv

load_dotenv()


class CacheManager:
    """Manages caching for transcriptions and analysis."""
    
    def __init__(self, cache_dir: str = ".cache"):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        
        # Try to connect to Redis if available
        self.redis_client = None
        try:
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
            self.redis_client = redis.from_url(redis_url, decode_responses=False)
            self.redis_client.ping()
        except:
            self.redis_client = None
    
    def _get_file_hash(self, file_path: str) -> str:
        """Generate hash for file."""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def _get_cache_key(self, file_path: str, operation: str) -> str:
        """Generate cache key."""
        file_hash = self._get_file_hash(file_path)
        return f"{operation}:{file_hash}"
    
    def get_cached_transcription(self, audio_path: str) -> Optional[list]:
        """
        Get cached transcription if available.
        
        Args:
            audio_path: Path to audio file
        
        Returns:
            Cached word map or None
        """
        cache_key = self._get_cache_key(audio_path, "transcription")
        
        # Try Redis first
        if self.redis_client:
            try:
                cached = self.redis_client.get(cache_key)
                if cached:
                    return pickle.loads(cached)
            except:
                pass
        
        # Try file cache
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.pkl")
        if os.path.exists(cache_file):
            # Check if cache is still valid (7 days)
            if os.path.getmtime(cache_file) > (datetime.now() - timedelta(days=7)).timestamp():
                with open(cache_file, 'rb') as f:
                    return pickle.load(f)
        
        return None
    
    def cache_transcription(self, audio_path: str, word_map: list):
        """
        Cache transcription result.
        
        Args:
            audio_path: Path to audio file
            word_map: Transcription result
        """
        cache_key = self._get_cache_key(audio_path, "transcription")
        
        # Cache in Redis
        if self.redis_client:
            try:
                self.redis_client.setex(
                    cache_key,
                    7 * 24 * 60 * 60,  # 7 days
                    pickle.dumps(word_map)
                )
            except:
                pass
        
        # Cache in file
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.pkl")
        with open(cache_file, 'wb') as f:
            pickle.dump(word_map, f)
    
    def get_cached_analysis(self, cache_key: str) -> Optional[Dict]:
        """
        Get cached analysis result.
        
        Args:
            cache_key: Cache key
        
        Returns:
            Cached analysis or None
        """
        if self.redis_client:
            try:
                cached = self.redis_client.get(cache_key)
                if cached:
                    return json.loads(cached)
            except:
                pass
        
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        if os.path.exists(cache_file):
            if os.path.getmtime(cache_file) > (datetime.now() - timedelta(days=1)).timestamp():
                with open(cache_file, 'r') as f:
                    return json.load(f)
        
        return None
    
    def cache_analysis(self, cache_key: str, analysis: Dict):
        """
        Cache analysis result.
        
        Args:
            cache_key: Cache key
            analysis: Analysis result
        """
        if self.redis_client:
            try:
                self.redis_client.setex(
                    cache_key,
                    24 * 60 * 60,  # 1 day
                    json.dumps(analysis)
                )
            except:
                pass
        
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        with open(cache_file, 'w') as f:
            json.dump(analysis, f)
    
    def clear_cache(self, pattern: Optional[str] = None):
        """
        Clear cache.
        
        Args:
            pattern: Optional pattern to match
        """
        if pattern:
            # Clear matching files
            for filename in os.listdir(self.cache_dir):
                if pattern in filename:
                    os.remove(os.path.join(self.cache_dir, filename))
        else:
            # Clear all
            for filename in os.listdir(self.cache_dir):
                os.remove(os.path.join(self.cache_dir, filename))
        
        # Clear Redis if available
        if self.redis_client:
            try:
                if pattern:
                    keys = self.redis_client.keys(f"*{pattern}*")
                    if keys:
                        self.redis_client.delete(*keys)
                else:
                    self.redis_client.flushdb()
            except:
                pass
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics."""
        stats = {
            'file_count': 0,
            'total_size_mb': 0,
            'redis_enabled': self.redis_client is not None
        }
        
        if os.path.exists(self.cache_dir):
            for filename in os.listdir(self.cache_dir):
                filepath = os.path.join(self.cache_dir, filename)
                stats['file_count'] += 1
                stats['total_size_mb'] += os.path.getsize(filepath) / (1024 * 1024)
        
        if self.redis_client:
            try:
                stats['redis_keys'] = self.redis_client.dbsize()
            except:
                pass
        
        return stats

