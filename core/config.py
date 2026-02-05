"""
GUVI Agentic Scam HoneyPot - Configuration
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List, Optional


class Settings(BaseSettings):
    """Application settings for GUVI Hackathon"""
    
    # App
    APP_NAME: str = "GUVI Agentic Scam HoneyPot"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False, env="DEBUG")
    
    # API Server
    API_HOST: str = Field(default="0.0.0.0", env="API_HOST")
    API_PORT: int = Field(default=8000, env="API_PORT")
    
    # Authentication - CRITICAL for GUVI
    API_KEY: str = Field(default="guvi-hackathon-secret-key", env="API_KEY")
    
    # GUVI Callback Endpoint - MANDATORY
    GUVI_CALLBACK_URL: str = Field(
        default="https://hackathon.guvi.in/api/updateHoneyPotFinalResult",
        env="GUVI_CALLBACK_URL"
    )
    
    # Scam Detection
    SCAM_DETECTION_THRESHOLD: float = Field(default=0.6, env="SCAM_DETECTION_THRESHOLD")
    
    # Agent Settings
    MAX_CONVERSATION_TURNS: int = Field(default=15, env="MAX_CONVERSATION_TURNS")
    MIN_TURNS_BEFORE_CALLBACK: int = 3  # Minimum turns before sending callback
    
    # Database
    DATABASE_URL: str = Field(default="sqlite:///./guvi_honeypot.db", env="DATABASE_URL")
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings
settings = Settings()


# Scam Detection Patterns
SCAM_PATTERNS = {
    "urgency": [
        r"blocked\s*(today|now|immediately)",
        r"will\s*be\s*blocked",
        r"urgent",
        r"immediately",
        r"right\s*now",
        r"hurry",
        r"expires?\s*(today|soon)",
        r"last\s*chance",
        r"final\s*notice",
        r"account\s*suspended",
        r"verify\s*(now|immediately)",
    ],
    "bank_fraud": [
        r"\b(sbi|hdfc|icici|axis|pnb|bob|union\s*bank)\b",
        r"bank\s*account",
        r"debit\s*card",
        r"credit\s*card",
        r"kyc\s*(update|verification)",
        r"account\s*verification",
        r"transaction\s*failed",
        r"suspicious\s*activity",
    ],
    "upi_fraud": [
        r"\bupi\b",
        r"\b(paytm|phonepe|gpay|google\s*pay|bhim)\b",
        r"qr\s*code",
        r"scan\s*qr",
        r"collect\s*request",
        r"request\s*money",
        r"send\s*money\s*to",
        r"transfer\s*to",
        r"@(?:paytm|phonepe|ybl|oksbi|okhdfcbank|okicici|okaxis)",
    ],
    "phishing": [
        r"click\s*(here|link)",
        r"tap\s*here",
        r"http[s]?://[^\s]+(?:verify|secure|login|update|kyc)",
        r"bit\.ly|tinyurl|t\.co|short\.link",
        r"verify\s*(?:account|identity|details)",
        r"update\s*(?:kyc|details|information)",
        r"login\s*to",
        r"enter\s*(?:otp|pin|password)",
    ],
    "fake_offers": [
        r"won\s*(?:rs\.?|₹)?\s*[\d,]+",
        r"congratulations!*\s*you\s*(?:have\s*)?won",
        r"lucky\s*(?:draw|winner|prize)",
        r"lottery",
        r"cash\s*(?:prize|back|reward)",
        r"\b(?:rs\.?|₹)\s*[\d,]+\s*(?:lakhs?|crores?|000)",
        r"gift\s*(?:waiting|pending|ready)",
        r"claim\s*(?:your|now)",
    ],
    "otp_pin_harvesting": [
        r"\botp\b",
        r"\bpin\b",
        r"one[-\s]?time[-\s]?password",
        r"verification\s*code",
        r"security\s*code",
        r"share\s*(?:your|the)\s*(?:otp|pin|code)",
        r"send\s*(?:me|us)\s*(?:otp|pin|code)",
        r"provide\s*(?:otp|pin|code)",
        r"enter\s*(?:otp|pin|code)",
        r"\b\d{4,6}\b",  # 4-6 digit codes
    ],
    "suspicious_keywords": [
        r"processing\s*fee",
        r"advance\s*payment",
        r"gst\s*(?:charges|fee)",
        r"tax\s*payment",
        r"refund\s*(?:pending|processing)",
        r"insurance\s*claim",
        r"package\s*delivery",
        r"courier",
        r"custom\s*duty",
    ]
}


# Extraction Patterns
EXTRACTION_PATTERNS = {
    "bank_account": {
        "regex": [
            r"\b\d{9,18}\b",
            r"(?:account|a/c)\s*(?:number|no)?[:\s]+(\d+)",
            r"(?:account|a/c)[:\s]+(\d{9,18})",
        ],
        "validate": lambda x: 9 <= len(''.join(c for c in x if c.isdigit())) <= 18
    },
    "ifsc_code": {
        "regex": [
            r"\b[A-Z]{4}0[A-Z0-9]{6}\b",
            r"ifsc[:\s]+([A-Z]{4}0[A-Z0-9]{6})",
        ],
        "validate": lambda x: len(x) == 11 and x[4] == '0'
    },
    "upi_id": {
        "regex": [
            r"\b[\w.-]+@(?:paytm|phonepe|ybl|oksbi|okhdfcbank|okicici|okaxis|ibl|axl)\b",
            r"\b[\w.-]+@[\w]+\b",
            r"upi\s*(?:id)?[:\s]+([\w.-]+@[\w]+)",
        ],
        "validate": lambda x: '@' in x and len(x.split('@')[0]) >= 3
    },
    "phone_number": {
        "regex": [
            r"\+91[-\s]?\d{10}",
            r"\b\d{10}\b",
            r"(?:mobile|phone|contact|call)[:\s]+(\+?\d[\d\s-]{8,})",
        ],
        "validate": lambda x: len(''.join(c for c in x if c.isdigit())) >= 10
    },
    "phishing_link": {
        "regex": [
            r"https?://[^\s<>\"{}|\\^`[\]]+",
            r"www\.[^\s<>\"{}|\\^`[\]]+",
        ],
        "validate": lambda x: '.' in x and len(x) > 10
    },
}


# Agent Personas
PERSONAS = {
    "confused": {
        "name": "Ramesh",
        "style": "slightly confused, elderly, cooperative",
        "responses": [
            "Wait... I'm a bit confused. Could you explain that again?",
            "Sorry, I'm not very good with technology. What did you say?",
            "My eyes aren't what they used to be. Can you repeat that slowly?",
            "I'm worried about making a mistake. Can you guide me step by step?",
            "Let me write this down... could you say that again?",
            "I didn't understand. Can you explain in simple words?",
            "Is this safe? I've heard about scams...",
            "My son usually helps me with these things. Let me try to understand.",
            "I'm getting a bit worried. Is everything okay?",
            "Please be patient with me, I'm trying my best.",
        ]
    },
    "cooperative": {
        "name": "Priya",
        "style": "cooperative but cautious, asks questions",
        "responses": [
            "Okay, I want to help. What do I need to do?",
            "I can do that. Just to confirm - what was the ID again?",
            "I want to make sure I do this right. Can you repeat?",
            "Alright, I'm following. What's the next step?",
            "I understand. But why do you need this information?",
            "I'll help, but I want to be careful. Is this legitimate?",
            "Let me check... okay, I'm ready. What next?",
            "I want to do this correctly. Can you confirm the details?",
        ]
    },
    "skeptical": {
        "name": "Vikram",
        "style": "slightly suspicious, asks for proof",
        "responses": [
            "How do I know this is real? I've been scammed before.",
            "Can you prove you're from the bank?",
            "This seems suspicious. Why do you need this?",
            "I need to verify this. Can you give me a reference number?",
            "I'm not comfortable sharing this. Can I call the bank directly?",
            "Something doesn't feel right. Can you explain more?",
            "Let me think about this. Why is this urgent?",
        ]
    },
    "curious": {
        "name": "Ananya",
        "style": "curious, asks many questions",
        "responses": [
            "Interesting... tell me more about this.",
            "Why would my account be blocked? I didn't do anything wrong.",
            "How does this work exactly?",
            "What happens if I don't do this?",
            "Can you explain why this is necessary?",
            "I have so many questions. Is this normal?",
            "Wait, let me understand this properly first.",
        ]
    }
}


# Extraction Questions by Type
EXTRACTION_QUESTIONS = {
    "upi_id": [
        "What's the UPI ID I should send to? I want to make sure I get it right.",
        "Can you confirm the UPI ID? I don't want to send to the wrong person.",
        "Sorry, I got disconnected. What was the UPI ID again?",
        "Let me write this down. What's the exact UPI ID?",
    ],
    "bank_account": [
        "Which account should I transfer to? Can you give me the details?",
        "I can do a bank transfer. What are the account details?",
        "My bank needs the account number and IFSC. Can you provide those?",
        "I prefer bank transfer. What's the account information?",
    ],
    "phone_number": [
        "Can I call you to confirm? What's your number?",
        "My phone is having issues. Can you give me your number again?",
        "I'd like to save your number. What is it?",
    ],
    "phishing_link": [
        "The link isn't working. Can you send it again?",
        "I'm having trouble opening the link. Could you resend?",
        "My browser says the link is broken. Can you check and resend?",
    ],
}
