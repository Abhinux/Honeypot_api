"""
GUVI Agentic Scam HoneyPot - Callback Module
Sends final results to GUVI endpoint (MANDATORY)
"""

import httpx
import asyncio
from typing import Optional

from core.models import SessionState, GUVICallbackPayload
from core.config import settings


class GUVICallback:
    """
    Handles sending final results to GUVI callback endpoint
    
    MANDATORY: This callback must be sent for evaluation
    """
    
    def __init__(self):
        self.callback_url = settings.GUVI_CALLBACK_URL
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def send_callback(self, session: SessionState) -> bool:
        """
        Send final results to GUVI callback endpoint
        
        Args:
            session: Complete session state with all extracted intelligence
        
        Returns:
            True if callback was successful
        """
        try:
            # Build callback payload
            payload = GUVICallbackPayload(
                sessionId=session.sessionId,
                scamDetected=session.detectionResult.scamDetected if session.detectionResult else False,
                totalMessagesExchanged=session.engagementMetrics.totalMessagesExchanged,
                extractedIntelligence=session.extractedIntelligence,
                agentNotes=session.agentNotes
            )
            
            print(f"[CALLBACK] Sending results for session {session.sessionId}")
            print(f"[CALLBACK] URL: {self.callback_url}")
            print(f"[CALLBACK] Payload: {payload.model_dump_json(indent=2)}")
            
            # Send POST request to GUVI endpoint
            response = await self.client.post(
                self.callback_url,
                json=payload.model_dump(),
                headers={
                    "Content-Type": "application/json"
                }
            )
            
            if response.status_code == 200:
                print(f"[CALLBACK] ✅ Success! Status: {response.status_code}")
                print(f"[CALLBACK] Response: {response.text}")
                return True
            else:
                print(f"[CALLBACK] ❌ Failed! Status: {response.status_code}")
                print(f"[CALLBACK] Response: {response.text}")
                return False
                
        except httpx.TimeoutException:
            print(f"[CALLBACK] ❌ Timeout error")
            return False
        except Exception as e:
            print(f"[CALLBACK] ❌ Error: {e}")
            return False
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()


# Singleton instance
callback_client = GUVICallback()


async def send_guvi_callback(session: SessionState) -> bool:
    """
    Convenience function to send GUVI callback
    
    This is MANDATORY for evaluation - do not skip!
    """
    return await callback_client.send_callback(session)
