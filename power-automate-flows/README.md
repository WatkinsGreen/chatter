# Power Automate Flows for Incident Response

This directory contains Power Automate flow templates and configuration for automating incident response workflows.

## Flow Templates

### 1. Critical Alert Teams Notification
**File**: `critical-alert-teams.json`
**Trigger**: HTTP webhook from chatbot
**Actions**:
- Parse incident data
- Format adaptive card for Teams
- Post to Teams channel
- Log notification in SharePoint list

### 2. Ticket Creation Automation
**File**: `ticket-automation.json`
**Trigger**: HTTP webhook for high-severity incidents
**Actions**:
- Create ServiceNow/Jira ticket
- Assign based on service mapping
- Set priority and category
- Send confirmation back to chatbot

### 3. Escalation Workflow
**File**: `escalation-workflow.json`
**Trigger**: Timer (5 minutes after alert)
**Actions**:
- Check if incident acknowledged
- If not acknowledged, escalate to manager
- Send escalated Teams notification
- Update ticket priority

### 4. Alert Correlation Trigger
**File**: `alert-correlation.json`
**Trigger**: HTTP webhook from monitoring systems
**Actions**:
- Collect recent alerts
- Analyze patterns
- Trigger chatbot analysis
- Send summary to Teams

## Setup Instructions

### Prerequisites
- Microsoft 365 Business/Enterprise license
- Power Automate Premium (for some connectors)
- Teams admin permissions
- ServiceNow/Jira connector (if using ticketing)

### 1. Import Flow Templates

1. Go to [Power Automate](https://flow.microsoft.com)
2. Click "My flows" → "Import" → "Import Package"
3. Upload the JSON files from this directory
4. Configure connections as prompted

### 2. Configure Webhook URLs

After importing flows, get the webhook URLs:

1. Open each flow in Power Automate
2. Click the HTTP trigger step
3. Copy the "HTTP POST URL"
4. Update the chatbot configuration:

```bash
curl -X POST http://localhost:8000/power-automate/webhooks/configure \
  -H "Content-Type: application/json" \
  -d '{
    "teams_critical": "YOUR_CRITICAL_TEAMS_WEBHOOK_URL",
    "teams_warning": "YOUR_WARNING_TEAMS_WEBHOOK_URL", 
    "serviceNow_ticket": "YOUR_SERVICENOW_WEBHOOK_URL",
    "jira_ticket": "YOUR_JIRA_WEBHOOK_URL",
    "escalation": "YOUR_ESCALATION_WEBHOOK_URL"
  }'
```

### 3. Test Integration

Test each webhook:

```bash
# Test Teams notification
curl -X POST http://localhost:8000/power-automate/trigger/teams-notification \
  -H "Content-Type: application/json" \
  -d '{
    "webhook_url": "YOUR_TEAMS_WEBHOOK",
    "title": "Test Alert",
    "message": "Testing Power Automate integration",
    "severity": "high",
    "service": "test-service"
  }'

# Test ticket creation
curl -X POST http://localhost:8000/power-automate/trigger/create-ticket \
  -H "Content-Type: application/json" \
  -d '{
    "service_now_url": "YOUR_SERVICENOW_URL",
    "title": "Test Incident",
    "description": "Testing ticket automation",
    "severity": "high",
    "service": "test-service"
  }'
```

## Flow Details

### Critical Alert Teams Notification

**Webhook URL**: `/power-automate/webhook/incident`

**Input Schema**:
```json
{
  "severity": "high|medium|low",
  "service": "service-name",
  "alert_name": "Alert Title", 
  "timestamp": "2025-01-08T14:30:00Z",
  "description": "Alert description",
  "metric_value": 1250.5,
  "baseline_value": 450.0,
  "correlation_data": { ... }
}
```

**Teams Adaptive Card Features**:
- Color-coded severity (red for high, yellow for medium)
- Service details and timeline
- Action buttons (View Dashboard, Acknowledge)
- Direct links to chatbot with service filter

### Ticket Automation

**Trigger Conditions**:
- Severity = "high"
- Service in critical services list
- Not acknowledged within 2 minutes

**ServiceNow Integration**:
- Maps service to assignment group
- Sets category based on alert type
- Links back to chatbot dashboard
- Auto-assigns based on on-call schedule

### Escalation Workflow

**Escalation Levels**:
1. **Level 1** (5 min): Team lead notification
2. **Level 2** (15 min): Department manager
3. **Level 3** (30 min): Director/VP level

**Actions**:
- Progressive Teams notifications
- Email alerts with increasing urgency
- Update ticket priority automatically
- Conference bridge creation for Level 3

## Monitoring and Analytics

### Power BI Dashboard
- Flow execution metrics
- Response time tracking  
- Escalation patterns
- Team acknowledgment rates

### Logs and Alerts
- Flow failure notifications
- Performance monitoring
- Usage analytics
- Cost tracking

## Customization

### Adding New Services
1. Update service mapping in flow variables
2. Add assignment rules
3. Configure notification channels
4. Test end-to-end workflow

### Custom Connectors
- Create custom connectors for proprietary systems
- Use HTTP actions for REST APIs
- Implement authentication (OAuth, API keys)
- Add error handling and retries

## Security Considerations

- Use managed identity for authentication
- Implement webhook signature verification
- Encrypt sensitive data in flows
- Regular access review and auditing
- Use Data Loss Prevention (DLP) policies