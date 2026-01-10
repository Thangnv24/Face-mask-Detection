"""
Tracker Manager for Face Mask Detection with BoT-SORT

This module manages tracking sessions for video/webcam streams, providing:
- Session-based state management for stateless HTTP API
- Label smoothing via temporal voting to reduce flicker
- Automatic cleanup of inactive sessions
"""

import time
from collections import defaultdict, deque
from typing import Dict, Tuple, Optional, List
from dataclasses import dataclass
import threading


@dataclass
class TrackPrediction:
    """Stores a single prediction for a track."""
    label: str
    confidence: float
    timestamp: float


class TrackerSession:
    """
    Manages tracking state and prediction history for a single session.
    
    Attributes:
        history_size: Number of frames to keep for label smoothing
        track_history: Dict mapping track_id -> deque of predictions
        last_activity: Timestamp of last update
    """
    
    def __init__(self, history_size: int = 5):
        self.history_size = history_size
        self.track_history: Dict[int, deque] = defaultdict(lambda: deque(maxlen=history_size))
        self.last_activity = time.time()
    
    def update_track(self, track_id: int, label: str, confidence: float):
        """
        Add a new prediction to the track's history.
        
        Args:
            track_id: Unique identifier for the tracked face
            label: Prediction label ("Mask" or "No Mask")
            confidence: Prediction confidence (0-1)
        """
        prediction = TrackPrediction(
            label=label,
            confidence=confidence,
            timestamp=time.time()
        )
        self.track_history[track_id].append(prediction)
        self.last_activity = time.time()
    
    def get_smoothed_prediction(self, track_id: int) -> Tuple[str, float]:
        """
        Get smoothed prediction using majority voting over history.
        
        Args:
            track_id: Track ID to get prediction for
            
        Returns:
            Tuple of (label, average_confidence)
        """
        history = self.track_history[track_id]
        
        if not history:
            return "Unknown", 0.0
        
        # Count votes for each label
        label_votes = defaultdict(list)
        for pred in history:
            label_votes[pred.label].append(pred.confidence)
        
        # Find label with most votes
        winner_label = max(label_votes.keys(), key=lambda k: len(label_votes[k]))
        
        # Calculate average confidence for winning label
        avg_confidence = sum(label_votes[winner_label]) / len(label_votes[winner_label])
        
        return winner_label, avg_confidence
    
    def is_active(self, timeout_seconds: int = 300) -> bool:
        """
        Check if session is still active.
        
        Args:
            timeout_seconds: Inactive timeout in seconds (default: 5 minutes)
            
        Returns:
            True if session has been active within timeout period
        """
        return (time.time() - self.last_activity) < timeout_seconds


class TrackerSessionManager:
    """
    Global manager for all tracking sessions.
    
    Maintains a registry of sessions indexed by session_id and provides
    automatic cleanup of inactive sessions.
    """
    
    def __init__(self, cleanup_interval: int = 60, session_timeout: int = 300):
        """
        Initialize the session manager.
        
        Args:
            cleanup_interval: How often to run cleanup (seconds)
            session_timeout: Inactive session timeout (seconds)
        """
        self.sessions: Dict[str, TrackerSession] = {}
        self.cleanup_interval = cleanup_interval
        self.session_timeout = session_timeout
        self._lock = threading.Lock()
        
        # Start cleanup thread
        self._cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self._cleanup_thread.start()
    
    def get_or_create_session(self, session_id: str, history_size: int = 5) -> TrackerSession:
        """
        Get existing session or create new one.
        
        Args:
            session_id: Unique session identifier
            history_size: Number of frames for smoothing
            
        Returns:
            TrackerSession instance
        """
        with self._lock:
            if session_id not in self.sessions:
                self.sessions[session_id] = TrackerSession(history_size)
            return self.sessions[session_id]
    
    def remove_session(self, session_id: str):
        """Remove a session from the registry."""
        with self._lock:
            if session_id in self.sessions:
                del self.sessions[session_id]
    
    def _cleanup_loop(self):
        """Background thread that removes inactive sessions."""
        while True:
            time.sleep(self.cleanup_interval)
            self._cleanup_inactive_sessions()
    
    def _cleanup_inactive_sessions(self):
        """Remove sessions that have been inactive."""
        with self._lock:
            inactive_sessions = [
                session_id 
                for session_id, session in self.sessions.items()
                if not session.is_active(self.session_timeout)
            ]
            
            for session_id in inactive_sessions:
                del self.sessions[session_id]
                print(f"[TrackerManager] Cleaned up inactive session: {session_id}")
    
    def get_session_count(self) -> int:
        """Get current number of active sessions."""
        with self._lock:
            return len(self.sessions)


# Global singleton instance
_session_manager = TrackerSessionManager()


def get_session_manager() -> TrackerSessionManager:
    """Get the global session manager instance."""
    return _session_manager
