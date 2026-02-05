"""
GUVI Agentic Scam HoneyPot - Database Layer
Session storage and retrieval
"""

import json
import sqlite3
from datetime import datetime
from typing import Optional, Dict, List
from pathlib import Path
import asyncio

from core.models import SessionState, Message, ScamDetectionResult, ExtractedIntelligence, EngagementMetrics
from core.config import settings


class Database:
    """SQLite database for session storage"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or settings.DATABASE_URL.replace("sqlite:///", "")
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """Initialize database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                created_at TEXT,
                updated_at TEXT,
                is_active INTEGER DEFAULT 1,
                callback_sent INTEGER DEFAULT 0,
                messages TEXT,
                detection_result TEXT,
                extracted_intelligence TEXT,
                engagement_metrics TEXT,
                agent_notes TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _get_conn(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def save_session(self, session: SessionState) -> bool:
        """Save or update session"""
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            
            # Serialize data
            messages_json = json.dumps([
                {"sender": m.sender, "text": m.text, "timestamp": m.timestamp}
                for m in session.messages
            ])
            
            detection_json = json.dumps(session.detection_result.model_dump()) if session.detectionResult else "{}"
            intel_json = json.dumps(session.extractedIntelligence.model_dump())
            metrics_json = json.dumps(session.engagementMetrics.model_dump())
            
            # Check if exists
            cursor.execute("SELECT session_id FROM sessions WHERE session_id = ?", (session.sessionId,))
            exists = cursor.fetchone()
            
            if exists:
                # Update
                cursor.execute('''
                    UPDATE sessions SET
                        updated_at = ?,
                        is_active = ?,
                        callback_sent = ?,
                        messages = ?,
                        detection_result = ?,
                        extracted_intelligence = ?,
                        engagement_metrics = ?,
                        agent_notes = ?
                    WHERE session_id = ?
                ''', (
                    session.updatedAt.isoformat(),
                    int(session.isActive),
                    int(session.callbackSent),
                    messages_json,
                    detection_json,
                    intel_json,
                    metrics_json,
                    session.agentNotes,
                    session.sessionId
                ))
            else:
                # Insert
                cursor.execute('''
                    INSERT INTO sessions 
                    (session_id, created_at, updated_at, is_active, callback_sent,
                     messages, detection_result, extracted_intelligence, 
                     engagement_metrics, agent_notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    session.sessionId,
                    session.createdAt.isoformat(),
                    session.updatedAt.isoformat(),
                    int(session.isActive),
                    int(session.callbackSent),
                    messages_json,
                    detection_json,
                    intel_json,
                    metrics_json,
                    session.agentNotes
                ))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"Database error: {e}")
            return False
    
    def get_session(self, session_id: str) -> Optional[SessionState]:
        """Get session by ID"""
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,))
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                return None
            
            return self._row_to_session(row)
            
        except Exception as e:
            print(f"Database error: {e}")
            return None
    
    def _row_to_session(self, row) -> SessionState:
        """Convert database row to SessionState"""
        columns = [
            "session_id", "created_at", "updated_at", "is_active", "callback_sent",
            "messages", "detection_result", "extracted_intelligence", 
            "engagement_metrics", "agent_notes"
        ]
        data = dict(zip(columns, row))
        
        # Parse messages
        messages = []
        if data.get("messages"):
            msg_list = json.loads(data["messages"])
            for m in msg_list:
                messages.append(Message(sender=m["sender"], text=m["text"], timestamp=m.get("timestamp")))
        
        # Parse detection result
        detection = None
        if data.get("detection_result") and data["detection_result"] != "{}":
            det_data = json.loads(data["detection_result"])
            from core.models import ScamType
            detection = ScamDetectionResult(
                scamDetected=det_data.get("scamDetected", False),
                confidenceScore=det_data.get("confidenceScore", 0),
                scamType=ScamType(det_data.get("scamType", "unknown")),
                indicators=det_data.get("indicators", []),
                reasoning=det_data.get("reasoning", "")
            )
        
        # Parse intelligence
        intel = ExtractedIntelligence()
        if data.get("extracted_intelligence"):
            intel_data = json.loads(data["extracted_intelligence"])
            intel = ExtractedIntelligence(**intel_data)
        
        # Parse metrics
        metrics = EngagementMetrics()
        if data.get("engagement_metrics"):
            met_data = json.loads(data["engagement_metrics"])
            metrics = EngagementMetrics(**met_data)
        
        return SessionState(
            sessionId=data["session_id"],
            createdAt=datetime.fromisoformat(data["created_at"]),
            updatedAt=datetime.fromisoformat(data["updated_at"]),
            messages=messages,
            detectionResult=detection,
            extractedIntelligence=intel,
            engagementMetrics=metrics,
            isActive=bool(data.get("is_active", 1)),
            callbackSent=bool(data.get("callback_sent", 0)),
            agentNotes=data.get("agent_notes", "")
        )
    
    def mark_callback_sent(self, session_id: str) -> bool:
        """Mark session as callback sent"""
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE sessions SET callback_sent = 1 WHERE session_id = ?",
                (session_id,)
            )
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Database error: {e}")
            return False


# Singleton instance
db = Database()


# Async wrappers
async def save_session(session: SessionState) -> bool:
    """Async wrapper for save_session"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, db.save_session, session)


async def get_session(session_id: str) -> Optional[SessionState]:
    """Async wrapper for get_session"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, db.get_session, session_id)


async def mark_callback_sent(session_id: str) -> bool:
    """Async wrapper for mark_callback_sent"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, db.mark_callback_sent, session_id)
