import os
import json
import asyncio
from typing import List, Dict, Any, Optional, AsyncGenerator
from datetime import datetime
import logging

import tiktoken
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage, AssistantMessage
from azure.identity import DefaultAzureCredential, AzureCliCredential
from azure.core.credentials import AzureKeyCredential
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class ConversationMessage(BaseModel):
    role: str
    content: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None

class LLMResponse(BaseModel):
    content: str
    provider: str
    model: str
    tokens_used: int
    processing_time_ms: int
    confidence: Optional[float] = None

class IncidentContext(BaseModel):
    recent_changes: Optional[Dict[str, Any]] = None
    active_alerts: Optional[List[Dict[str, Any]]] = None
    error_patterns: Optional[List[Dict[str, Any]]] = None
    service_health: Optional[Dict[str, Any]] = None
    correlation_analysis: Optional[str] = None

class LLMService:
    def __init__(self):
        # Azure OpenAI Configuration
        self.azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.azure_api_key = os.getenv("AZURE_OPENAI_KEY")
        self.azure_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4")
        self.azure_api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01")
        
        # Initialize Azure OpenAI client
        self.azure_client = None
        if self.azure_endpoint:
            try:
                if self.azure_api_key:
                    # Use API key authentication
                    credential = AzureKeyCredential(self.azure_api_key)
                else:
                    # Use Azure CLI or managed identity authentication
                    try:
                        credential = AzureCliCredential()
                    except:
                        credential = DefaultAzureCredential()
                
                self.azure_client = ChatCompletionsClient(
                    endpoint=self.azure_endpoint,
                    credential=credential
                )
                logger.info("Azure OpenAI client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Azure OpenAI client: {e}")
                self.azure_client = None
        else:
            logger.error("AZURE_OPENAI_ENDPOINT not configured")
        
        # Token counting
        try:
            self.encoding = tiktoken.encoding_for_model("gpt-4")
        except:
            self.encoding = tiktoken.get_encoding("cl100k_base")
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        try:
            return len(self.encoding.encode(text))
        except:
            return len(text.split()) * 1.3  # Rough estimation
    
    def create_incident_prompt(self, user_query: str, context: IncidentContext) -> str:
        """Create a specialized prompt for incident response"""
        
        system_prompt = """You are an expert incident response analyst with deep knowledge of system monitoring, troubleshooting, and root cause analysis. You help teams quickly identify and resolve production issues.

Your capabilities:
- Analyze monitoring data and correlate events
- Identify patterns in errors and performance metrics  
- Suggest investigation steps and remediation actions
- Prioritize incidents based on impact and urgency
- Explain complex technical issues in clear terms

Guidelines:
- Be concise but thorough in your analysis
- Prioritize actionable insights over general advice
- Include specific commands, queries, or steps when helpful
- Highlight critical correlations and patterns
- Suggest both immediate fixes and long-term improvements
- Use emojis sparingly for visual clarity (🚨 for critical, ⚠️ for warnings, ✅ for recommendations)

Context provided:
- Recent system changes and deployments
- Active alerts and monitoring data
- Error patterns and frequency
- Service health metrics
- Automated correlation analysis"""

        context_section = ""
        if context.recent_changes:
            context_section += f"\n## Recent Changes\n{json.dumps(context.recent_changes, indent=2)}\n"
        
        if context.active_alerts:
            context_section += f"\n## Active Alerts\n{json.dumps(context.active_alerts, indent=2)}\n"
        
        if context.error_patterns:
            context_section += f"\n## Error Patterns\n{json.dumps(context.error_patterns, indent=2)}\n"
        
        if context.service_health:
            context_section += f"\n## Service Health\n{json.dumps(context.service_health, indent=2)}\n"
        
        if context.correlation_analysis:
            context_section += f"\n## Correlation Analysis\n{context.correlation_analysis}\n"
        
        user_section = f"\n## User Query\n{user_query}\n"
        
        full_prompt = system_prompt + context_section + user_section + "\n## Analysis\nPlease analyze the situation and provide actionable insights:"
        
        return full_prompt
    
    
    async def generate_response_azure_openai(self, prompt: str, conversation_history: List[ConversationMessage]) -> LLMResponse:
        """Generate response using Azure OpenAI"""
        if not self.azure_client:
            raise ValueError("Azure OpenAI not configured")
        
        start_time = datetime.now()
        
        # Build messages for Azure OpenAI
        messages = [SystemMessage(content=prompt)]
        
        # Add conversation history (last 10 messages to stay within limits)
        for msg in conversation_history[-10:]:
            if msg.role == "user":
                messages.append(UserMessage(content=msg.content))
            else:
                messages.append(AssistantMessage(content=msg.content))
        
        try:
            response = await asyncio.to_thread(
                self.azure_client.complete,
                messages=messages,
                model=self.azure_deployment,
                temperature=0.3,
                max_tokens=2000,
                top_p=0.9,
                frequency_penalty=0.1,
                presence_penalty=0.1
            )
            
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # Extract response content
            content = response.choices[0].message.content
            tokens_used = getattr(response.usage, 'total_tokens', 0) if hasattr(response, 'usage') else 0
            
            # Estimate tokens if not provided
            if tokens_used == 0:
                total_text = prompt + "".join([msg.content for msg in conversation_history[-10:]]) + content
                tokens_used = self.count_tokens(total_text)
            
            return LLMResponse(
                content=content,
                provider="azure_openai",
                model=self.azure_deployment,
                tokens_used=tokens_used,
                processing_time_ms=int(processing_time)
            )
            
        except Exception as e:
            logger.error(f"Azure OpenAI API error: {e}")
            raise
    
    async def generate_response(self, user_query: str, context: IncidentContext, 
                              conversation_history: List[ConversationMessage], 
                              provider: Optional[str] = None) -> Optional[LLMResponse]:
        """Generate intelligent response based on incident context using Azure OpenAI (optional)"""
        
        # Use Azure OpenAI if available
        if self.azure_client:
            try:
                # Create specialized prompt
                prompt = self.create_incident_prompt(user_query, context)
                return await self.generate_response_azure_openai(prompt, conversation_history)
            except Exception as e:
                logger.error(f"Azure OpenAI failed, falling back to traditional response: {e}")
                return None
        else:
            logger.info("Azure OpenAI not configured, will use traditional responses only")
            return None
    
    async def generate_streaming_response(self, user_query: str, context: IncidentContext,
                                        conversation_history: List[ConversationMessage],
                                        provider: Optional[str] = None) -> AsyncGenerator[str, None]:
        """Generate streaming response for real-time experience using Azure OpenAI (optional)"""
        
        if not self.azure_client:
            yield "Azure OpenAI not configured. Using traditional response mode only."
            return
        
        prompt = self.create_incident_prompt(user_query, context)
        
        # Build messages for Azure OpenAI
        messages = [SystemMessage(content=prompt)]
        for msg in conversation_history[-10:]:
            if msg.role == "user":
                messages.append(UserMessage(content=msg.content))
            else:
                messages.append(AssistantMessage(content=msg.content))
        
        try:
            # Note: Azure AI Inference may not support streaming yet
            # Fall back to regular response and yield it in chunks
            response = await self.generate_response_azure_openai(prompt, conversation_history)
            
            # Simulate streaming by yielding response in chunks
            content = response.content
            chunk_size = 50  # Characters per chunk
            for i in range(0, len(content), chunk_size):
                chunk = content[i:i + chunk_size]
                yield chunk
                await asyncio.sleep(0.01)  # Small delay for streaming effect
                
        except Exception as e:
            logger.error(f"Azure OpenAI streaming error: {e}")
            yield f"Error generating response: {str(e)}"
    
    def get_available_providers(self) -> List[str]:
        """Get list of available LLM providers"""
        providers = []
        if self.azure_client:
            providers.append("azure_openai")
        return providers
    
    async def analyze_incident_summary(self, incident_data: Dict[str, Any]) -> str:
        """Generate executive summary of incident"""
        
        context = IncidentContext(
            recent_changes=incident_data.get("changes"),
            active_alerts=incident_data.get("alerts"),
            error_patterns=incident_data.get("errors"),
            service_health=incident_data.get("health"),
            correlation_analysis=incident_data.get("correlation")
        )
        
        summary_query = "Provide a concise executive summary of this incident including impact, root cause hypothesis, and recommended next steps."
        
        response = await self.generate_response(summary_query, context, [])
        if response:
            return response.content
        else:
            # Fallback to traditional summary when Azure OpenAI is not available
            return "Azure OpenAI not configured. Please review the incident data manually for analysis."

# Global LLM service instance
llm_service = LLMService()