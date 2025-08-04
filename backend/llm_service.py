import os
import json
import asyncio
from typing import List, Dict, Any, Optional, AsyncGenerator
from datetime import datetime
import logging
from enum import Enum

import openai
import anthropic
import tiktoken
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class LLMProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"

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
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        self.default_provider = os.getenv("LLM_PROVIDER", "openai").lower()
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
        self.anthropic_model = os.getenv("ANTHROPIC_MODEL", "claude-3-sonnet-20240229")
        
        # Initialize clients
        self.openai_client = None
        self.anthropic_client = None
        
        if self.openai_api_key:
            self.openai_client = openai.AsyncOpenAI(api_key=self.openai_api_key)
            
        if self.anthropic_api_key:
            self.anthropic_client = anthropic.AsyncAnthropic(api_key=self.anthropic_api_key)
        
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
    
    async def generate_response_openai(self, prompt: str, conversation_history: List[ConversationMessage]) -> LLMResponse:
        """Generate response using OpenAI"""
        if not self.openai_client:
            raise ValueError("OpenAI API key not configured")
        
        start_time = datetime.now()
        
        # Build messages
        messages = [{"role": "system", "content": prompt}]
        
        # Add conversation history (last 10 messages to stay within limits)
        for msg in conversation_history[-10:]:
            messages.append({"role": msg.role, "content": msg.content})
        
        try:
            response = await self.openai_client.chat.completions.create(
                model=self.openai_model,
                messages=messages,
                temperature=0.3,  # Lower temperature for more focused responses
                max_tokens=2000,
                top_p=0.9,
                frequency_penalty=0.1,
                presence_penalty=0.1
            )
            
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return LLMResponse(
                content=response.choices[0].message.content,
                provider="openai",
                model=self.openai_model,
                tokens_used=response.usage.total_tokens,
                processing_time_ms=int(processing_time)
            )
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise
    
    async def generate_response_anthropic(self, prompt: str, conversation_history: List[ConversationMessage]) -> LLMResponse:
        """Generate response using Anthropic Claude"""
        if not self.anthropic_client:
            raise ValueError("Anthropic API key not configured")
        
        start_time = datetime.now()
        
        # Build conversation for Claude
        messages = []
        for msg in conversation_history[-10:]:  # Last 10 messages
            messages.append({
                "role": "user" if msg.role == "user" else "assistant",
                "content": msg.content
            })
        
        try:
            response = await self.anthropic_client.messages.create(
                model=self.anthropic_model,
                max_tokens=2000,
                temperature=0.3,
                system=prompt,
                messages=messages
            )
            
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # Estimate tokens (Anthropic doesn't always provide exact counts)
            total_text = prompt + "".join([msg.content for msg in messages]) + response.content[0].text
            estimated_tokens = self.count_tokens(total_text)
            
            return LLMResponse(
                content=response.content[0].text,
                provider="anthropic", 
                model=self.anthropic_model,
                tokens_used=estimated_tokens,
                processing_time_ms=int(processing_time)
            )
            
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise
    
    async def generate_response(self, user_query: str, context: IncidentContext, 
                              conversation_history: List[ConversationMessage], 
                              provider: Optional[str] = None) -> LLMResponse:
        """Generate intelligent response based on incident context"""
        
        # Choose provider
        selected_provider = provider or self.default_provider
        
        # Create specialized prompt
        prompt = self.create_incident_prompt(user_query, context)
        
        # Generate response based on provider
        if selected_provider == "openai" and self.openai_client:
            return await self.generate_response_openai(prompt, conversation_history)
        elif selected_provider == "anthropic" and self.anthropic_client:
            return await self.generate_response_anthropic(prompt, conversation_history)
        else:
            # Fallback logic
            if self.openai_client:
                return await self.generate_response_openai(prompt, conversation_history)
            elif self.anthropic_client:
                return await self.generate_response_anthropic(prompt, conversation_history)
            else:
                raise ValueError("No LLM provider configured. Please set OPENAI_API_KEY or ANTHROPIC_API_KEY")
    
    async def generate_streaming_response(self, user_query: str, context: IncidentContext,
                                        conversation_history: List[ConversationMessage],
                                        provider: Optional[str] = None) -> AsyncGenerator[str, None]:
        """Generate streaming response for real-time experience"""
        
        selected_provider = provider or self.default_provider
        prompt = self.create_incident_prompt(user_query, context)
        
        if selected_provider == "openai" and self.openai_client:
            messages = [{"role": "system", "content": prompt}]
            for msg in conversation_history[-10:]:
                messages.append({"role": msg.role, "content": msg.content})
            
            try:
                stream = await self.openai_client.chat.completions.create(
                    model=self.openai_model,
                    messages=messages,
                    temperature=0.3,
                    max_tokens=2000,
                    stream=True
                )
                
                async for chunk in stream:
                    if chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
                        
            except Exception as e:
                logger.error(f"OpenAI streaming error: {e}")
                yield f"Error generating response: {str(e)}"
        
        elif selected_provider == "anthropic" and self.anthropic_client:
            # Anthropic streaming implementation
            messages = []
            for msg in conversation_history[-10:]:
                messages.append({
                    "role": "user" if msg.role == "user" else "assistant",
                    "content": msg.content
                })
            
            try:
                async with self.anthropic_client.messages.stream(
                    model=self.anthropic_model,
                    max_tokens=2000,
                    temperature=0.3,
                    system=prompt,
                    messages=messages
                ) as stream:
                    async for text in stream.text_stream:
                        yield text
                        
            except Exception as e:
                logger.error(f"Anthropic streaming error: {e}")
                yield f"Error generating response: {str(e)}"
        
        else:
            yield "No LLM provider available. Please configure OPENAI_API_KEY or ANTHROPIC_API_KEY."
    
    def get_available_providers(self) -> List[str]:
        """Get list of available LLM providers"""
        providers = []
        if self.openai_client:
            providers.append("openai")
        if self.anthropic_client:
            providers.append("anthropic")
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
        return response.content

# Global LLM service instance
llm_service = LLMService()