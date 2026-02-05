"""
GUVI Agentic Scam HoneyPot - Data Models
Strictly follows GUVI Hackathon specifications
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Literal
from datetime import datetime
from enum import Enum


class SenderType(str, Enum):
    """Message sender types"""
    SCAMMER = "scammer"
    USER = "user"
    AGENT = "agent"


class Message(BaseModel):
    """Individual message in conversation"""
    sender: Literal["scammer", "user", "agent"]
    text: str
    timestamp: Optional[int] = None  # Unix timestamp in milliseconds


class Metadata(BaseModel):
    """Message metadata"""
    channel: Optional[str] = "SMS"  # SMS, WhatsApp, Email, etc.
    language: Optional[str] = "English"
    locale: Optional[str] = "IN"


class IncomingRequest(BaseModel):
    """
    GUVI API Request Format
    
    {
      "sessionId": "unique-session-id",
      "message": {
        "sender": "scammer",
        "text": "Your account will be blocked today.",
        "timestamp": 1770005528731
      },
      "conversationHistory": [...],
      "metadata": {...}
    }
    """
    sessionId: str = Field(..., description="Unique session identifier")
    message: Message = Field(..., description="Current message")
    conversationHistory: List[Message] = Field(default_factory=list, description="Previous messages")
    metadata: Optional[Metadata] = Field(default_factory=Metadata)
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "sessionId": "sess_abc123",
                "message": {
                    "sender": "scammer",
                    "text": "Your account will be blocked today. Click here to verify.",
                    "timestamp": 1770005528731
                },
                "conversationHistory": [],
                "metadata": {
                    "channel": "SMS",
                    "language": "English",
                    "locale": "IN"
                }
            }
        }
    }


class AgentResponse(BaseModel):
    """
    GUVI API Response Format - MANDATORY
    
    {
      "status": "success",
      "reply": "<human-like message to scammer>"
    }
    """
    status: Literal["success", "error"] = "success"
    reply: str = Field(..., description="Human-like response to scammer")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "success",
                "reply": "Wait... why would my bank block my account? I didn't do anything wrong."
            }
        }
    }


class ScamType(str, Enum):
    """Types of scams"""
    BANK_FRAUD = "bank_fraud"
    UPI_FRAUD = "upi_fraud"
    PHISHING = "phishing"
    FAKE_OFFER = "fake_offer"
    OTP_HARVESTING = "otp_harvesting"
    UNKNOWN = "unknown"


class ScamDetectionResult(BaseModel):
    """Result of scam detection analysis"""
    scamDetected: bool = Field(default=False, description="Whether scam was detected")
    confidenceScore: float = Field(default=0.0, ge=0.0, le=1.0, description="Detection confidence")
    scamType: ScamType = Field(default=ScamType.UNKNOWN, description="Type of scam detected")
    indicators: List[str] = Field(default_factory=list, description="Detected scam indicators")
    reasoning: str = Field(default="", description="Internal reasoning for detection")


class ExtractedIntelligence(BaseModel):
    """
    Extracted actionable intelligence
    
    {
      "bankAccounts": [],
      "upiIds": [],
      "phishingLinks": [],
      "phoneNumbers": [],
      "suspiciousKeywords": []
    }
    """
    bankAccounts: List[str] = Field(default_factory=list)
    ifscCodes: List[str] = Field(default_factory=list)
    upiIds: List[str] = Field(default_factory=list)
    phishingLinks: List[str] = Field(default_factory=list)
    phoneNumbers: List[str] = Field(default_factory=list)
    suspiciousKeywords: List[str] = Field(default_factory=list)
    
    def has_intelligence(self) -> bool:
        """Check if any intelligence was extracted"""
        return any([
            self.bankAccounts,
            self.ifscCodes,
            self.upiIds,
            self.phishingLinks,
            self.phoneNumbers
        ])
    
    def get_summary(self) -> str:
        """Get summary of extracted intelligence"""
        items = []
        if self.bankAccounts:
            items.append(f"{len(self.bankAccounts)} bank account(s)")
        if self.upiIds:
            items.append(f"{len(self.upiIds)} UPI ID(s)")
        if self.phishingLinks:
            items.append(f"{len(self.phishingLinks)} phishing link(s)")
        if self.phoneNumbers:
            items.append(f"{len(self.phoneNumbers)} phone number(s)")
        return ", ".join(items) if items else "No actionable intelligence"


class EngagementMetrics(BaseModel):
    """Engagement tracking metrics"""
    totalMessagesExchanged: int = Field(default=0, ge=0)
    numberOfTurns: int = Field(default=0, ge=0)
    engagementDurationSeconds: float = Field(default=0.0, ge=0.0)
    scamDetectionConfidence: float = Field(default=0.0, ge=0.0, le=1.0)


class SessionState(BaseModel):
    """Complete session state"""
    sessionId: str
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)
    messages: List[Message] = Field(default_factory=list)
    detectionResult: Optional[ScamDetectionResult] = None
    extractedIntelligence: ExtractedIntelligence = Field(default_factory=ExtractedIntelligence)
    engagementMetrics: EngagementMetrics = Field(default_factory=EngagementMetrics)
    isActive: bool = True
    callbackSent: bool = False
    agentNotes: str = ""
    
    def get_scammer_message_count(self) -> int:
        """Count scammer messages"""
        return len([m for m in self.messages if m.sender == "scammer"])
    
    def get_agent_message_count(self) -> int:
        """Count agent messages"""
        return len([m for m in self.messages if m.sender == "agent"])


class GUVICallbackPayload(BaseModel):
    """
    MANDATORY GUVI Callback Payload
    
    POST https://hackathon.guvi.in/api/updateHoneyPotFinalResult
    
    {
      "sessionId": "<sessionId>",
      "scamDetected": true,
      "totalMessagesExchanged": <int>,
      "extractedIntelligence": {...},
      "agentNotes": "<summary of scam tactics>"
    }
    """
    sessionId: str
    scamDetected: bool
    totalMessagesExchanged: int
    extractedIntelligence: ExtractedIntelligence
    agentNotes: str
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "sessionId": "sess_abc123",
                "scamDetected": True,
                "totalMessagesExchanged": 8,
                "extractedIntelligence": {
                    "bankAccounts": [],
                    "upiIds": ["fraudster@paytm"],
                    "phishingLinks": ["http://fake-verify.com"],
                    "phoneNumbers": ["+919876543210"],
                    "suspiciousKeywords": ["urgent", "verify now", "account blocked"]
                },
                "agentNotes": "Scammer claimed account would be blocked and requested UPI transfer. Used urgency tactics and provided fake verification link."
            }
        }
    }


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    timestamp: str
