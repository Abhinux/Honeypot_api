"""
GUVI Agentic Scam HoneyPot - Intelligence Extraction Engine
Extracts actionable intelligence from scammer messages
"""

import re
from typing import List, Set
from urllib.parse import urlparse

from core.models import Message, ExtractedIntelligence
from core.config import EXTRACTION_PATTERNS, SCAM_PATTERNS


class IntelligenceExtractor:
    """
    Extracts bank accounts, UPI IDs, phishing links, phone numbers, etc.
    """
    
    # Known legitimate domains to filter
    LEGITIMATE_DOMAINS = {
        "google.com", "gmail.com", "yahoo.com", "hotmail.com",
        "facebook.com", "instagram.com", "twitter.com", "x.com",
        "youtube.com", "linkedin.com",
        "amazon.in", "amazon.com", "flipkart.com",
        "paytm.com", "phonepe.com", "google.com/pay",
        "sbi.co.in", "onlinesbi.sbi", "hdfcbank.com", "icicibank.com",
        "axisbank.com", "pnbindia.in", "bankofbaroda.in",
        "rbi.org.in", "npci.org.in",
        "whatsapp.com", "telegram.org",
    }
    
    # Suspicious TLDs
    SUSPICIOUS_TLDS = {".tk", ".ml", ".ga", ".cf", ".top", ".xyz", ".club", ".online", ".site"}
    
    def __init__(self):
        self.compiled_patterns = self._compile_patterns()
        self.scam_keywords = self._load_scam_keywords()
    
    def _compile_patterns(self) -> dict:
        """Compile extraction patterns"""
        compiled = {}
        for data_type, config in EXTRACTION_PATTERNS.items():
            compiled[data_type] = [re.compile(p, re.IGNORECASE) for p in config["regex"]]
        return compiled
    
    def _load_scam_keywords(self) -> List[str]:
        """Load suspicious keywords from patterns"""
        keywords = []
        for category, patterns in SCAM_PATTERNS.items():
            for pattern in patterns[:3]:  # Take first 3 from each category
                # Extract keyword from pattern
                keyword = pattern.replace(r"\b", "").replace(r"\s*", " ").replace("?", "").replace("*", "")
                if len(keyword) > 3:
                    keywords.append(keyword)
        return keywords
    
    def extract(self, messages: List[Message]) -> ExtractedIntelligence:
        """
        Extract all intelligence from messages
        
        Returns:
            ExtractedIntelligence with all extracted data
        """
        # Combine all scammer messages
        scammer_text = " ".join([m.text for m in messages if m.sender == "scammer"])
        
        intelligence = ExtractedIntelligence()
        
        # Extract each type
        intelligence.bankAccounts = self._extract_bank_accounts(scammer_text)
        intelligence.ifscCodes = self._extract_ifsc_codes(scammer_text)
        intelligence.upiIds = self._extract_upi_ids(scammer_text)
        intelligence.phishingLinks = self._extract_phishing_links(scammer_text)
        intelligence.phoneNumbers = self._extract_phone_numbers(scammer_text)
        intelligence.suspiciousKeywords = self._extract_suspicious_keywords(scammer_text)
        
        return intelligence
    
    def _extract_bank_accounts(self, text: str) -> List[str]:
        """Extract bank account numbers"""
        accounts = []
        patterns = self.compiled_patterns.get("bank_account", [])
        
        for pattern in patterns:
            for match in pattern.finditer(text):
                account = match.group(1) if match.groups() else match.group(0)
                account = ''.join(c for c in account if c.isdigit())
                
                # Validate
                if EXTRACTION_PATTERNS["bank_account"]["validate"](account):
                    if account not in accounts:
                        accounts.append(account)
        
        return accounts[:5]  # Limit to 5
    
    def _extract_ifsc_codes(self, text: str) -> List[str]:
        """Extract IFSC codes"""
        codes = []
        patterns = self.compiled_patterns.get("ifsc_code", [])
        
        for pattern in patterns:
            for match in pattern.finditer(text):
                code = match.group(1) if match.groups() else match.group(0)
                code = code.upper().strip()
                
                if EXTRACTION_PATTERNS["ifsc_code"]["validate"](code):
                    if code not in codes:
                        codes.append(code)
        
        return codes[:5]
    
    def _extract_upi_ids(self, text: str) -> List[str]:
        """Extract UPI IDs"""
        upis = []
        patterns = self.compiled_patterns.get("upi_id", [])
        
        for pattern in patterns:
            for match in pattern.finditer(text):
                upi = match.group(1) if match.groups() else match.group(0)
                upi = upi.lower().strip()
                
                # Filter out common false positives
                if '@' in upi and not upi.endswith(('@gmail.com', '@yahoo.com', '@hotmail.com')):
                    if EXTRACTION_PATTERNS["upi_id"]["validate"](upi):
                        if upi not in upis:
                            upis.append(upi)
        
        return upis[:5]
    
    def _extract_phishing_links(self, text: str) -> List[str]:
        """Extract and filter phishing links"""
        links = []
        patterns = self.compiled_patterns.get("phishing_link", [])
        
        for pattern in patterns:
            for match in pattern.finditer(text):
                url = match.group(0).strip()
                
                # Skip if not valid URL
                if not url.startswith(("http://", "https://", "www.")):
                    continue
                
                # Check if suspicious
                if self._is_suspicious_url(url):
                    if url not in links:
                        links.append(url)
        
        return links[:10]
    
    def _is_suspicious_url(self, url: str) -> bool:
        """Check if URL is potentially suspicious"""
        try:
            # Parse URL
            if url.startswith("www."):
                url = "http://" + url
            
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Remove www prefix for comparison
            if domain.startswith("www."):
                domain = domain[4:]
            
            # Check against legitimate domains
            for legit in self.LEGITIMATE_DOMAINS:
                if domain == legit or domain.endswith("." + legit):
                    return False
            
            # Check for suspicious TLDs
            if any(domain.endswith(tld) for tld in self.SUSPICIOUS_TLDS):
                return True
            
            # Check for typosquatting (e.g., paytm-secure.com)
            for legit in self.LEGITIMATE_DOMAINS:
                legit_name = legit.split('.')[0]
                if legit_name in domain and domain != legit:
                    return True
            
            # Check for suspicious keywords in URL
            suspicious_keywords = ['verify', 'secure', 'login', 'update', 'kyc', 'confirm', 'validate']
            if any(kw in domain for kw in suspicious_keywords):
                return True
            
            # Shortened URLs are suspicious
            if any(short in domain for short in ['bit.ly', 'tinyurl', 't.co', 'short.link', 'goo.gl']):
                return True
            
            return True  # Unknown URLs are suspicious by default
            
        except Exception:
            return True  # If parsing fails, consider suspicious
    
    def _extract_phone_numbers(self, text: str) -> List[str]:
        """Extract phone numbers"""
        numbers = []
        patterns = self.compiled_patterns.get("phone_number", [])
        
        for pattern in patterns:
            for match in pattern.finditer(text):
                number = match.group(1) if match.groups() else match.group(0)
                
                # Normalize
                digits = ''.join(c for c in number if c.isdigit())
                
                if len(digits) == 10:
                    normalized = f"+91{digits}"
                elif len(digits) == 12 and digits.startswith("91"):
                    normalized = f"+{digits}"
                elif len(digits) > 10:
                    normalized = f"+{digits}"
                else:
                    continue
                
                if normalized not in numbers:
                    numbers.append(normalized)
        
        return numbers[:5]
    
    def _extract_suspicious_keywords(self, text: str) -> List[str]:
        """Extract suspicious keywords found in text"""
        text_lower = text.lower()
        found = []
        
        for keyword in self.scam_keywords:
            if keyword.lower() in text_lower:
                found.append(keyword)
        
        # Also check for specific urgent phrases
        urgent_phrases = [
            "account blocked", "verify now", "urgent", "immediately",
            "hurry up", "last chance", "expires today", "final notice",
            "suspended", "limited time", "act now"
        ]
        
        for phrase in urgent_phrases:
            if phrase in text_lower and phrase not in found:
                found.append(phrase)
        
        return list(set(found))[:15]  # Limit and deduplicate
    
    def extract_from_text(self, text: str) -> ExtractedIntelligence:
        """Extract from single text (convenience method)"""
        message = Message(sender="scammer", text=text)
        return self.extract([message])


# Singleton instance
extractor = IntelligenceExtractor()


def extract_intelligence(messages: List[Message]) -> ExtractedIntelligence:
    """Convenience function"""
    return extractor.extract(messages)
