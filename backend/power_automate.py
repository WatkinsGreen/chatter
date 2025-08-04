from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import asyncio
import aiohttp
import json
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/power-automate", tags=["Power Automate"])

class IncidentAlert(BaseModel):
    severity: str
    service: str
    alert_name: str
    timestamp: str
    description: str
    metric_value: Optional[float] = None
    baseline_value: Optional[float] = None
    correlation_data: Optional[Dict[str, Any]] = None

class TeamsNotification(BaseModel):
    webhook_url: str
    title: str
    message: str
    severity: str
    service: str
    actions: Optional[List[Dict[str, str]]] = None

class TicketCreation(BaseModel):
    service_now_url: str
    title: str
    description: str
    severity: str 
    service: str
    assigned_to: Optional[str] = None

class PowerAutomateIntegration:
    def __init__(self):
        self.webhook_urls = {
            "teams_critical": "",  # Configure these in environment
            "teams_warning": "",
            "serviceNow_ticket": "",
            "jira_ticket": "",
            "escalation": ""
        }
    
    async def trigger_teams_notification(self, alert: IncidentAlert) -> bool:
        """Trigger Teams notification via Power Automate webhook"""
        try:
            teams_webhook = self.webhook_urls.get("teams_critical" if alert.severity == "high" else "teams_warning")
            if not teams_webhook:
                logger.warning(f"No Teams webhook configured for severity: {alert.severity}")
                return False
            
            # Create adaptive card payload for Teams
            adaptive_card = {
                "type": "message",
                "attachments": [{
                    "contentType": "application/vnd.microsoft.card.adaptive",
                    "content": {
                        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                        "type": "AdaptiveCard",
                        "version": "1.2",
                        "body": [
                            {
                                "type": "TextBlock",
                                "text": f"🚨 {alert.alert_name}",
                                "weight": "Bolder",
                                "size": "Medium",
                                "color": "Attention" if alert.severity == "high" else "Warning"
                            },
                            {
                                "type": "FactSet",
                                "facts": [
                                    {"title": "Service", "value": alert.service},
                                    {"title": "Severity", "value": alert.severity.upper()},
                                    {"title": "Time", "value": alert.timestamp},
                                    {"title": "Description", "value": alert.description}
                                ]
                            }
                        ],
                        "actions": [
                            {
                                "type": "Action.OpenUrl",
                                "title": "View in Dashboard",
                                "url": f"http://localhost:3000?service={alert.service}"
                            },
                            {
                                "type": "Action.Http",
                                "title": "Acknowledge",
                                "method": "POST",
                                "url": f"http://localhost:8000/power-automate/acknowledge/{alert.service}",
                                "body": json.dumps({"acknowledged_by": "{{user.displayName}}"})
                            }
                        ]
                    }
                }]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(teams_webhook, json=adaptive_card) as response:
                    if response.status == 200:
                        logger.info(f"Teams notification sent for {alert.service}")
                        return True
                    else:
                        logger.error(f"Failed to send Teams notification: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"Error sending Teams notification: {e}")
            return False
    
    async def create_ticket(self, alert: IncidentAlert, ticket_system: str = "servicenow") -> Optional[str]:
        """Create ticket via Power Automate webhook"""
        try:
            webhook_key = f"{ticket_system}_ticket"
            webhook_url = self.webhook_urls.get(webhook_key)
            
            if not webhook_url:
                logger.warning(f"No webhook configured for {ticket_system}")
                return None
            
            ticket_data = {
                "title": f"{alert.alert_name} - {alert.service}",
                "description": f"""
Incident Details:
- Service: {alert.service}
- Severity: {alert.severity}
- Time: {alert.timestamp}
- Description: {alert.description}

Correlation Data:
{json.dumps(alert.correlation_data, indent=2) if alert.correlation_data else 'None'}

Auto-generated by Incident Response Chatbot
                """.strip(),
                "severity": "1" if alert.severity == "high" else "2",
                "service": alert.service,
                "category": "Infrastructure",
                "subcategory": "Monitoring Alert"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=ticket_data) as response:
                    if response.status == 200:
                        result = await response.json()
                        ticket_id = result.get("ticket_id", "Unknown")
                        logger.info(f"Ticket created: {ticket_id}")
                        return ticket_id
                    else:
                        logger.error(f"Failed to create ticket: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error creating ticket: {e}")
            return None
    
    async def trigger_escalation(self, alert: IncidentAlert, escalation_level: int = 1) -> bool:
        """Trigger escalation workflow via Power Automate"""
        try:
            webhook_url = self.webhook_urls.get("escalation")
            if not webhook_url:
                return False
            
            escalation_data = {
                "alert": alert.dict(),
                "escalation_level": escalation_level,
                "timestamp": datetime.now().isoformat(),
                "auto_escalated": True
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=escalation_data) as response:
                    return response.status == 200
                    
        except Exception as e:
            logger.error(f"Error triggering escalation: {e}")
            return False

power_automate = PowerAutomateIntegration()

@router.post("/webhook/incident")
async def webhook_incident(alert: IncidentAlert, background_tasks: BackgroundTasks):
    """Webhook endpoint for Power Automate to send incident alerts"""
    logger.info(f"Received incident alert for {alert.service}: {alert.alert_name}")
    
    # Process alert in background
    background_tasks.add_task(process_incident_alert, alert)
    
    return {
        "status": "received",
        "alert_id": f"{alert.service}_{alert.timestamp}",
        "message": "Alert processing initiated"
    }

async def process_incident_alert(alert: IncidentAlert):
    """Process incident alert and trigger automations"""
    try:
        # 1. Send Teams notification
        teams_sent = await power_automate.trigger_teams_notification(alert)
        
        # 2. Create ticket for high severity alerts
        ticket_id = None
        if alert.severity == "high":
            ticket_id = await power_automate.create_ticket(alert)
        
        # 3. Auto-escalate if critical and no acknowledgment within 5 minutes
        if alert.severity == "high":
            # This would be handled by a separate background job in production
            await asyncio.sleep(300)  # 5 minutes
            # Check if acknowledged, if not, escalate
            
        logger.info(f"Processed alert {alert.service}: Teams={teams_sent}, Ticket={ticket_id}")
        
    except Exception as e:
        logger.error(f"Error processing incident alert: {e}")

@router.post("/acknowledge/{service}")
async def acknowledge_incident(service: str, request: Request):
    """Acknowledge an incident (called from Teams adaptive card)"""
    body = await request.json()
    acknowledged_by = body.get("acknowledged_by", "Unknown")
    
    logger.info(f"Incident acknowledged for {service} by {acknowledged_by}")
    
    # Update internal tracking
    # In production, this would update a database
    
    return {
        "status": "acknowledged",
        "service": service,
        "acknowledged_by": acknowledged_by,
        "timestamp": datetime.now().isoformat()
    }

@router.post("/trigger/teams-notification")
async def trigger_teams_notification(notification: TeamsNotification):
    """Manually trigger Teams notification"""
    alert = IncidentAlert(
        severity=notification.severity,
        service=notification.service,
        alert_name=notification.title,
        timestamp=datetime.now().isoformat(),
        description=notification.message
    )
    
    success = await power_automate.trigger_teams_notification(alert)
    
    if success:
        return {"status": "sent", "message": "Teams notification sent successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to send Teams notification")

@router.post("/trigger/create-ticket")
async def trigger_create_ticket(ticket: TicketCreation):
    """Manually trigger ticket creation"""
    alert = IncidentAlert(
        severity=ticket.severity,
        service=ticket.service,
        alert_name=ticket.title,
        timestamp=datetime.now().isoformat(),
        description=ticket.description
    )
    
    ticket_id = await power_automate.create_ticket(alert)
    
    if ticket_id:
        return {"status": "created", "ticket_id": ticket_id}
    else:
        raise HTTPException(status_code=500, detail="Failed to create ticket")

@router.get("/webhooks/configure")
async def get_webhook_configuration():
    """Get current webhook configuration"""
    return {
        "webhooks": {
            "teams_critical": power_automate.webhook_urls["teams_critical"] or "Not configured",
            "teams_warning": power_automate.webhook_urls["teams_warning"] or "Not configured", 
            "serviceNow_ticket": power_automate.webhook_urls["serviceNow_ticket"] or "Not configured",
            "jira_ticket": power_automate.webhook_urls["jira_ticket"] or "Not configured",
            "escalation": power_automate.webhook_urls["escalation"] or "Not configured"
        },
        "status": "Configuration endpoint active"
    }

@router.post("/webhooks/configure")
async def configure_webhooks(webhooks: Dict[str, str]):
    """Configure Power Automate webhook URLs"""
    for key, url in webhooks.items():
        if key in power_automate.webhook_urls:
            power_automate.webhook_urls[key] = url
    
    return {
        "status": "configured",
        "message": "Webhook URLs updated successfully",
        "configured_webhooks": list(webhooks.keys())
    }

@router.get("/unacknowledged-alerts")
async def get_unacknowledged_alerts():
    """Get unacknowledged alerts for escalation workflow"""
    # Mock data - in production, this would query a database
    alerts = [
        {
            "service": "api-gateway",
            "alert_name": "High Response Time",
            "severity": "high",
            "timestamp": "2025-01-08T14:30:00Z",
            "minutes_since_alert": 8,
            "escalation_level": 0
        },
        {
            "service": "user-service", 
            "alert_name": "Database Connection Error",
            "severity": "high",
            "timestamp": "2025-01-08T14:25:00Z", 
            "minutes_since_alert": 13,
            "escalation_level": 1
        }
    ]
    
    return {"alerts": alerts}

@router.post("/escalation-acknowledge")
async def escalation_acknowledge(request: Request):
    """Handle escalation acknowledgment"""
    body = await request.json()
    service = body.get("service")
    escalation_level = body.get("escalation_level")
    acknowledged_by = body.get("acknowledged_by")
    
    logger.info(f"Escalation L{escalation_level} acknowledged for {service} by {acknowledged_by}")
    
    return {
        "status": "acknowledged",
        "service": service,
        "escalation_level": escalation_level,
        "acknowledged_by": acknowledged_by,
        "timestamp": datetime.now().isoformat()
    }

@router.post("/escalation-triggered")
async def escalation_triggered(request: Request):
    """Log escalation trigger events"""
    body = await request.json()
    
    logger.info(f"Escalation triggered: {body}")
    
    return {
        "status": "logged",
        "timestamp": datetime.now().isoformat()
    }

@router.post("/ticket-created")
async def ticket_created(request: Request):
    """Handle ticket creation notification from Power Automate"""
    body = await request.json()
    
    logger.info(f"Ticket created: {body.get('ticket_id')} for service {body.get('service')}")
    
    return {
        "status": "logged",
        "timestamp": datetime.now().isoformat()
    }