from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import asyncio
import aiohttp
import json
from datetime import datetime, timedelta
import logging

app = FastAPI(title="Incident Response Chatbot", version="1.0.0")

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

class ChatResponse(BaseModel):
    response: str
    data: Optional[Dict[str, Any]] = None
    suggestions: Optional[List[str]] = None

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

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(message: ChatMessage):
    query = message.message.lower()
    
    try:
        if "what changed" in query or "recent changes" in query:
            hours = 2
            if "hour" in query:
                # Extract hours if specified
                import re
                hour_match = re.search(r'(\d+)\s*hours?', query)
                if hour_match:
                    hours = int(hour_match.group(1))
            
            data = await analyzer.query_recent_changes(hours)
            correlation_analysis = analyzer.analyze_correlation(data)
            
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
                "Show me error details for affected services",
                "Check dependency health",
                "Analyze error patterns",
                "Show deployment rollback options"
            ]
            
            return ChatResponse(
                response=response,
                data=data,
                suggestions=suggestions
            )
        
        elif "error" in query and ("detail" in query or "pattern" in query):
            data = await analyzer.query_recent_changes(2)
            
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
                "What changed recently?",
                "Check service dependencies",
                "Show related alerts"
            ]
            
            return ChatResponse(
                response=response,
                data=data,
                suggestions=suggestions
            )
        
        else:
            # Default help response
            response = """## 🤖 Incident Response Assistant

I can help you investigate incidents by analyzing your monitoring data. Try asking:

- **"What changed in the last 2 hours?"** - Shows recent deployments, alerts, and anomalies
- **"Show me error details"** - Analyzes error patterns and frequency  
- **"What changed since 15:30?"** - Time-specific change analysis
- **"Check service dependencies"** - Shows service health relationships

I monitor your Grafana, Prometheus, Elasticsearch, and Nagios systems to correlate changes with issues."""
            
            suggestions = [
                "What changed in the last 2 hours?",
                "Show me error details",
                "Check active alerts",
                "Analyze recent deployments"
            ]
            
            return ChatResponse(
                response=response,
                suggestions=suggestions
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