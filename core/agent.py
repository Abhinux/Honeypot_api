"""
GUVI Agentic Scam HoneyPot - Autonomous Agent
Engages scammers naturally with believable persona
"""

import random
from typing import List, Optional
from datetime import datetime

from core.models import Message, ExtractedIntelligence, ScamType
from core.config import PERSONAS, EXTRACTION_QUESTIONS, settings


class ConversationMemory:
    """Memory for agent to track conversation context"""
    
    def __init__(self):
        self.scammer_claims: List[str] = []
        self.extracted_so_far: dict = {
            "upi": False,
            "bank": False,
            "phone": False,
            "link": False,
        }
        self.extraction_attempts: dict = {
            "upi": 0,
            "bank": 0,
            "phone": 0,
            "link": 0,
        }
        self.last_topics: List[str] = []
    
    def record_extraction_attempt(self, data_type: str):
        """Record extraction attempt"""
        if data_type in self.extraction_attempts:
            self.extraction_attempts[data_type] += 1
    
    def mark_extracted(self, data_type: str):
        """Mark data type as extracted"""
        if data_type in self.extracted_so_far:
            self.extracted_so_far[data_type] = True
    
    def add_topic(self, topic: str):
        """Add topic to recent topics"""
        self.last_topics.append(topic)
        if len(self.last_topics) > 5:
            self.last_topics = self.last_topics[-5:]
    
    def get_repeated_topics(self) -> List[str]:
        """Get topics that have been mentioned multiple times"""
        from collections import Counter
        counts = Counter(self.last_topics)
        return [t for t, c in counts.items() if c > 1]


