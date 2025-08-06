from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import asyncio
import aiohttp
import json
from datetime import datetime, timedelta
import logging
from llm_service import llm_service, IncidentContext, ConversationMessage, LLMResponse
from conversation_flow import conversation_flow

app = FastAPI(title="Incident Response Chatbot with AI", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatMessage(BaseModel):
    message: str
    timestamp: Optional[datetime] = None
    conversation_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    data: Optional[Dict[str, Any]] = None
    suggestions: Optional[List[str]] = None
    llm_response: Optional[LLMResponse] = None
    analysis_type: str = "standard"

class StreamingChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    provider: Optional[str] = None

# Conversation memory storage (in production, use Redis or database)
conversation_memory: Dict[str, List[ConversationMessage]] = {}

class IncidentAnalyzer:
    def __init__(self):
        self.monitoring_systems = {
            "grafana": {"url": "http://localhost:3000", "token": ""},
            "prometheus": {"url": "http://localhost:9090", "token": ""},
            "elasticsearch": {"url": "http://localhost:9200", "token": ""},
            "nagios": {"url": "http://localhost/nagios", "token": ""}
        }
    
    async def query_recent_changes(self, hours: int = 2) -> Dict[str, Any]:
        """Query all systems for recent changes"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        tasks = [
            self.get_recent_deployments(start_time, end_time),
            self.get_metric_anomalies(start_time, end_time),
            self.get_error_spikes(start_time, end_time),
            self.get_alerts(start_time, end_time)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return {
            "deployments": results[0] if not isinstance(results[0], Exception) else [],
            "anomalies": results[1] if not isinstance(results[1], Exception) else [],
            "errors": results[2] if not isinstance(results[2], Exception) else [],
            "alerts": results[3] if not isinstance(results[3], Exception) else [],
            "time_range": {"start": start_time.isoformat(), "end": end_time.isoformat()}
        }
    
    async def get_recent_deployments(self, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        """Mock deployment data - replace with actual Elasticsearch query"""
        return [
            {
                "service": "api-gateway",
                "version": "v2.1.3",
                "timestamp": "2025-01-08T14:30:00Z",
                "author": "devops-bot",
                "status": "success"
            },
            {
                "service": "user-service",
                "version": "v1.8.1",
                "timestamp": "2025-01-08T13:45:00Z",
                "author": "john.doe",
                "status": "success"
            }
        ]
    
    async def get_metric_anomalies(self, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        """Mock Prometheus anomaly detection"""
        return [
            {
                "metric": "response_time_p95",
                "service": "api-gateway",
                "current_value": 1250,
                "baseline": 450,
                "severity": "high",
                "timestamp": "2025-01-08T14:35:00Z"
            },
            {
                "metric": "error_rate",
                "service": "user-service",
                "current_value": 0.05,
                "baseline": 0.001,
                "severity": "medium",
                "timestamp": "2025-01-08T14:32:00Z"
            }
        ]
    
    async def get_error_spikes(self, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        """Mock error log analysis"""
        return [
            {
                "service": "api-gateway",
                "error_type": "TimeoutError",
                "count": 47,
                "first_seen": "2025-01-08T14:31:00Z",
                "sample_message": "Connection timeout to user-service after 30s"
            },
            {
                "service": "user-service",
                "error_type": "DatabaseConnectionError",
                "count": 12,
                "first_seen": "2025-01-08T14:30:00Z",
                "sample_message": "Failed to connect to primary database"
            }
        ]
    
    async def get_alerts(self, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        """Mock alert data from Nagios/Prometheus"""
        return [
            {
                "service": "user-service",
                "alert": "High Error Rate",
                "status": "CRITICAL",
                "timestamp": "2025-01-08T14:32:00Z",
                "duration": "3m"
            },
            {
                "service": "database-primary",
                "alert": "Connection Pool Exhausted",
                "status": "WARNING",
                "timestamp": "2025-01-08T14:29:00Z",
                "duration": "6m"
            }
        ]
    
    def analyze_correlation(self, data: Dict[str, Any]) -> str:
        """Analyze correlations between different data sources"""
        analysis = []
        
        # Check if deployments correlate with issues
        deployments = data.get("deployments", [])
        errors = data.get("errors", [])
        anomalies = data.get("anomalies", [])
        
        for deployment in deployments:
            deploy_time = datetime.fromisoformat(deployment["timestamp"].replace('Z', '+00:00'))
            
            # Check for errors after deployment
            related_errors = [e for e in errors if 
                            e["service"] == deployment["service"] and
                            datetime.fromisoformat(e["first_seen"].replace('Z', '+00:00')) > deploy_time]
            
            if related_errors:
                analysis.append(f"🚨 **Deployment Correlation**: {deployment['service']} v{deployment['version']} deployed at {deployment['timestamp']} followed by {len(related_errors)} error types")
        
        # Check for cascading failures
        services_with_issues = set()
        for error in errors:
            services_with_issues.add(error["service"])
        for anomaly in anomalies:
            services_with_issues.add(anomaly["service"])
            
        if len(services_with_issues) > 1:
            analysis.append(f"⚠️ **Multi-Service Impact**: {len(services_with_issues)} services affected: {', '.join(services_with_issues)}")
        
        return "\n".join(analysis) if analysis else "No significant correlations detected."

analyzer = IncidentAnalyzer()

# Power Automate integration is available on PowerAutomate branch

def get_conversation_history(conversation_id: str) -> List[ConversationMessage]:
    """Get conversation history for a session"""
    return conversation_memory.get(conversation_id, [])

def add_to_conversation(conversation_id: str, role: str, content: str, metadata: Dict[str, Any] = None):
    """Add message to conversation history"""
    if conversation_id not in conversation_memory:
        conversation_memory[conversation_id] = []
    
    message = ConversationMessage(
        role=role,
        content=content,
        timestamp=datetime.now(),
        metadata=metadata
    )
    
    conversation_memory[conversation_id].append(message)
    
    # Keep only last 50 messages per conversation
    if len(conversation_memory[conversation_id]) > 50:
        conversation_memory[conversation_id] = conversation_memory[conversation_id][-50:]

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(message: ChatMessage):
    query = message.message.lower()
    conversation_id = message.conversation_id or "default"
    
    try:
        # Add user message to conversation history
        add_to_conversation(conversation_id, "user", message.message)
        
        # Process message through conversation flow first
        flow_result = conversation_flow.process_message(conversation_id, message.message)
        
        # If conversation flow handled the message, use its response
        if not flow_result.get('use_traditional_flow', False):
            # Add assistant response to history
            add_to_conversation(conversation_id, "assistant", flow_result['response'])
            
            return ChatResponse(
                response=flow_result['response'],
                data={},
                suggestions=flow_result.get('suggestions', []),
                analysis_type="conversation_flow"
            )
        
        # If conversation flow says to use traditional flow, continue with normal logic
        # Get monitoring data for context
        data = await analyzer.query_recent_changes(2)
        correlation_analysis = analyzer.analyze_correlation(data)
        
        # Create incident context for LLM
        context = IncidentContext(
            recent_changes=data,
            active_alerts=data.get("alerts", []),
            error_patterns=data.get("errors", []),
            service_health=data.get("anomalies", []),
            correlation_analysis=correlation_analysis
        )
        
        # Get conversation history
        history = get_conversation_history(conversation_id)
        
        # Apply any focus from conversation flow
        focus_context = flow_result.get('focus', '')
        if focus_context:
            # Add focus context to the LLM prompt
            context.correlation_analysis = f"{correlation_analysis}\n\nFOCUS: {focus_context}"
        
        # Check if we should use LLM for this query
        use_llm = any(keyword in query for keyword in [
            "analyze", "explain", "why", "how", "what should", "recommend", 
            "suggest", "help", "understand", "investigate", "troubleshoot"
        ]) or len(query.split()) > 10 or flow_result.get('use_traditional_flow', False)
        
        if use_llm and llm_service.get_available_providers():
            # Generate intelligent response using LLM
            try:
                llm_response = await llm_service.generate_response(
                    message.message, context, history
                )
                
                # Check if LLM response was successful
                if llm_response:
                    # Add assistant response to history
                    add_to_conversation(conversation_id, "assistant", llm_response.content, {
                        "llm_provider": llm_response.provider,
                        "tokens_used": llm_response.tokens_used
                    })
                    
                    # Generate contextual suggestions
                    suggestions = [
                        "Show me specific error details",
                        "What are the next steps to resolve this?",
                        "Check related service dependencies",
                        "Generate incident summary report"
                    ]
                    
                    return ChatResponse(
                        response=llm_response.content,
                        data=data,
                        suggestions=suggestions,
                        llm_response=llm_response,
                        analysis_type="ai_powered"
                    )
                else:
                    # LLM not available, fall back to traditional response
                    logger.info("LLM returned None, falling back to traditional response")
                    use_llm = False
                
            except Exception as llm_error:
                logger.error(f"LLM error: {llm_error}")
                # Fall back to traditional response
                use_llm = False
        
        # Traditional rule-based responses
        if "what changed" in query or "recent changes" in query:
            hours = 2
            if "hour" in query:
                import re
                hour_match = re.search(r'(\d+)\s*hours?', query)
                if hour_match:
                    hours = int(hour_match.group(1))
            
            response = f"## Recent Changes (Last {hours} hours)\n\n"
            response += correlation_analysis + "\n\n"
            
            if data["deployments"]:
                response += "### 🚀 Deployments\n"
                for dep in data["deployments"]:
                    response += f"- **{dep['service']}** v{dep['version']} at {dep['timestamp']}\n"
                response += "\n"
            
            if data["alerts"]:
                response += "### 🚨 Active Alerts\n"
                for alert in data["alerts"]:
                    response += f"- **{alert['service']}**: {alert['alert']} ({alert['status']}) - {alert['duration']}\n"
                response += "\n"
            
            if data["anomalies"]:
                response += "### 📊 Metric Anomalies\n"
                for anomaly in data["anomalies"]:
                    response += f"- **{anomaly['service']}**: {anomaly['metric']} = {anomaly['current_value']} (baseline: {anomaly['baseline']})\n"
            
            suggestions = [
                "Analyze the correlation between deployments and errors",
                "What should I investigate first?",
                "Generate incident summary",
                "Show deployment rollback options"
            ]
            
        elif "error" in query and ("detail" in query or "pattern" in query):
            response = "## Error Analysis\n\n"
            
            if data["errors"]:
                for error in data["errors"]:
                    response += f"### {error['service']} - {error['error_type']}\n"
                    response += f"**Count**: {error['count']} occurrences\n"
                    response += f"**First Seen**: {error['first_seen']}\n"
                    response += f"**Sample**: `{error['sample_message']}`\n\n"
            else:
                response = "No recent errors detected in the monitored services."
            
            suggestions = [
                "What's causing these errors?",
                "How can I fix this issue?",
                "Check service dependencies",
                "Show related alerts"
            ]
            
        else:
            # Enhanced help response
            llm_status = "🤖 **AI-Powered Analysis Available**" if llm_service.get_available_providers() else "📊 **Rule-Based Analysis**"
            
            response = f"""## {llm_status}

I can help you investigate incidents by analyzing your monitoring data and providing intelligent insights:

**Smart Analysis:**
- **"Analyze what changed in the last 2 hours"** - AI-powered correlation analysis
- **"Why are we seeing these errors?"** - Root cause analysis
- **"What should I investigate first?"** - Prioritized action recommendations
- **"Explain this incident impact"** - Business impact assessment

**Quick Data:**
- **"Show me error details"** - Recent error patterns
- **"Check active alerts"** - Current system alerts
- **"Recent deployments"** - Latest changes

I monitor your Grafana, Prometheus, Elasticsearch, and Nagios systems."""
            
            suggestions = [
                "Analyze what changed in the last 2 hours",
                "What should I investigate first?",
                "Show me current system health",
                "Generate incident summary"
            ]
        
        # Add assistant response to history for traditional responses
        add_to_conversation(conversation_id, "assistant", response)
        
        return ChatResponse(
            response=response,
            data=data,
            suggestions=suggestions,
            analysis_type="traditional"
        )
    
    except Exception as e:
        logging.error(f"Error processing chat message: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)