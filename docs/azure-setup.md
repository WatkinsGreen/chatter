# Azure OpenAI Setup Guide

This guide walks through setting up Azure OpenAI for the Incident Response Chatbot.

## Why Azure OpenAI?

Azure OpenAI provides enterprise-grade AI with additional benefits:

- **🔒 Enhanced Security**: Data stays within your Azure tenant
- **🌍 Regional Deployment**: Choose your data residency
- **🏢 Enterprise Compliance**: SOC 2, ISO 27001, HIPAA compliance
- **🔧 Integration**: Native Azure services integration
- **💰 Cost Management**: Azure billing and cost controls
- **🚀 Performance**: Optimized for enterprise workloads

## Prerequisites

- Azure subscription with Azure OpenAI access
- Azure CLI installed (optional, for authentication)
- Resource group for deploying Azure OpenAI

## Step 1: Create Azure OpenAI Resource

### Via Azure Portal

1. **Navigate to Azure Portal** → Create a resource
2. **Search for "OpenAI"** → Select "Azure OpenAI"
3. **Configure Resource**:
   - **Subscription**: Your Azure subscription
   - **Resource Group**: Create new or use existing
   - **Region**: Choose your preferred region
   - **Name**: `your-company-openai` (must be globally unique)
   - **Pricing Tier**: Standard S0

4. **Review + Create** → Wait for deployment

### Via Azure CLI

```bash
# Login to Azure
az login

# Create resource group (if needed)
az group create --name rg-incident-response --location eastus

# Create Azure OpenAI resource
az cognitiveservices account create \
  --name your-company-openai \
  --resource-group rg-incident-response \
  --location eastus \
  --kind OpenAI \
  --sku S0 \
  --yes
```

## Step 2: Deploy GPT-4 Model

### Via Azure Portal

1. **Navigate to your Azure OpenAI resource**
2. **Go to "Model deployments"** → "Manage Deployments"
3. **Create New Deployment**:
   - **Model**: `gpt-4` or `gpt-4-turbo`
   - **Deployment Name**: `gpt-4-incident-response`
   - **Model Version**: Latest
   - **Scale Settings**: Standard (adjust based on needs)

### Via Azure CLI

```bash
# Deploy GPT-4 model
az cognitiveservices account deployment create \
  --resource-group rg-incident-response \
  --account-name your-company-openai \
  --deployment-name gpt-4-incident-response \
  --model-name gpt-4 \
  --model-version "0613" \
  --model-format OpenAI \
  --scale-settings-scale-type Standard \
  --scale-settings-capacity 10
```

## Step 3: Get Configuration Details

### Via Azure Portal

1. **Navigate to your Azure OpenAI resource**
2. **Go to "Keys and Endpoint"**
3. **Copy the following**:
   - **Endpoint**: `https://your-company-openai.openai.azure.com/`
   - **Key 1**: Your API key
   - **Region**: Your deployment region

### Via Azure CLI

```bash
# Get endpoint
az cognitiveservices account show \
  --resource-group rg-incident-response \
  --name your-company-openai \
  --query "properties.endpoint" \
  --output tsv

# Get API key
az cognitiveservices account keys list \
  --resource-group rg-incident-response \
  --name your-company-openai \
  --query "key1" \
  --output tsv
```

## Step 4: Configure Chatbot

### Environment Variables

Create/update your `.env` file:

```bash
# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=https://your-company-openai.openai.azure.com/
AZURE_OPENAI_KEY=your-api-key-here
AZURE_OPENAI_DEPLOYMENT=gpt-4-incident-response
AZURE_OPENAI_API_VERSION=2024-02-01
LLM_PROVIDER=azure_openai
```

### Docker Compose Environment

Update your `docker-compose.yml`:

```yaml
services:
  backend:
    environment:
      - AZURE_OPENAI_ENDPOINT=${AZURE_OPENAI_ENDPOINT}
      - AZURE_OPENAI_KEY=${AZURE_OPENAI_KEY}
      - AZURE_OPENAI_DEPLOYMENT=${AZURE_OPENAI_DEPLOYMENT}
      - AZURE_OPENAI_API_VERSION=${AZURE_OPENAI_API_VERSION}
      - LLM_PROVIDER=azure_openai
```

## Step 5: Authentication Options

### Option 1: API Key (Recommended for Development)

```bash
export AZURE_OPENAI_KEY="your-api-key"
```

### Option 2: Azure CLI Authentication

```bash
# Login to Azure CLI
az login

# No additional environment variables needed
# Application will use Azure CLI credentials automatically
```

### Option 3: Managed Identity (Production)

For applications running on Azure (VMs, App Service, AKS):

