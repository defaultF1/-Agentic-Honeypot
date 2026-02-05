"""
Rate limiting and session management utilities.
"""

import time
import threading
from typing import Dict, Optional
from collections import defaultdict, deque
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Simple in-memory rate limiter using token bucket algorithm.
    """

    def __init__(self, max_requests: int = 20, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, deque] = defaultdict(deque)
        self._lock = threading.Lock()

    def is_allowed(self, key: str) -> bool:
        """
        Check if request is allowed under rate limit.

        Args:
            key: Identifier (e.g., API key or IP address)

        Returns:
            True if request allowed, False if rate limited
        """
        with self._lock:
            now = time.time()
            window_start = now - self.window_seconds

            # Clean old requests outside window
            if key in self.requests:
                while self.requests[key] and self.requests[key][0] < window_start:
                    self.requests[key].popleft()

            # Check if under limit
            if len(self.requests[key]) >= self.max_requests:
                logger.warning(f"Rate limit exceeded for key: {key[:8]}...")
                return False

            # Record this request
            self.requests[key].append(now)
            return True

    def get_retry_after(self, key: str) -> int:
        """Get seconds until rate limit resets."""
        with self._lock:
            if key not in self.requests or not self.requests[key]:
                return 0

            oldest = self.requests[key][0]
            retry_after = int(self.window_seconds - (time.time() - oldest)) + 1
            return max(retry_after, 1)

    def cleanup(self):
        """Clean up old entries."""
        with self._lock:
            now = time.time()
            window_start = now - self.window_seconds

            keys_to_remove = []
            for key, timestamps in self.requests.items():
                # Remove old timestamps
                while timestamps and timestamps[0] < window_start:
                    timestamps.popleft()

                # Mark empty entries for removal
                if not timestamps:
                    keys_to_remove.append(key)

            # Remove empty entries
            for key in keys_to_remove:
                del self.requests[key]


class SessionManager:
    """
    Manages session lifecycle with TTL-based cleanup.
    """

    def __init__(self, ttl_seconds: int = 3600):
        self.ttl_seconds = ttl_seconds
        self.sessions: Dict[str, dict] = {}
        self._lock = threading.Lock()
        self._last_cleanup = time.time()

    def get_or_create(self, session_id: Optional[str]) -> tuple[str, dict, bool]:
        """
        Get existing session or create new one.

        Returns:
            Tuple of (session_id, session_data, is_new)
        """
        with self._lock:
            # Periodic cleanup
            self._cleanup_if_needed()

            if session_id and session_id in self.sessions:
                session = self.sessions[session_id]
                # Update last accessed
                session["last_accessed"] = time.time()
                return session_id, session, False

            # Create new session
            import uuid

            new_id = str(uuid.uuid4())
            new_session = {
                "id": new_id,
                "created_at": time.time(),
                "last_accessed": time.time(),
                "turns": 0,
                "history": [],
                "persona": None,
                "intel_collected": [],
            }
            self.sessions[new_id] = new_session
            return new_id, new_session, True

    def update(self, session_id: str, updates: dict):
        """Update session data."""
        with self._lock:
            if session_id in self.sessions:
                self.sessions[session_id].update(updates)
                self.sessions[session_id]["last_accessed"] = time.time()

    def _cleanup_if_needed(self):
        """Clean up expired sessions if enough time passed."""
        now = time.time()
        if now - self._last_cleanup < 300:  # Cleanup every 5 minutes
            return

        self._cleanup()
        self._last_cleanup = now

    def _cleanup(self):
        """Remove expired sessions."""
        now = time.time()
        expired = []

        for session_id, session in self.sessions.items():
            last_accessed = session.get("last_accessed", session["created_at"])
            if now - last_accessed > self.ttl_seconds:
                expired.append(session_id)

        for session_id in expired:
            del self.sessions[session_id]
            logger.info(f"Cleaned up expired session: {session_id}")

        if expired:
            logger.info(f"Cleaned up {len(expired)} expired sessions")

    def get_stats(self) -> dict:
        """Get session statistics."""
        with self._lock:
            return {
                "total_sessions": len(self.sessions),
                "ttl_seconds": self.ttl_seconds,
            }


# Global instances
rate_limiter = RateLimiter()
session_manager = SessionManager()
