# GUVI Agentic Scam HoneyPot - Project Summary

## 🎯 GUVI Hackathon Submission

**Project Name:** Agentic Scam HoneyPot API: Multi-Turn Scam Engagement & Intelligence Extraction

---

## ✅ Requirements Checklist

### Core Requirements
- [x] Accept incoming scam messages via POST requests
- [x] Support multi-turn conversations with conversationHistory
- [x] Detect scam/fraud intent with confidence scoring
- [x] Activate autonomous AI Agent when scam detected
- [x] Maintain believable human-like persona
- [x] Extract actionable intelligence (UPI, bank accounts, links, phone numbers)
- [x] Return structured JSON response
- [x] **MANDATORY:** Send final results to GUVI callback endpoint

### API Requirements
- [x] `x-api-key` header authentication
- [x] `Content-Type: application/json`
- [x] Reject unauthorized requests
- [x] Input format matches GUVI specification
- [x] Output format: `{"status": "success", "reply": "..."}`

### Scam Detection
- [x] Bank fraud detection
- [x] UPI fraud detection
- [x] Phishing link detection
- [x] Fake offer detection
- [x] OTP/PIN harvesting detection
- [x] Confidence score (0-1)
- [x] Does NOT reveal detection to scammer

### Agent Engagement
- [x] Natural human-like responses
- [x] Curious, concerned, cooperative persona
- [x] Multi-turn conversation support
- [x] No aggressive confrontation
- [x] Strategic intelligence extraction

### Intelligence Extraction
- [x] Bank account numbers
- [x] IFSC codes
- [x] UPI IDs
- [x] Phishing URLs
- [x] Phone numbers
- [x] Suspicious keywords

### Metrics Tracking
- [x] totalMessagesExchanged
- [x] numberOfTurns
- [x] engagementDurationSeconds
- [x] scamDetectionConfidence

### Ethics & Constraints
- [x] No impersonation of real people
- [x] No harassment or threats
- [x] Remains calm and responsible
- [x] Only extracts scam-related intelligence

---

## 📁 Project Structure

```
guvi-scam-honeypot/
│
├── app/
│   └── main.py                 # FastAPI application with all endpoints
│
├── core/
│   ├── config.py               # Settings, patterns, personas
│   ├── models.py               # Pydantic data models (GUVI format)
│   ├── detector.py             # Scam detection engine
│   ├── extractor.py            # Intelligence extraction
│   ├── agent.py                # Autonomous agent
│   ├── database.py             # SQLite session storage
│   └── callback.py             # GUVI callback handler
│
├── requirements.txt            # Python dependencies
├── test_api.py                # API test script
├── Dockerfile                 # Docker container
├── .env.example               # Environment template
├── README.md                  # Full documentation
└── PROJECT_SUMMARY.md         # This file
```

---

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set API key
export API_KEY="guvi-hackathon-secret-key"

# 3. Run server
python -m app.main

# 4. Test
python test_api.py
```

---

## 📡 API Endpoints

### Main Endpoint (Required)

```http
POST /api/scam-detection
x-api-key: your-secret-key
Content-Type: application/json
```

**Request:**
```json
{
  "sessionId": "sess-abc123",
  "message": {
    "sender": "scammer",
    "text": "Your account will be blocked today.",
    "timestamp": 1770005528731
  },
  "conversationHistory": [],
  "metadata": {
    "channel": "SMS",
    "language": "English",
    "locale": "IN"
  }
}
```

**Response:**
```json
{
  "status": "success",
  "reply": "Wait... why would my bank block my account? I didn't do anything wrong."
}
```

### Additional Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /health` | Health check |
| `GET /api/session/{id}` | Get session state |
| `POST /api/force-callback/{id}` | Force send callback |

---

## 🔍 Scam Detection

### Detection Pipeline

1. **Pattern Matching** - 50+ regex patterns across 7 categories
2. **Confidence Calculation** - Based on category matches, critical indicators
3. **Scam Type Classification** - Bank fraud, UPI fraud, phishing, etc.
4. **Threshold Check** - Agent engages if confidence >= 0.6

### Scam Types Detected

| Type | Patterns |
|------|----------|
| `bank_fraud` | SBI, HDFC, ICICI, KYC, account blocked, debit card |
| `upi_fraud` | UPI, Paytm, PhonePe, GPay, QR code, collect request |
| `phishing` | Click here, verify account, suspicious URLs |
| `fake_offer` | Won Rs. X, lottery, lucky draw, prize |
| `otp_harvesting` | Share OTP, PIN, verification code |

---

