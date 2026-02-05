# 🤖 GUVI Agentic Scam HoneyPot API

## Autonomous Scam Engagement & Intelligence Extraction

[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)

> **An AI-powered deception system that detects scam intent, engages scammers autonomously, and extracts actionable intelligence for cybersecurity defense.**

---

## 🎯 GUVI Hackathon Submission

This project is built strictly according to the GUVI Hackathon problem statement.

### Key Features

✅ **Scam Detection** - Pattern-based detection with confidence scoring  
✅ **Autonomous Agent** - Engages scammers with believable human persona  
✅ **Multi-Turn Support** - Full conversation history handling  
✅ **Intelligence Extraction** - Bank accounts, UPI IDs, phishing links, phone numbers  
✅ **Mandatory Callback** - Sends results to GUVI endpoint  
✅ **x-api-key Auth** - Secure API authentication  

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set API Key

```bash
export API_KEY="your-secret-api-key"
```

### 3. Run Server

```bash
python -m app.main
```

Server starts at `http://localhost:8000`

### 4. Test API

```bash
python test_api.py
```

---

## 📡 API Documentation

### Main Endpoint

```http
POST /api/scam-detection
Content-Type: application/json
x-api-key: your-secret-api-key
```

**Request Format:**
```json
{
  "sessionId": "unique-session-id",
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

**Response Format:**
```json
{
  "status": "success",
  "reply": "Wait... why would my bank block my account? I didn't do anything wrong."
}
```

---

## 🔍 Scam Detection

### Detected Scam Types

| Type | Indicators |
|------|------------|
| `bank_fraud` | SBI, HDFC, ICICI, KYC, account blocked |
| `upi_fraud` | UPI, Paytm, PhonePe, QR code, collect request |
| `phishing` | Click here, suspicious links, verify account |
| `fake_offer` | Won Rs. X, lottery, lucky draw, prize |
| `otp_harvesting` | Share OTP, PIN, verification code |

### Confidence Scoring

- **0.0 - 0.6**: Low confidence (no agent engagement)
- **0.6 - 0.8**: Medium confidence (agent may engage)
- **0.8 - 1.0**: High confidence (agent engages)

---

## 🤖 Autonomous Agent

### Personas

The agent adopts different personas based on scam type:

1. **Confused (Ramesh)** - Elderly, not tech-savvy, asks for repetition
2. **Cooperative (Priya)** - Helpful but cautious, asks questions  
3. **Skeptical (Vikram)** - Suspicious, asks for proof
4. **Curious (Ananya)** - Asks many questions, seeks understanding

### Response Strategy

- Extracts UPI IDs, bank accounts, phone numbers, phishing links
- Asks believable follow-up questions
- Maintains conversation flow without revealing detection
- Tracks extraction attempts to avoid repetition

---

## 📊 Intelligence Extraction

### Extracted Data Types

```json
{
  "bankAccounts": ["1234567890"],
  "ifscCodes": ["SBIN0001234"],
  "upiIds": ["fraudster@paytm"],
  "phishingLinks": ["http://fake-verify.com"],
  "phoneNumbers": ["+919876543210"],
  "suspiciousKeywords": ["urgent", "account blocked"]
}
```

---

## 📞 Mandatory GUVI Callback

Once scam is confirmed and intelligence is extracted, the system automatically sends results to:

```http
POST https://hackathon.guvi.in/api/updateHoneyPotFinalResult
Content-Type: application/json
```

**Payload:**
```json
{
  "sessionId": "session-id",
  "scamDetected": true,
  "totalMessagesExchanged": 8,
  "extractedIntelligence": {...},
  "agentNotes": "Scammer used urgency tactics and requested UPI transfer."
}
```

⚠️ **This callback is MANDATORY for evaluation. Do not skip!**

---

## 🐳 Docker Deployment

```bash
# Build image
docker build -t guvi-scam-honeypot .

# Run container
docker run -p 8000:8000 \
  -e API_KEY="your-secret-key" \
  guvi-scam-honeypot
```

---

## ☁️ Cloud Deployment

### Render/Railway/Heroku

1. Push code to GitHub
2. Connect repository to platform
3. Set environment variable: `API_KEY=your-secret-key`
4. Deploy

### AWS/GCP/Azure

Use the provided Dockerfile for container deployment.

---

## 🧪 Testing

```bash
# Run all tests
python test_api.py

# Test specific scenario
curl -X POST http://localhost:8000/api/scam-detection \
  -H "x-api-key: your-secret-key" \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "test-123",
    "message": {
      "sender": "scammer",
      "text": "You won Rs. 5,00,000! Send money to upi:winner@paytm"
    },
    "conversationHistory": []
  }'
```

---

## 📁 Project Structure

```
guvi-scam-honeypot/
├── app/
│   ├── __init__.py
│   └── main.py              # FastAPI application
├── core/
│   ├── __init__.py
│   ├── config.py            # Settings & patterns
│   ├── models.py            # Pydantic models
│   ├── detector.py          # Scam detection engine
│   ├── extractor.py         # Intelligence extraction
│   ├── agent.py             # Autonomous agent
│   ├── database.py          # Session storage
│   └── callback.py          # GUVI callback
├── requirements.txt         # Dependencies
├── test_api.py             # Test script
├── Dockerfile              # Docker image
└── README.md               # This file
```

---

## ⚙️ Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `API_KEY` | `guvi-hackathon-secret-key` | API authentication key |
| `API_HOST` | `0.0.0.0` | Server host |
| `API_PORT` | `8000` | Server port |
| `GUVI_CALLBACK_URL` | `https://hackathon.guvi.in/api/updateHoneyPotFinalResult` | Callback endpoint |
| `SCAM_DETECTION_THRESHOLD` | `0.6` | Minimum confidence for agent engagement |
| `MAX_CONVERSATION_TURNS` | `15` | Maximum turns per session |

---

## 🔒 Security

- **x-api-key header** required for all endpoints
- Input validation with Pydantic
- No PII stored beyond session duration
- Configurable data retention

---

## 📈 Metrics Tracked

- `totalMessagesExchanged` - Total messages in session
- `numberOfTurns` - Number of scammer responses
- `engagementDurationSeconds` - Time spent engaging
- `scamDetectionConfidence` - AI confidence score

---

## 🛣️ Future Enhancements

- [ ] LLM integration for smarter responses
- [ ] Redis for distributed state
- [ ] WebSocket real-time streaming
- [ ] Admin dashboard
- [ ] Multi-language support

---

## 📞 Support

For issues or questions:
- Check logs in console output
- Review API docs at `/docs`
- Run `python test_api.py` for diagnostics

---

## 📜 License

MIT License

---

<p align="center">
  <b>🛡️ Built for GUVI Hackathon 🛡️</b>
</p>