```bash
# Enable system-assigned managed identity on your Azure resource
az vm identity assign --resource-group rg-incident-response --name your-vm

# Grant access to Azure OpenAI resource
az role assignment create \
  --assignee $(az vm identity show --resource-group rg-incident-response --name your-vm --query principalId --output tsv) \
  --role "Cognitive Services OpenAI User" \
  --scope /subscriptions/your-subscription-id/resourceGroups/rg-incident-response/providers/Microsoft.CognitiveServices/accounts/your-company-openai

# No API key needed - application will use managed identity
```

## Step 6: Test Configuration

### Test Connection

```bash
# Test with curl
curl -X POST \
  "$AZURE_OPENAI_ENDPOINT/openai/deployments/$AZURE_OPENAI_DEPLOYMENT/chat/completions?api-version=$AZURE_OPENAI_API_VERSION" \
  -H "api-key: $AZURE_OPENAI_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {
        "role": "user",
        "content": "Hello, Azure OpenAI!"
      }
    ],
    "max_tokens": 50
  }'
```

### Test Chatbot

1. **Start the application**:
   ```bash
   docker-compose up --build
   ```

2. **Access the chatbot**: http://localhost:3000

3. **Test AI functionality**:
   - "Analyze what changed in the last 2 hours"
   - "Why are we seeing these errors?"
   - "What should I investigate first?"

## Troubleshooting

### Common Issues

#### 1. Access Denied Error
```
Error: Access denied due to Virtual Network/Firewall rules
```
**Solution**: Configure network access in Azure Portal → Your OpenAI Resource → Networking

#### 2. Model Not Found
```
Error: The API deployment for this resource does not exist
```
**Solution**: Verify deployment name matches `AZURE_OPENAI_DEPLOYMENT` exactly

#### 3. Rate Limiting
```
Error: Rate limit exceeded
```
**Solution**: Increase quota in Azure Portal → Your OpenAI Resource → Quotas

#### 4. Authentication Failed
```
Error: Invalid authentication credentials
```
**Solutions**:
- Verify API key is correct
- Check endpoint URL format
- Ensure managed identity has proper role assignments

### Debug Mode

Enable debug logging:

```bash
export LOG_LEVEL=DEBUG
```

Check application logs for detailed Azure OpenAI connection information.

## Cost Management

### Monitor Usage

1. **Azure Portal** → Your OpenAI Resource → Metrics
2. **Monitor**:
   - Total Tokens
   - Generated Tokens
   - Processed Prompt Tokens

### Set Up Alerts

```bash
# Create cost alert
az monitor metrics alert create \
  --name "OpenAI High Usage" \
  --resource-group rg-incident-response \
  --scopes /subscriptions/your-subscription-id/resourceGroups/rg-incident-response/providers/Microsoft.CognitiveServices/accounts/your-company-openai \
  --condition "count \"Total Tokens\" > 1000000" \
  --description "Alert when token usage exceeds 1M"
```

### Cost Optimization

- **Smart Query Routing**: Chatbot automatically uses traditional responses for simple queries
- **Conversation Limits**: Automatic conversation history truncation
- **Model Selection**: Use appropriate model size for your needs
- **Regional Deployment**: Choose cost-effective regions

## Security Best Practices

### Network Security

1. **Enable Private Endpoints**:
   - Azure Portal → Your OpenAI Resource → Networking → Private Endpoints

2. **Configure Firewall Rules**:
   - Allow only your application's IP addresses
   - Use Virtual Network integration for Azure-hosted applications

### Key Management

1. **Rotate Keys Regularly**:
   ```bash
   az cognitiveservices account keys regenerate \
     --resource-group rg-incident-response \
     --name your-company-openai \
     --key-name key1
   ```

2. **Use Azure Key Vault**:
   ```bash
   # Store API key in Key Vault
   az keyvault secret set \
     --vault-name your-keyvault \
     --name azure-openai-key \
     --value "your-api-key"
   ```

### Monitoring & Auditing

1. **Enable Diagnostic Logs**:
   ```bash
   az monitor diagnostic-settings create \
     --resource /subscriptions/your-subscription-id/resourceGroups/rg-incident-response/providers/Microsoft.CognitiveServices/accounts/your-company-openai \
     --name "OpenAI-Diagnostics" \
     --logs '[{"category":"Audit","enabled":true}]' \
     --storage-account your-storage-account
   ```

2. **Review Access Logs**: Monitor who's accessing your Azure OpenAI resource

## Production Checklist

- [ ] Azure OpenAI resource deployed in production region
- [ ] GPT-4 model deployed with appropriate capacity
- [ ] Network security configured (private endpoints, firewall)
- [ ] Managed identity configured for authentication
- [ ] Cost alerts and monitoring set up
- [ ] Diagnostic logging enabled
- [ ] API key rotation schedule established
- [ ] Backup authentication method configured
- [ ] Load testing completed
- [ ] Disaster recovery plan documented

## Support

- **Azure OpenAI Documentation**: https://docs.microsoft.com/azure/cognitive-services/openai/
- **Azure Support**: Create support ticket in Azure Portal
- **Community**: Azure OpenAI discussions on Microsoft Tech Community