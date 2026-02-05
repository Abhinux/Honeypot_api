"""
GUVI Agentic Scam HoneyPot - Scam Detection Module
Detects scam intent with confidence scoring
"""

import re
from typing import List, Tuple, Set
from collections import Counter

from core.models import ScamDetectionResult, ScamType, Message
from core.config import SCAM_PATTERNS, settings


class ScamDetector:
    """
    Scam detection engine using pattern matching and heuristics
    """
    
    def __init__(self):
        self.compiled_patterns = self._compile_patterns()
    
    def _compile_patterns(self) -> dict:
        """Compile regex patterns for faster matching"""
        compiled = {}
        for category, patterns in SCAM_PATTERNS.items():
            compiled[category] = [re.compile(p, re.IGNORECASE) for p in patterns]
        return compiled
    
    def detect(self, messages: List[Message]) -> ScamDetectionResult:
        """
        Analyze messages for scam indicators
        
        Returns:
            ScamDetectionResult with scamDetected, confidenceScore, scamType
        """
        # Combine all messages into one text for analysis
        all_text = " ".join([m.text for m in messages]).lower()
        
        # Find all matching indicators
        indicators_found = []
        category_matches = {}
        
        for category, patterns in self.compiled_patterns.items():
            matches = []
            for pattern in patterns:
                if pattern.search(all_text):
                    matches.append(pattern.pattern)
            
            if matches:
                category_matches[category] = matches
                indicators_found.extend(matches[:2])  # Limit indicators per category
        
        # If no indicators found, return negative
        if not category_matches:
            return ScamDetectionResult(
                scamDetected=False,
                confidenceScore=0.1,
                scamType=ScamType.UNKNOWN,
                indicators=[],
                reasoning="No scam indicators detected"
            )
        
        # Calculate confidence score
        confidence = self._calculate_confidence(category_matches, all_text)
        
        # Determine scam type
        scam_type = self._determine_scam_type(category_matches)
        
        # Generate reasoning
        reasoning = self._generate_reasoning(category_matches, scam_type)
        
        # Determine if scam detected based on threshold
        scam_detected = confidence >= settings.SCAM_DETECTION_THRESHOLD
        
        return ScamDetectionResult(
            scamDetected=scam_detected,
            confidenceScore=round(confidence, 2),
            scamType=scam_type,
            indicators=list(set(indicators_found))[:10],
            reasoning=reasoning
        )
    
    def _calculate_confidence(self, category_matches: dict, text: str) -> float:
        """
        Calculate confidence score based on:
        - Number of categories matched
        - Number of patterns matched per category
        - Critical indicators present
        """
        base_score = 0.0
        
        # Score based on number of categories
        num_categories = len(category_matches)
        base_score += min(num_categories * 0.15, 0.45)
        
        # Bonus for multiple patterns in same category
        for category, matches in category_matches.items():
            if len(matches) >= 2:
                base_score += 0.1
            if len(matches) >= 3:
                base_score += 0.1
        
        # Critical indicators boost confidence significantly
        critical_categories = ["urgency", "otp_pin_harvesting", "phishing"]
        for crit in critical_categories:
            if crit in category_matches:
                base_score += 0.15
        
        # UPI fraud is very common
        if "upi_fraud" in category_matches:
            base_score += 0.1
        
        # Bank fraud indicators
        if "bank_fraud" in category_matches:
            base_score += 0.1
        
        # Check for combination of urgency + financial
        if "urgency" in category_matches and \
           ("bank_fraud" in category_matches or "upi_fraud" in category_matches):
            base_score += 0.15
        
        # Cap at 0.99
        return min(base_score, 0.99)
    
    def _determine_scam_type(self, category_matches: dict) -> ScamType:
        """Determine the primary scam type from matched categories"""
        
        # Priority order for scam types
        priority = [
            ("upi_fraud", ScamType.UPI_FRAUD),
            ("bank_fraud", ScamType.BANK_FRAUD),
            ("phishing", ScamType.PHISHING),
            ("fake_offers", ScamType.FAKE_OFFER),
            ("otp_pin_harvesting", ScamType.OTP_HARVESTING),
        ]
        
        for category, scam_type in priority:
            if category in category_matches:
                return scam_type
        
        # If only urgency or suspicious keywords, might be phishing
        if "urgency" in category_matches or "suspicious_keywords" in category_matches:
            return ScamType.PHISHING
        
        return ScamType.UNKNOWN
    
    def _generate_reasoning(self, category_matches: dict, scam_type: ScamType) -> str:
        """Generate internal reasoning for detection"""
        parts = []
        
        if "urgency" in category_matches:
            parts.append("Creates false urgency")
        
        if "bank_fraud" in category_matches:
            parts.append("Impersonates bank")
        
        if "upi_fraud" in category_matches:
            parts.append("Requests UPI transfer")
        
        if "phishing" in category_matches:
            parts.append("Contains suspicious links")
        
        if "fake_offers" in category_matches:
            parts.append("Promises fake rewards")
        
        if "otp_pin_harvesting" in category_matches:
            parts.append("Requests sensitive codes")
        
        if "suspicious_keywords" in category_matches:
            parts.append("Uses suspicious terminology")
        
        return f"Detected {scam_type.value}: " + "; ".join(parts) if parts else "Low confidence detection"
    
    def quick_check(self, text: str) -> Tuple[bool, float]:
        """Quick check for single message - returns (is_suspicious, confidence)"""
        message = Message(sender="scammer", text=text)
        result = self.detect([message])
        return result.scamDetected, result.confidenceScore


# Singleton instance
detector = ScamDetector()


def detect_scam(messages: List[Message]) -> ScamDetectionResult:
    """Convenience function for scam detection"""
    return detector.detect(messages)