class AutonomousAgent:
    """
    Autonomous agent that engages scammers naturally
    """
    
    def __init__(self, session_id: str, scam_type: ScamType):
        self.session_id = session_id
        self.scam_type = scam_type
        self.persona = self._select_persona()
        self.memory = ConversationMemory()
        self.turn_count = 0
        self.start_time = datetime.utcnow()
    
    def _select_persona(self) -> dict:
        """Select appropriate persona based on scam type"""
        # Different personas work better for different scams
        if self.scam_type == ScamType.BANK_FRAUD:
            return PERSONAS["skeptical"]  # Skeptical works well for bank fraud
        elif self.scam_type == ScamType.UPI_FRAUD:
            return PERSONAS["confused"]  # Confused works well for UPI
        elif self.scam_type == ScamType.FAKE_OFFER:
            return PERSONAS["curious"]  # Curious for fake offers
        else:
            # Random for other types
            return random.choice(list(PERSONAS.values()))
    
    def generate_response(self, 
                         messages: List[Message],
                         extracted: ExtractedIntelligence) -> str:
        """
        Generate human-like response to engage scammer
        
        Strategy:
        1. Analyze what scammer is asking for
        2. Determine what intelligence we still need
        3. Generate appropriate response
        """
        self.turn_count += 1
        
        # Get last scammer message
        last_scammer_msg = None
        for m in reversed(messages):
            if m.sender == "scammer":
                last_scammer_msg = m.text.lower()
                break
        
        if not last_scammer_msg:
            return self._get_random_response()
        
        # Update memory with what we've extracted
        if extracted.upiIds:
            self.memory.mark_extracted("upi")
        if extracted.bankAccounts:
            self.memory.mark_extracted("bank")
        if extracted.phoneNumbers:
            self.memory.mark_extracted("phone")
        if extracted.phishingLinks:
            self.memory.mark_extracted("link")
        
        # Determine strategy
        strategy = self._determine_strategy(last_scammer_msg, extracted)
        
        # Generate response based on strategy
        if strategy == "extract_upi" and not self.memory.extracted_so_far["upi"]:
            response = self._generate_extraction_question("upi_id")
            self.memory.record_extraction_attempt("upi")
        
        elif strategy == "extract_bank" and not self.memory.extracted_so_far["bank"]:
            response = self._generate_extraction_question("bank_account")
            self.memory.record_extraction_attempt("bank")
        
        elif strategy == "extract_phone" and not self.memory.extracted_so_far["phone"]:
            response = self._generate_extraction_question("phone_number")
            self.memory.record_extraction_attempt("phone")
        
        elif strategy == "extract_link" and not self.memory.extracted_so_far["link"]:
            response = self._generate_extraction_question("phishing_link")
            self.memory.record_extraction_attempt("link")
        
        elif strategy == "express_confusion":
            response = self._generate_confusion_response(last_scammer_msg)
        
        elif strategy == "ask_clarification":
            response = self._generate_clarification_question(last_scammer_msg)
        
        elif strategy == "show_cooperation":
            response = self._generate_cooperative_response()
        
        elif strategy == "express_concern":
            response = self._generate_concern_response()
        
        else:
            response = self._get_random_response()
        
        return response
    
    def _determine_strategy(self, scammer_msg: str, extracted: ExtractedIntelligence) -> str:
        """Determine best response strategy"""
        
        # Check what scammer is asking for
        msg_lower = scammer_msg.lower()
        
        # If scammer mentions UPI, try to extract
        if "upi" in msg_lower or "paytm" in msg_lower or "phonepe" in msg_lower:
            if not extracted.upiIds and self.memory.extraction_attempts["upi"] < 2:
                return "extract_upi"
        
        # If scammer mentions bank/account
        if "bank" in msg_lower or "account" in msg_lower or "transfer" in msg_lower:
            if not extracted.bankAccounts and self.memory.extraction_attempts["bank"] < 2:
                return "extract_bank"
        
        # If scammer mentions phone/call
        if "call" in msg_lower or "phone" in msg_lower or "contact" in msg_lower:
            if not extracted.phoneNumbers and self.memory.extraction_attempts["phone"] < 2:
                return "extract_phone"
        
        # If scammer mentions link/click
        if "click" in msg_lower or "link" in msg_lower or "website" in msg_lower:
            if not extracted.phishingLinks and self.memory.extraction_attempts["link"] < 2:
                return "extract_link"
        
        # If scammer is being pushy/urgent
        if any(word in msg_lower for word in ["hurry", "quick", "now", "urgent", "immediately"]):
            return "express_concern"
        
        # If asking for sensitive info
        if any(word in msg_lower for word in ["send", "share", "provide", "give"]):
            return "express_confusion"
        
        # Early turns - ask clarification
        if self.turn_count <= 2:
            return "ask_clarification"
        
        # Default - show cooperation
        return "show_cooperation"
    
    def _generate_extraction_question(self, data_type: str) -> str:
        """Generate question to extract specific data"""
        questions = EXTRACTION_QUESTIONS.get(data_type, ["Can you tell me more?"])
        question = random.choice(questions)
        
        # Add persona flavor
        if self.persona["name"] == "Ramesh":  # Confused elderly
            question += " I want to make sure I do it correctly."
        elif self.persona["name"] == "Priya":  # Cooperative
            question += " I want to help."
        elif self.persona["name"] == "Vikram":  # Skeptical
            question += " I need to verify this first."
        
        return question
    
    def _generate_confusion_response(self, scammer_msg: str) -> str:
        """Generate confusion response"""
        responses = [
            "I'm a bit confused. Could you explain that again more simply?",
            "Sorry, I didn't understand. Can you repeat that?",
            "This is confusing for me. What exactly do you need?",
            "I'm not sure I follow. Can you break it down?",
            "Wait... I'm lost. What are you asking for?",
        ]
        return random.choice(responses)
    
    def _generate_clarification_question(self, scammer_msg: str) -> str:
        """Generate clarification question"""
        responses = [
            "Why do you need this information?",
            "Is this really from my bank?",
            "How do I know this is legitimate?",
            "Can you tell me more about why this is urgent?",
            "What will happen if I don't do this?",
        ]
        return random.choice(responses)
    
    def _generate_cooperative_response(self) -> str:
        """Generate cooperative response"""
        responses = [
            "Okay, I'm listening. What should I do next?",
            "I understand. Please guide me through this.",
            "Alright, I want to do this right. What's the next step?",
            "I'm ready. What do I need to do?",
            "Okay, I'm following along. Please continue.",
        ]
        return random.choice(responses)
    
    def _generate_concern_response(self) -> str:
        """Generate concerned response"""
        responses = [
            "This feels rushed. Can we take this slowly?",
            "I'm getting worried. Is everything okay?",
            "Why is this so urgent? Can you explain?",
            "I need to think about this. Is there a deadline?",
            "I'm concerned. Can I verify this with my bank first?",
        ]
        return random.choice(responses)
    
    def _get_random_response(self) -> str:
        """Get random response from persona"""
        return random.choice(self.persona["responses"])
    
    def should_continue(self) -> bool:
        """Check if agent should continue engagement"""
        if self.turn_count >= settings.MAX_CONVERSATION_TURNS:
            return False
        return True
    
    def get_engagement_duration(self) -> float:
        """Get engagement duration in seconds"""
        return (datetime.utcnow() - self.start_time).total_seconds()
    
    def generate_agent_notes(self, extracted: ExtractedIntelligence) -> str:
        """Generate summary notes about the scam"""
        notes_parts = []
        
        # Scam type
        notes_parts.append(f"Scammer attempted {self.scam_type.value}.")
        
        # Tactics used
        tactics = []
        if "urgent" in str(extracted.suspiciousKeywords).lower() or "immediately" in str(extracted.suspiciousKeywords).lower():
            tactics.append("urgency tactics")
        if extracted.phishingLinks:
            tactics.append("phishing links")
        if extracted.upiIds:
            tactics.append("UPI fraud")
        if extracted.bankAccounts:
            tactics.append("bank account fraud")
        
        if tactics:
            notes_parts.append(f"Used {' and '.join(tactics)}.")
        
        # Intelligence extracted
        intel_summary = extracted.get_summary()
        if intel_summary != "No actionable intelligence":
            notes_parts.append(f"Extracted: {intel_summary}.")
        
        # Engagement
        notes_parts.append(f"Engaged for {self.turn_count} turns.")
        
        return " ".join(notes_parts)


def create_agent(session_id: str, scam_type: ScamType) -> AutonomousAgent:
    """Factory function to create agent"""
    return AutonomousAgent(session_id, scam_type)