## 🤖 Autonomous Agent

### Agent Personas

1. **Confused (Ramesh)** - Elderly, not tech-savvy
   - "I'm sorry, I'm not very good with technology..."
   
2. **Cooperative (Priya)** - Helpful but cautious
   - "I want to help. What do I need to do?"
   
3. **Skeptical (Vikram)** - Asks for proof
   - "How do I know this is real?"
   
4. **Curious (Ananya)** - Asks many questions
   - "Why would my account be blocked?"

### Response Strategy

- Analyzes scammer message for extraction opportunities
- Asks strategic questions to get UPI IDs, bank accounts, links
- Varies responses to avoid repetition
- Tracks what has been extracted

---

## 📊 Intelligence Extraction

### Extracted Data

```json
{
  "bankAccounts": ["1234567890"],
  "ifscCodes": ["SBIN0001234"],
  "upiIds": ["fraudster@paytm"],
  "phishingLinks": ["http://fake-verify.com"],
  "phoneNumbers": ["+919876543210"],
  "suspiciousKeywords": ["urgent", "account blocked", "verify now"]
}
```

### Extraction Methods

- **Regex Patterns** - For bank accounts, UPI IDs, phone numbers, URLs
- **Pattern Validation** - IFSC codes, phone number normalization
- **URL Filtering** - Removes legitimate domains, flags suspicious TLDs
- **Keyword Extraction** - Scam-related terminology

---

## 📞 Mandatory GUVI Callback

### When Callback is Sent

Callback is triggered when ALL of the following are true:
1. Scam detected with confidence >= 0.6
2. At least 3 turns completed
3. Actionable intelligence extracted
4. Callback not already sent

### Callback Payload

```http
POST https://hackathon.guvi.in/api/updateHoneyPotFinalResult
Content-Type: application/json
```

```json
{
  "sessionId": "sess-abc123",
  "scamDetected": true,
  "totalMessagesExchanged": 8,
  "extractedIntelligence": {
    "bankAccounts": [],
    "upiIds": ["fraudster@paytm"],
    "phishingLinks": ["http://fake-verify.com"],
    "phoneNumbers": ["+919876543210"],
    "suspiciousKeywords": ["urgent", "account blocked"]
  },
  "agentNotes": "Scammer claimed account would be blocked and requested UPI transfer. Used urgency tactics and provided fake verification link."
}
```

⚠️ **This callback is MANDATORY for evaluation!**

---

## 🐳 Deployment

### Docker

```bash
docker build -t guvi-scam-honeypot .
docker run -p 8000:8000 -e API_KEY=secret guvi-scam-honeypot
```

### Cloud Platforms

**Render:**
1. Push to GitHub
2. Connect to Render
3. Set `API_KEY` environment variable
4. Deploy

**Railway:**
1. Push to GitHub
2. Connect to Railway
3. Set `API_KEY` environment variable
4. Deploy

**Heroku:**
```bash
heroku create your-app-name
heroku config:set API_KEY=your-secret-key
git push heroku main
```

---

## 🧪 Testing

```bash
# Run all tests
python test_api.py

# Manual test
curl -X POST http://localhost:8000/api/scam-detection \
  -H "x-api-key: your-secret-key" \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "test-123",
    "message": {
      "sender": "scammer",
      "text": "You won Rs. 5,00,000! Send to upi:winner@paytm"
    },
    "conversationHistory": []
  }'
```

---

## 📈 Metrics

| Metric | Description |
|--------|-------------|
| `totalMessagesExchanged` | Total messages in conversation |
| `numberOfTurns` | Scammer response count |
| `engagementDurationSeconds` | Time spent engaging |
| `scamDetectionConfidence` | AI confidence (0-1) |

---

## 🔒 Security

- **x-api-key header** required for all endpoints
- Invalid keys rejected with 401
- Input validation with Pydantic
- SQLite database for session storage

---

## 🛣️ Future Enhancements

- [ ] LLM integration (OpenAI/Anthropic) for smarter responses
- [ ] Redis for distributed state management
- [ ] WebSocket support for real-time streaming
- [ ] Admin dashboard for monitoring
- [ ] Multi-language support
- [ ] Voice call integration

---

## 📞 Support

For issues:
1. Check server logs
2. Run `python test_api.py`
3. Check API docs at `/docs`

---

## 📜 License

MIT License

---

<p align="center">
  <b>🛡️ Built for GUVI Hackathon 2024 🛡️</b><br>
  <i>Agentic Scam HoneyPot: Autonomous Scam Engagement & Intelligence Extraction</i>
</p>
