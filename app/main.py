"""
GUVI Agentic Scam HoneyPot - FastAPI Application
Main API server with x-api-key authentication
"""

import time
from datetime import datetime
from typing import Optional, Dict
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Header, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from core.config import settings
from core.models import (
    IncomingRequest, AgentResponse, SessionState, Message,
    ScamDetectionResult, EngagementMetrics
)
from core.detector import detect_scam
from core.extractor import extract_intelligence
from core.agent import create_agent, AutonomousAgent
from core.database import save_session, get_session, mark_callback_sent
from core.callback import send_guvi_callback


# In-memory store for active agents
active_agents: Dict[str, AutonomousAgent] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    print(f"🚀 Starting {settings.APP_NAME}")
    print(f"📍 GUVI Callback URL: {settings.GUVI_CALLBACK_URL}")
    yield
    print("👋 Shutting down...")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Agentic Scam HoneyPot API for GUVI Hackathon",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Authentication middleware
async def verify_api_key(x_api_key: Optional[str] = Header(None)) -> str:
    """Verify x-api-key header"""
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing x-api-key header"
        )
    
    if x_api_key != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    return x_api_key


@app.get("/", tags=["Health"])
async def root():
    """Root endpoint"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "operational",
        "docs": "/docs"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/api/scam-detection", response_model=AgentResponse, tags=["Scam Detection"])
async def scam_detection(
    request: IncomingRequest,
    x_api_key: str = Header(..., description="API Key for authentication")
):
    """
    Main GUVI API Endpoint - Process incoming scam messages
    
    - Detects scam intent
    - Activates autonomous agent if scam detected
    - Extracts actionable intelligence
    - Returns human-like response
    - Sends callback to GUVI when complete
    
    **Authentication:** Requires `x-api-key` header
    """
    start_time = time.time()
    
    # Verify API key
    await verify_api_key(x_api_key)
    
    try:
        session_id = request.sessionId
        
        # Get or create session
        session = await get_session(session_id)
        
        if not session:
            # New session
            session = SessionState(
                sessionId=session_id,
                messages=[]
            )
        
        # Add current message to session
        session.messages.append(request.message)
        
        # Add conversation history if provided
        if request.conversationHistory:
            # Only add messages not already in session
            existing = {(m.sender, m.text) for m in session.messages}
            for msg in request.conversationHistory:
                if (msg.sender, msg.text) not in existing:
                    session.messages.append(msg)
        
        # Update metadata
        if request.metadata:
            session.metadata = request.metadata.model_dump()
        
        # ========== STEP 1: SCAM DETECTION ==========
        detection_result = detect_scam(session.messages)
        session.detectionResult = detection_result
        
        print(f"[SESSION {session_id}] Scam detected: {detection_result.scamDetected} (confidence: {detection_result.confidenceScore})")
        
        # ========== STEP 2: INTELLIGENCE EXTRACTION ==========
        extracted_intel = extract_intelligence(session.messages)
        
        # Merge with existing intelligence (avoid duplicates)
        for upi in extracted_intel.upiIds:
            if upi not in session.extractedIntelligence.upiIds:
                session.extractedIntelligence.upiIds.append(upi)
        
        for bank in extracted_intel.bankAccounts:
            if bank not in session.extractedIntelligence.bankAccounts:
                session.extractedIntelligence.bankAccounts.append(bank)
        
        for ifsc in extracted_intel.ifscCodes:
            if ifsc not in session.extractedIntelligence.ifscCodes:
                session.extractedIntelligence.ifscCodes.append(ifsc)
        
        for link in extracted_intel.phishingLinks:
            if link not in session.extractedIntelligence.phishingLinks:
                session.extractedIntelligence.phishingLinks.append(link)
        
        for phone in extracted_intel.phoneNumbers:
            if phone not in session.extractedIntelligence.phoneNumbers:
                session.extractedIntelligence.phoneNumbers.append(phone)
        
        for kw in extracted_intel.suspiciousKeywords:
            if kw not in session.extractedIntelligence.suspiciousKeywords:
                session.extractedIntelligence.suspiciousKeywords.append(kw)
        
        # ========== STEP 3: AGENT HANDOFF & RESPONSE ==========
        agent_response = ""
        
        if detection_result.scamDetected and detection_result.confidenceScore >= settings.SCAM_DETECTION_THRESHOLD:
            # Get or create agent
            if session_id not in active_agents:
                agent = create_agent(session_id, detection_result.scamType)
                active_agents[session_id] = agent
            else:
                agent = active_agents[session_id]
            
            # Generate agent response
            agent_response = agent.generate_response(
                session.messages,
                session.extractedIntelligence
            )
            
            # Add agent response to session
            session.messages.append(Message(sender="agent", text=agent_response))
            
            print(f"[SESSION {session_id}] Agent engaged. Response: {agent_response[:50]}...")
        else:
            # Not a scam or low confidence - generic response
            agent_response = "Thank you for the information. I'll look into this."
        
        # ========== STEP 4: UPDATE METRICS ==========
        scammer_msgs = len([m for m in session.messages if m.sender == "scammer"])
        agent_msgs = len([m for m in session.messages if m.sender == "agent"])
        
        session.engagementMetrics = EngagementMetrics(
            totalMessagesExchanged=len(session.messages),
            numberOfTurns=scammer_msgs,
            engagementDurationSeconds=time.time() - start_time,
            scamDetectionConfidence=detection_result.confidenceScore
        )
        
        # ========== STEP 5: CHECK IF READY FOR CALLBACK ==========
        should_send_callback = (
            detection_result.scamDetected and
            scammer_msgs >= settings.MIN_TURNS_BEFORE_CALLBACK and
            not session.callbackSent and
            session.extractedIntelligence.has_intelligence()
        )
        
        if should_send_callback:
            # Generate agent notes
            agent = active_agents.get(session_id)
            if agent:
                session.agentNotes = agent.generate_agent_notes(session.extractedIntelligence)
            
            # Save session before callback
            await save_session(session)
            
            # Send callback to GUVI (MANDATORY)
            print(f"[SESSION {session_id}] Sending callback to GUVI...")
            callback_success = await send_guvi_callback(session)
            
            if callback_success:
                session.callbackSent = True
                await mark_callback_sent(session_id)
                print(f"[SESSION {session_id}] ✅ Callback sent successfully")
            else:
                print(f"[SESSION {session_id}] ❌ Callback failed - will retry on next message")
        
        # Save session
        session.updatedAt = datetime.utcnow()
        await save_session(session)
        
        # ========== STEP 6: RETURN RESPONSE ==========
        return AgentResponse(
            status="success",
            reply=agent_response
        )
        
    except Exception as e:
        print(f"Error processing request: {e}")
        import traceback
        traceback.print_exc()
        
        # Return error response
        return AgentResponse(
            status="error",
            reply="I'm sorry, I'm having trouble understanding. Could you repeat that?"
        )


@app.get("/api/session/{session_id}", tags=["Monitoring"])
async def get_session_state(
    session_id: str,
    x_api_key: str = Header(...)
):
    """Get session state (for debugging/monitoring)"""
    await verify_api_key(x_api_key)
    
    session = await get_session(session_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    return {
        "sessionId": session.sessionId,
        "createdAt": session.createdAt.isoformat(),
        "updatedAt": session.updatedAt.isoformat(),
        "isActive": session.isActive,
        "callbackSent": session.callbackSent,
        "scamDetected": session.detectionResult.scamDetected if session.detectionResult else False,
        "scamType": session.detectionResult.scamType.value if session.detectionResult else None,
        "confidenceScore": session.detectionResult.confidenceScore if session.detectionResult else 0,
        "totalMessagesExchanged": session.engagementMetrics.totalMessagesExchanged,
        "extractedIntelligence": session.extractedIntelligence.model_dump(),
        "agentNotes": session.agentNotes
    }


@app.post("/api/force-callback/{session_id}", tags=["Admin"])
async def force_callback(
    session_id: str,
    x_api_key: str = Header(...)
):
    """Force send callback for a session (admin only)"""
    await verify_api_key(x_api_key)
    
    session = await get_session(session_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # Generate agent notes if not present
    if not session.agentNotes:
        agent = active_agents.get(session_id)
        if agent:
            session.agentNotes = agent.generate_agent_notes(session.extractedIntelligence)
        else:
            session.agentNotes = f"Scam detected: {session.detectionResult.scamType.value if session.detectionResult else 'unknown'}"
    
    # Send callback
    success = await send_guvi_callback(session)
    
    if success:
        session.callbackSent = True
        await mark_callback_sent(session_id)
        return {"status": "success", "message": "Callback sent successfully"}
    else:
        return {"status": "error", "message": "Callback failed"}


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": "error", "error": exc.detail}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"status": "error", "error": "Internal server error"}
    )


def main():
    """Run the application"""
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )


if __name__ == "__main__":
    main()
